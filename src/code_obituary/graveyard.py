"""
graveyard.py - Reads and writes GRAVEYARD.md for the code obituary project.
"""

import os
import re
from datetime import date
from typing import Optional

GRAVEYARD_HEADER = """# \U0001fab6 GRAVEYARD.md

*Here lie the fallen code, remembered but no longer needed.*

---
"""


def get_graveyard_path(repo_root: str) -> str:
    """Return the path to GRAVEYARD.md in the repo root."""
    return os.path.join(repo_root, "GRAVEYARD.md")


def ensure_graveyard(repo_root: str) -> None:
    """Create GRAVEYARD.md with header if it does not exist."""
    path = get_graveyard_path(repo_root)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(GRAVEYARD_HEADER)


def append_obituary(
    repo_root: str,
    filename: str,
    obituary: str,
    metadata: Optional[dict] = None,
) -> str:
    """
    Append an obituary entry to GRAVEYARD.md.

    Args:
        repo_root: Path to the repository root.
        filename: Name of the deleted file.
        obituary: The generated obituary text.
        metadata: Optional dict with keys: born, died, reason, last_words.

    Returns:
        The formatted obituary entry that was appended.
    """
    ensure_graveyard(repo_root)
    meta = metadata or {}

    born = meta.get("born", "unknown")
    died = meta.get("died", str(date.today()))
    reason = meta.get("reason", "Unknown")
    last_words = meta.get("last_words", "")

    entry_lines = [
        f"\n## {filename}\n",
        f"**Lived:** {born} \u2014 {died}  \n",
        f"**Cause of death:** {reason}  \n",
    ]
    if last_words:
        entry_lines.append(f'**Last words:** `"{last_words[:80]}..."`\n')

    entry_lines.append("\n")
    # Wrap obituary lines with > blockquote style
    for line in obituary.splitlines():
        if line.strip():
            entry_lines.append(f"> {line}\n")
        else:
            entry_lines.append(">\n")

    entry_lines.append("\n---\n")

    entry = "".join(entry_lines)

    graveyard_path = get_graveyard_path(repo_root)
    with open(graveyard_path, "a", encoding="utf-8") as f:
        f.write(entry)

    return entry


def list_obituaries(repo_root: str) -> list:
    """
    Parse GRAVEYARD.md and return a list of obituary records.

    Each record is a dict with keys: filename, lived, cause, body.
    """
    path = get_graveyard_path(repo_root)
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    obituaries = []
    # Split on ## headings (each obituary starts with ## filename)
    sections = re.split(r"\n## ", content)

    for section in sections[1:]:  # skip the header section
        lines = section.splitlines()
        if not lines:
            continue

        filename = lines[0].strip()
        lived = ""
        cause = ""
        body_lines = []

        for line in lines[1:]:
            lived_match = re.match(r"\*\*Lived:\*\*\s*(.+)", line)
            cause_match = re.match(r"\*\*Cause of death:\*\*\s*(.+)", line)
            body_match = re.match(r"^>\s?(.*)", line)

            if lived_match:
                lived = lived_match.group(1).strip().rstrip("  ")
            elif cause_match:
                cause = cause_match.group(1).strip().rstrip("  ")
            elif body_match:
                body_lines.append(body_match.group(1))

        body = " ".join(body_lines).strip()
        obituaries.append(
            {
                "filename": filename,
                "lived": lived,
                "cause": cause,
                "body": body,
            }
        )

    return obituaries


def read_graveyard(repo_root: str) -> str:
    """Return the full contents of GRAVEYARD.md, or a message if it doesn't exist."""
    path = get_graveyard_path(repo_root)
    if not os.path.exists(path):
        return "No GRAVEYARD.md found. No code has been mourned yet."
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
