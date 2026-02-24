"""
hook.py - Git pre-commit hook installer and runner for code-obituary.
"""

import os
import stat
import subprocess
from typing import List, Optional

HOOK_SCRIPT = """\
#!/usr/bin/env bash
# code-obituary pre-commit hook
# Automatically generates obituaries for deleted files.

set -e

# Check if code-obituary is installed
if ! command -v code-obituary &> /dev/null; then
    echo "[code-obituary] WARNING: code-obituary not found in PATH, skipping hook."
    exit 0
fi

# Get list of deleted files from the staged changes
DELETED_FILES=$(git diff --cached --diff-filter=D --name-only)

if [ -z "$DELETED_FILES" ]; then
    exit 0
fi

echo "[code-obituary] Mourning deleted files..."
REPO_ROOT=$(git rev-parse --show-toplevel)

while IFS= read -r filepath; do
    if [ -n "$filepath" ]; then
        echo "[code-obituary] Writing obituary for: $filepath"
        # Get the file content from HEAD (before deletion)
        code-obituary mourn "$filepath" --from-git || true
    fi
done <<< "$DELETED_FILES"

echo "[code-obituary] Obituaries written to GRAVEYARD.md"
# Stage the updated GRAVEYARD.md if it exists
if [ -f "$REPO_ROOT/GRAVEYARD.md" ]; then
    git add "$REPO_ROOT/GRAVEYARD.md"
fi
"""


def get_hooks_dir(repo_root: Optional[str] = None) -> str:
    """Return the .git/hooks directory for the given or current repo."""
    if repo_root is None:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_root = result.stdout.strip()
    return os.path.join(repo_root, ".git", "hooks")


def install_hook(repo_root: Optional[str] = None) -> str:
    """
    Install the code-obituary pre-commit hook in the current git repository.

    Returns the path to the installed hook file.
    """
    hooks_dir = get_hooks_dir(repo_root)
    if not os.path.isdir(hooks_dir):
        raise RuntimeError(
            f"No .git/hooks directory found at {hooks_dir}. " "Are you inside a git repository?"
        )

    hook_path = os.path.join(hooks_dir, "pre-commit")

    # If a hook already exists, check if it already has code-obituary
    if os.path.exists(hook_path):
        with open(hook_path, "r") as f:
            existing = f.read()
        if "code-obituary" in existing:
            return hook_path  # Already installed

        # Append our hook to the existing one
        with open(hook_path, "a") as f:
            f.write("\n\n# --- code-obituary hook ---\n")
            # Write the body without the shebang
            body = "\n".join(HOOK_SCRIPT.splitlines()[1:])
            f.write(body)
    else:
        with open(hook_path, "w") as f:
            f.write(HOOK_SCRIPT)

    # Make executable
    current = os.stat(hook_path).st_mode
    os.chmod(hook_path, current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return hook_path


def get_deleted_files_from_git() -> List[str]:
    """Return a list of staged-for-deletion file paths."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--diff-filter=D", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except subprocess.CalledProcessError:
        return []


def get_file_content_from_git(filepath: str) -> Optional[str]:
    """
    Retrieve the content of a file from the HEAD commit (before deletion).
    """
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{filepath}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except Exception:
        return None


def get_repo_root() -> Optional[str]:
    """Return the root of the current git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
