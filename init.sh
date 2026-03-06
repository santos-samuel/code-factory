#!/usr/bin/env bash
#
# init.sh -- Bootstrap code-factory: symlink configs and install OpenCode assets globally.
#
# This script:
#   1. Installs rtk (Rust Token Killer) via cargo if not already present.
#   2. Symlinks configuration files into the user's home directory.
#   3. Symlinks Claude Code hooks from hooks/ into ~/.claude/hooks/.
#   4. Runs sync-opencode.sh to generate OpenCode assets in the repo.
#   5. Symlinks .opencode/{skills,agents,commands} into ~/.config/opencode/.
#
# Behavior:
#   - If the destination is an existing symlink, it is removed and re-created.
#   - If the destination is a regular file, the script records an error.
#     To fix, back up or remove the existing file manually and re-run.
#   - If the destination does not exist, the symlink is created.
#   - Parent directories are created as needed (e.g., ~/.claude/, ~/.config/opencode/).
#   - The script exits non-zero if any file fails to link, with a summary at the end.
#
# This script is idempotent: running it multiple times produces the same result.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

errors=()

# Install or update rtk (Rust Token Killer) via cargo
echo "Checking rtk installation..."
if ! command -v cargo &>/dev/null; then
    errors+=("rtk: cargo not found, install Rust toolchain first (https://rustup.rs)")
    echo "FAIL  rtk requires cargo (install Rust via https://rustup.rs)"
else
    if command -v rtk &>/dev/null && rtk gain &>/dev/null; then
        echo "  OK  rtk already installed ($(rtk --version 2>/dev/null || echo 'unknown version'))"
        echo "  Checking for updates..."
    else
        echo "  Installing rtk via cargo..."
    fi
    if cargo install --git https://github.com/rtk-ai/rtk --config net.git-fetch-with-cli=true 2>&1; then
        echo "  OK  rtk up-to-date ($(rtk --version 2>/dev/null || echo 'unknown version'))"
    else
        errors+=("rtk: cargo install failed")
        echo "FAIL  rtk installation failed"
    fi
fi
echo ""

SRCS=(
    "$SCRIPT_DIR/settings.json"
    "$SCRIPT_DIR/opencode.jsonc"
)
DESTS=(
    "$HOME/.claude/settings.json"
    "$HOME/.config/opencode/opencode.jsonc"
)

# In workspace mode, force-remove settings.json so linking always succeeds
# (workspaces may have a pre-existing regular file instead of a symlink)
if [[ "${IN_WORKSPACE:-}" == "1" ]]; then
    rm -f "$HOME/.claude/settings.json"
fi

for i in "${!SRCS[@]}"; do
    src="${SRCS[$i]}"
    dest="${DESTS[$i]}"

    if [[ ! -f "$src" ]]; then
        errors+=("$src -> $dest: source file not found")
        echo "FAIL  $src (source file not found)"
        continue
    fi

    mkdir -p "$(dirname "$dest")"

    if [[ -L "$dest" ]]; then
        rm "$dest"
    elif [[ -e "$dest" ]]; then
        errors+=("$src -> $dest: destination already exists as a regular file")
        echo "FAIL  $dest already exists as a regular file, cannot link"
        continue
    fi

    if ! ln -s "$src" "$dest"; then
        errors+=("$src -> $dest: ln -s failed")
        echo "FAIL  could not link $dest -> $src"
        continue
    fi
    echo "LINK  $dest -> $src"
done

# Sync MCP servers: regenerate opencode.jsonc block + install into Claude Code
echo ""
echo "Syncing MCP servers..."
"$SCRIPT_DIR/sync-mcp.sh"

echo ""
echo "Installing MCP servers into Claude Code (user scope)..."

# Clean up stale ~/.mcp.json symlink from old approach
if [[ -L "$HOME/.mcp.json" ]]; then
    rm "$HOME/.mcp.json"
    echo "  Removed stale ~/.mcp.json symlink"
fi

