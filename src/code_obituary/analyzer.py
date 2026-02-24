"""
analyzer.py - Reads file content and generates obituaries via AI or template fallback.
"""

import os
import re
import subprocess
from typing import Optional


def extract_symbols(content: str) -> dict:
    """Extract function and class names from source code using regex."""
    functions = re.findall(
        r"^\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
        content,
        re.MULTILINE,
    )
    classes = re.findall(r"^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]", content, re.MULTILINE)
    return {"functions": functions, "classes": classes}


def get_git_dates(filepath: str) -> tuple:
    """Get the first and last git commit dates for a file."""
    try:
        first = subprocess.run(
            ["git", "log", "--follow", "--format=%as", "--", filepath],
            capture_output=True,
            text=True,
            timeout=5,
        )
        dates = [d.strip() for d in first.stdout.strip().splitlines() if d.strip()]
        if dates:
            return dates[-1], dates[0]  # oldest first, newest last
        return None, None
    except Exception:
        return None, None


def get_file_description(filename: str, content: str) -> str:
    """Generate a short human-readable description based on file extension and symbols."""
    ext = os.path.splitext(filename)[1].lower()
    symbols = extract_symbols(content)
    lines = content.splitlines()

    ext_map = {
        ".py": "Python module",
        ".js": "JavaScript module",
        ".ts": "TypeScript module",
        ".tsx": "React TypeScript component",
        ".jsx": "React JavaScript component",
        ".java": "Java class",
        ".rb": "Ruby script",
        ".go": "Go source file",
        ".rs": "Rust source file",
        ".c": "C source file",
        ".cpp": "C++ source file",
        ".cs": "C# source file",
        ".sh": "Shell script",
        ".sql": "SQL script",
        ".yaml": "YAML configuration",
        ".yml": "YAML configuration",
        ".json": "JSON configuration",
        ".md": "Markdown document",
        ".html": "HTML template",
        ".css": "CSS stylesheet",
    }
    file_type = ext_map.get(ext, "source file")

    desc_parts = [f"{filename} was a {file_type} with {len(lines)} lines"]
    if symbols["classes"]:
        desc_parts.append(f"containing the classes: {', '.join(symbols['classes'][:5])}")
    if symbols["functions"]:
        desc_parts.append(f"defining the functions: {', '.join(symbols['functions'][:5])}")

    return ". ".join(desc_parts) + "."


def generate_template_obituary(
    filename: str,
    content: str,
    born: Optional[str] = None,
    died: Optional[str] = None,
    reason: Optional[str] = None,
) -> str:
    """Generate a template-based obituary without an AI API."""
    symbols = extract_symbols(content)
    lines = content.splitlines()
    ext = os.path.splitext(filename)[1].lower()

    ext_roles = {
        ".py": "faithfully served the Python runtime",
        ".js": "brought interactivity to the browser",
        ".ts": "ensured type safety across the codebase",
        ".java": "upheld the Java virtual machine's grand tradition",
        ".rb": "embraced the principle of programmer happiness",
        ".go": "kept concurrency simple and efficient",
        ".rs": "compiled without fear of memory errors",
        ".sh": "automated the mundane so humans didn't have to",
        ".sql": "guarded the sanctity of relational data",
        ".css": "kept the UI beautiful and consistent",
        ".html": "structured content for the world to see",
    }
    role = ext_roles.get(ext, "contributed to the project")

    lifetime = ""
    if born and died:
        lifetime = f" from {born} to {died}"
    elif died:
        lifetime = f" until {died}"

    cause = f" due to: {reason}" if reason else " in the natural course of refactoring"

    survivor_line = ""
    all_symbols = symbols["classes"] + symbols["functions"]
    if all_symbols:
        survivor_line = f" It is survived by the memories of `{'`, `'.join(all_symbols[:3])}`."

    last_words = ""
    non_empty = [
        line.strip() for line in lines if line.strip() and not line.strip().startswith("#")
    ]
    if non_empty:
        snippet = non_empty[0][:60]
        last_words = f'\n\n*Last words: "{snippet}..."*'

    obituary = (
        f"{filename} {role}{lifetime}, spanning {len(lines)} lines of code. "
        f"It was deleted{cause}.{survivor_line}"
        f"{last_words}"
    )
    return obituary


def generate_obituary(
    filename: str,
    content: str,
    reason: Optional[str] = None,
    born: Optional[str] = None,
    died: Optional[str] = None,
) -> str:
    """
    Generate an obituary for the given file content.

    Uses the Anthropic API if ANTHROPIC_API_KEY is set, otherwise falls back
    to a template-based obituary.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if api_key:
        return _generate_ai_obituary(filename, content, reason, born, died, api_key)
    else:
        return generate_template_obituary(filename, content, born, died, reason)


def _generate_ai_obituary(
    filename: str,
    content: str,
    reason: Optional[str],
    born: Optional[str],
    died: Optional[str],
    api_key: str,
) -> str:
    """Generate an obituary using the Anthropic Claude API."""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        symbols = extract_symbols(content)
        lines = content.splitlines()

        lifetime_str = ""
        if born and died:
            lifetime_str = f"It was created on {born} and deleted on {died}."
        elif died:
            lifetime_str = f"It was deleted on {died}."

        cause_str = (
            f"Cause of death: {reason}"
            if reason
            else "Cause of death: unknown (likely refactoring or replacement)."
        )

        symbols_str = ""
        if symbols["classes"] or symbols["functions"]:
            parts = []
            if symbols["classes"]:
                parts.append(f"Classes: {', '.join(symbols['classes'])}")
            if symbols["functions"]:
                parts.append(f"Functions: {', '.join(symbols['functions'])}")
            symbols_str = ". ".join(parts) + "."

        # Truncate content to avoid huge prompts
        content_preview = content[:2000] if len(content) > 2000 else content

        prompt = f"""You are writing a poetic, brief obituary for a deleted piece of code.
Write 3-5 sentences in a respectful, slightly melancholy tone like an obituary in a newspaper.
Mention what the code did, how long it lived, and what caused its deletion.
Be creative but concise. Do not use markdown headers. Plain prose only.

File: {filename}
Lines of code: {len(lines)}
{lifetime_str}
{cause_str}
{symbols_str}

Code content (preview):
```
{content_preview}
```

Write the obituary now:"""

        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    except Exception as e:
        # Fall back to template if AI call fails
        return (
            generate_template_obituary(filename, content, born, died, reason)
            + f"\n\n*(AI obituary unavailable: {e})*"
        )
