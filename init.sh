#!/usr/bin/env bash
#
# init.sh -- Bootstrap code-factory: symlink configs and install OpenCode assets globally.
#
# This script:
#   1. Symlinks configuration files into the user's home directory.
#   2. Runs sync-opencode.sh to generate OpenCode assets in the repo.
#   3. Symlinks .opencode/{skills,agents,commands} into ~/.config/opencode/.
#
# Behavior:
#   - If the destination is an existing symlink, it is removed and re-created.
#   - If the destination is a regular file, it is skipped with a warning.
#     To use the symlink, back up or remove the existing file manually.
#   - If the destination does not exist, the symlink is created.
#   - Parent directories are created as needed (e.g., ~/.claude/, ~/.config/opencode/).
#
# This script is idempotent: running it multiple times produces the same result.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SRCS=(
    "$SCRIPT_DIR/mcp.json"
    "$SCRIPT_DIR/settings.json"
    "$SCRIPT_DIR/opencode.jsonc"
)
DESTS=(
    "$HOME/.mcp.json"
    "$HOME/.claude/settings.json"
    "$HOME/.config/opencode/opencode.jsonc"
)

for i in "${!SRCS[@]}"; do
    src="${SRCS[$i]}"
    dest="${DESTS[$i]}"

    if [[ ! -f "$src" ]]; then
        echo "SKIP  $src (source file not found)"
        continue
    fi

    mkdir -p "$(dirname "$dest")"

    if [[ -L "$dest" ]]; then
        rm "$dest"
    elif [[ -e "$dest" ]]; then
        echo "WARN  $dest already exists as a regular file, skipping"
        continue
    fi

    ln -s "$src" "$dest"
    echo "LINK  $dest -> $src"
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
        ln -sfn "$skill_src" "$skill_dest"
        new_manifest+=("$skill_dest")
        echo "  LINK  skills/$skill_name/"
    done
fi

# Symlink agent and command files
for subdir in agents commands; do
    src_dir="$OPENCODE_DIR/$subdir"
    dest_dir="$GLOBAL_DIR/$subdir"
    [[ -d "$src_dir" ]] || continue
    mkdir -p "$dest_dir"

    while IFS= read -r src_file; do
        rel="${src_file#"$src_dir"/}"
        dest_file="$dest_dir/$rel"
        ln -sf "$src_file" "$dest_file"
        new_manifest+=("$dest_file")
        echo "  LINK  $subdir/$rel"
    done < <(find "$src_dir" -type f -name "*.md" | sort)
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

# Install pre-commit hook
HOOK_SRC="$SCRIPT_DIR/.githooks/pre-commit"
HOOK_DEST="$SCRIPT_DIR/.git/hooks/pre-commit"
if [[ -f "$HOOK_SRC" ]]; then
    if [[ -L "$HOOK_DEST" ]]; then
        rm "$HOOK_DEST"
    elif [[ -e "$HOOK_DEST" ]]; then
        echo "WARN  $HOOK_DEST already exists as a regular file, skipping"
    fi
    if [[ ! -e "$HOOK_DEST" ]]; then
        ln -s "$HOOK_SRC" "$HOOK_DEST"
        echo "LINK  $HOOK_DEST -> $HOOK_SRC"
    fi
fi