mcp_server_names=$(python3 -c "
import json
data = json.load(open('$SCRIPT_DIR/mcp.json'))
for name in data.get('mcpServers', {}):
    print(name)
")

for name in $mcp_server_names; do
    config=$(python3 -c "
import json
data = json.load(open('$SCRIPT_DIR/mcp.json'))
print(json.dumps(data['mcpServers']['$name']))
")
    # Remove existing (ignore errors if not present)
    claude mcp remove "$name" 2>/dev/null || true
    # Add with user scope
    if claude mcp add-json -s user "$name" "$config" 2>&1; then
        echo "  OK  $name"
    else
        errors+=("mcp: failed to install $name")
        echo "  FAIL  $name"
    fi
done

# Symlink Claude Code hooks from hooks/ into ~/.claude/hooks/
echo ""
echo "Linking Claude Code hooks..."
HOOKS_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOKS_DIR"
for hook_src in "$SCRIPT_DIR/hooks"/*; do
    [[ -f "$hook_src" ]] || continue
    hook_name=$(basename "$hook_src")
    hook_dest="$HOOKS_DIR/$hook_name"
    if [[ -L "$hook_dest" ]]; then
        rm "$hook_dest"
    elif [[ -e "$hook_dest" ]]; then
        errors+=("$hook_src -> $hook_dest: destination already exists as a regular file")
        echo "  FAIL  $hook_dest already exists as a regular file, cannot link"
        continue
    fi
    if ! ln -s "$hook_src" "$hook_dest"; then
        errors+=("$hook_src -> $hook_dest: ln -s failed")
        echo "  FAIL  could not link $hook_dest -> $hook_src"
    else
        echo "  LINK  $hook_dest -> $hook_src"
    fi
done

# Generate OpenCode assets in the repo
echo ""
echo "Syncing skills, agents, and commands..."
"$SCRIPT_DIR/sync-opencode.sh"

# Propagate .opencode/{skills,agents,commands} to ~/.config/opencode/
echo ""
echo "Linking to ~/.config/opencode/..."

GLOBAL_DIR="$HOME/.config/opencode"
OPENCODE_DIR="$SCRIPT_DIR/.opencode"
MANIFEST="$GLOBAL_DIR/.code-factory-managed"

new_manifest=()

# Read old manifest for cleanup
old_manifest=()
if [[ -f "$MANIFEST" ]]; then
    while IFS= read -r line; do
        old_manifest+=("$line")
    done < "$MANIFEST"
fi

# Symlink each skill directory
if [[ -d "$OPENCODE_DIR/skills" ]]; then
    mkdir -p "$GLOBAL_DIR/skills"
    for skill_src in "$OPENCODE_DIR/skills"/*/; do
        [[ -d "$skill_src" ]] || continue
        skill_name=$(basename "$skill_src")
        skill_dest="$GLOBAL_DIR/skills/$skill_name"
        if ! ln -sfn "$skill_src" "$skill_dest"; then
            errors+=("$skill_src -> $skill_dest: ln -sfn failed")
            echo "  FAIL  skills/$skill_name/"
        else
            new_manifest+=("$skill_dest")
            echo "  LINK  skills/$skill_name/"
        fi
    done
fi

# Symlink agent, command, and plugin files
for subdir in agents commands plugins; do
    src_dir="$OPENCODE_DIR/$subdir"
    dest_dir="$GLOBAL_DIR/$subdir"
    [[ -d "$src_dir" ]] || continue
    mkdir -p "$dest_dir"

    while IFS= read -r src_file; do
        rel="${src_file#"$src_dir"/}"
        dest_file="$dest_dir/$rel"
        if ! ln -sf "$src_file" "$dest_file"; then
            errors+=("$src_file -> $dest_file: ln -sf failed")
            echo "  FAIL  $subdir/$rel"
        else
            new_manifest+=("$dest_file")
            echo "  LINK  $subdir/$rel"
        fi
    done < <(find "$src_dir" -type f \( -name "*.md" -o -name "*.ts" \) | sort)
done

# Manifest cleanup: remove stale global files
sorted_manifest=$(printf '%s\n' "${new_manifest[@]}" | sort)
cleaned=0
for old_file in "${old_manifest[@]+"${old_manifest[@]}"}"; do
    [[ -z "$old_file" ]] && continue
    if ! echo "$sorted_manifest" | grep -qxF "$old_file"; then
        if [[ -e "$old_file" || -L "$old_file" ]]; then
            rm -f "$old_file"
            echo "  CLEAN  $old_file"
            cleaned=$((cleaned + 1))
        fi
        parent=$(dirname "$old_file")
        rmdir "$parent" 2>/dev/null || true
    fi
done

# Write new manifest
echo "$sorted_manifest" > "$MANIFEST"

echo ""
echo "Linked ${#new_manifest[@]} files to ~/.config/opencode/. Cleaned $cleaned stale files."

# Install git hooks from .githooks/
for HOOK_SRC in "$SCRIPT_DIR/.githooks"/*; do
    [[ -f "$HOOK_SRC" ]] || continue
    HOOK_NAME=$(basename "$HOOK_SRC")
    HOOK_DEST="$SCRIPT_DIR/.git/hooks/$HOOK_NAME"
    if [[ -L "$HOOK_DEST" ]]; then
        rm "$HOOK_DEST"
    elif [[ -e "$HOOK_DEST" ]]; then
        errors+=("$HOOK_SRC -> $HOOK_DEST: destination already exists as a regular file")
        echo "FAIL  $HOOK_DEST already exists as a regular file, cannot link"
        continue
    fi
    if [[ ! -e "$HOOK_DEST" ]]; then
        if ! ln -s "$HOOK_SRC" "$HOOK_DEST"; then
            errors+=("$HOOK_SRC -> $HOOK_DEST: ln -s failed")
            echo "FAIL  could not link $HOOK_DEST -> $HOOK_SRC"
        else
            echo "LINK  $HOOK_DEST -> $HOOK_SRC"
        fi
    fi
done

# In workspace mode, patch settings.json with workspace-specific keys
if [[ "${IN_WORKSPACE:-}" == "1" ]]; then
    settings_file="$HOME/.claude/settings.json"
    if [[ -f "$settings_file" ]]; then
        python3 -c "
import json, os
path = os.path.expanduser('$settings_file')
# Resolve symlink so we write to the actual file
real = os.path.realpath(path)
with open(real) as f:
    data = json.load(f)
data['apiKeyHelper'] = 'workspace_secret ANTHROPIC_APIKEY1'
data['forceLoginMethod'] = 'console'
with open(real, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
"
        echo "PATCH  $settings_file (workspace: apiKeyHelper, forceLoginMethod)"
    else
        errors+=("workspace: $settings_file not found after linking, cannot patch")
        echo "FAIL  workspace patch: $settings_file not found"
    fi
fi

# Final error summary
if [[ ${#errors[@]} -gt 0 ]]; then
    echo ""
    echo "========================================="
    echo "ERROR: ${#errors[@]} file(s) failed to link or sync:"
    for err in "${errors[@]}"; do
        echo "  - $err"
    done
    echo "========================================="
    exit 1
fi
