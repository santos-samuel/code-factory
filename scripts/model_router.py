#!/usr/bin/env python3
"""Resolve deterministic cross-surface model routes and bounded fan-out."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "model-routing.json"
SURFACES = ("claude", "codex", "pi")


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    with path.open() as stream:
        return json.load(stream)


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise ValueError("unsupported model-routing.json schema")

    tiers = policy.get("tiers", {})
    if not tiers:
        raise ValueError("model-routing.json has no routing tiers")
    for tier, profiles in tiers.items():
        for surface in SURFACES:
            profile = profiles.get(surface)
            if not isinstance(profile, dict):
                raise ValueError(f"missing {surface} profile for tier {tier}")
            if surface == "pi":
                if not profile.get("provider") or not profile.get("model") or not profile.get("thinking"):
                    raise ValueError(f"incomplete Pi profile for tier {tier}")
            elif not profile.get("model") or not profile.get("effort"):
                raise ValueError(f"incomplete {surface} profile for tier {tier}")

    for surface in SURFACES:
        if policy.get("default_tier", {}).get(surface) not in tiers:
            raise ValueError(f"invalid default tier for {surface}")

    constraints = policy.get("pi_constraints", {})
    allowed_providers = constraints.get("allowed_providers", [])
    allowed_prefixes = constraints.get("allowed_model_prefixes", [])
    allowed_models = constraints.get("allowed_models", [])
    for tier, profiles in tiers.items():
        profile = profiles["pi"]
        if profile["provider"] not in allowed_providers:
            raise ValueError(f"Pi tier {tier} uses a forbidden provider")
        if not any(profile["model"].startswith(prefix) for prefix in allowed_prefixes):
            raise ValueError(f"Pi tier {tier} uses a forbidden model")
        if profile["model"] not in allowed_models:
            raise ValueError(f"Pi tier {tier} uses a model outside the configured allowlist")

    if not set(policy.get("allowed_efforts", [])) >= {"high", "xhigh", "max"}:
        raise ValueError("policy must define the supported agent effort levels")
    if not set(policy.get("allowed_pi_thinking", [])) >= {"low", "medium", "high", "xhigh", "max"}:
        raise ValueError("policy must define the supported Pi thinking levels")

    parallelism = policy.get("parallelism", {})
    if parallelism.get("max_leaf_workers") != 3:
        raise ValueError("parallelism must cap automatic fan-out at three leaf workers")
    if parallelism.get("coordinator_reserved_slots") != 1:
        raise ValueError("parallelism must reserve one coordinator slot")
    if parallelism.get("unknown_capacity_probe") != 1:
        raise ValueError("unknown capacity must allow exactly one probe worker")


def profile_for_tier(surface: str, tier: str, policy: dict[str, Any] | None = None) -> dict[str, str]:
    policy = policy or load_policy()
    validate_policy(policy)
    if surface not in SURFACES:
        raise ValueError(f"unsupported surface: {surface}")
    try:
        profile = policy["tiers"][tier][surface]
    except KeyError as error:
        raise ValueError(f"unsupported tier for {surface}: {tier}") from error
    return copy.deepcopy(profile)


def _parse_override(
    surface: str,
    override: str,
    base: dict[str, str],
    policy: dict[str, Any],
) -> dict[str, str]:
    route, separator, level = override.rpartition(":")
    if not separator:
        route, level = override, ""
    route = route.strip()
    level = level.strip()
    if not route:
        raise ValueError("override must include a model")

    if surface == "pi":
        if "/" in route:
            provider, model = route.split("/", 1)
        else:
            provider, model = base["provider"], route
        if level and level not in policy["allowed_pi_thinking"]:
            raise ValueError(f"unsupported Pi thinking level: {level}")
        return {
            "provider": provider,
            "model": model,
            "thinking": level or base["thinking"],
        }

    if level and level not in policy["allowed_efforts"]:
        raise ValueError(f"unsupported effort level: {level}")
    return {
        "model": route,
        "effort": level or base["effort"],
    }


def _pi_route_allowed(profile: dict[str, str], policy: dict[str, Any]) -> bool:
    constraints = policy["pi_constraints"]
    return (
        profile["provider"] in constraints["allowed_providers"]
        and any(profile["model"].startswith(prefix) for prefix in constraints["allowed_model_prefixes"])
        and profile["model"] in constraints["allowed_models"]
    )


def _route_keys(surface: str, profile: dict[str, str]) -> set[str]:
    if surface == "pi":
        return {profile["model"], f"{profile['provider']}/{profile['model']}"}
    return {profile["model"]}


def resolve_route(
    surface: str,
    *,
    task: str | None = None,
    tier: str | None = None,
    override: str | None = None,
    available: Iterable[str] | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a route without making network calls or claiming actual usage."""

    policy = policy or load_policy()
    validate_policy(policy)
    if surface not in SURFACES:
        raise ValueError(f"unsupported surface: {surface}")
    if tier and task:
        raise ValueError("choose either task or tier")
    if task:
        try:
            tier = policy["task_tiers"][task]
        except KeyError as error:
            raise ValueError(f"unsupported task: {task}") from error
    tier = tier or policy["default_tier"][surface]

    recommended = profile_for_tier(surface, tier, policy)
    selected = copy.deepcopy(recommended)
    selection = "policy"
    reason = "task evidence selected the policy tier"

    if override:
        try:
            explicit = _parse_override(surface, override, recommended, policy)
        except ValueError as error:
            explicit = None
            reason = f"explicit route was invalid ({error}); retained the configured default"
        if explicit is None or (surface == "pi" and not _pi_route_allowed(explicit, policy)):
            fallback_tier = policy["default_tier"][surface]
            selected = profile_for_tier(surface, fallback_tier, policy)
            selection = "fail-open-default"
            if explicit is not None:
                reason = "explicit route is forbidden in Pi; retained the configured default"
        else:
            selected = explicit
            selection = "explicit-override"
            reason = "valid explicit user override"

    available_set = None if available is None else {item for item in available if item}
    verification = "unverified"
    observed = "unknown"
    if available_set is not None:
        if _route_keys(surface, selected) & available_set:
            verification = "available"
            observed = "available"
        else:
            fallback_tier = policy["default_tier"][surface]
            selected = profile_for_tier(surface, fallback_tier, policy)
            selection = "fail-open-default"
            reason = "requested route was unavailable; retained the configured default"

    return {
        "surface": surface,
        "task": task,
        "tier": tier,
        "recommended": recommended,
        "selected": selected,
        "selection": selection,
        "verification": verification,
        "observed": observed,
        "observed_usage": "unknown",
        "reason": reason,
    }


def plan_parallel(
    requested: int,
    *,
    capacity: int | None = None,
    active: int = 0,
    failed: bool = False,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Plan one bounded dispatch wave; it never starts work after a failure."""

    policy = policy or load_policy()
    validate_policy(policy)
    if requested < 0 or active < 0 or (capacity is not None and capacity < 0):
        raise ValueError("requested, active, and capacity must be non-negative")

    max_leaf = policy["parallelism"]["max_leaf_workers"]
    reserved = policy["parallelism"]["coordinator_reserved_slots"]
    if failed:
        return {
            "dispatch_now": 0,
            "drain_active": True,
            "skip_undispatched": requested,
            "capacity_status": "failed",
            "max_leaf_workers": max_leaf,
        }

    if capacity is None:
        remaining_leaf_slots = max(0, max_leaf - active)
        dispatch_now = min(
            requested,
            policy["parallelism"]["unknown_capacity_probe"],
            remaining_leaf_slots,
        )
        capacity_status = "unknown-probe"
    else:
        available_leaf_slots = max(0, min(max_leaf - active, capacity - reserved - active))
        dispatch_now = min(requested, max_leaf, available_leaf_slots)
        capacity_status = "measured"

    return {
        "dispatch_now": dispatch_now,
        "drain_active": False,
        "skip_undispatched": 0,
        "capacity_status": capacity_status,
        "max_leaf_workers": max_leaf,
    }


def _available_arg(value: str | None) -> list[str] | None:
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    route = subparsers.add_parser("route", help="resolve a task route")
    route.add_argument("--surface", choices=SURFACES, required=True)
    route_group = route.add_mutually_exclusive_group()
    route_group.add_argument("--task")
    route_group.add_argument("--tier")
    route.add_argument("--override", help="explicit model route, optionally with :effort/thinking")
    route.add_argument("--available", help="comma-separated routes known to be available")

    profile = subparsers.add_parser("agent-profile", help="print an agent tier profile")
    profile.add_argument("--surface", choices=SURFACES, required=True)
    profile.add_argument("--tier", required=True)
    profile.add_argument("--format", choices=("json", "shell"), default="json")

    parallel = subparsers.add_parser("parallel-plan", help="plan one bounded dispatch wave")
    parallel.add_argument("--requested", type=int, required=True)
    parallel.add_argument("--capacity", type=int)
    parallel.add_argument("--active", type=int, default=0)
    parallel.add_argument("--failed", action="store_true")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.command == "route":
        result = resolve_route(
            args.surface,
            task=args.task,
            tier=args.tier,
            override=args.override,
            available=_available_arg(args.available),
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.command == "agent-profile":
        profile = profile_for_tier(args.surface, args.tier)
        if args.format == "shell":
            if args.surface == "pi":
                print(f"{profile['provider']}/{profile['model']} {profile['thinking']}")
            else:
                print(f"{profile['model']} {profile['effort']}")
        else:
            print(json.dumps(profile, sort_keys=True))
        return 0

    print(
        json.dumps(
            plan_parallel(
                args.requested,
                capacity=args.capacity,
                active=args.active,
                failed=args.failed,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
