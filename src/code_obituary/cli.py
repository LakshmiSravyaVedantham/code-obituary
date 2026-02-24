"""
cli.py - Click CLI for code-obituary.

Commands:
  mourn    - Manually mourn a specific file
  install  - Install the git pre-commit hook
  view     - Display GRAVEYARD.md
  list     - List all obituaries with dates
"""

import os
import sys
from datetime import date
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .analyzer import generate_obituary, get_git_dates
from .graveyard import append_obituary, list_obituaries, read_graveyard
from .hook import (
    get_file_content_from_git,
    get_repo_root,
    install_hook,
)

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="code-obituary")
def main() -> None:
    """
    code-obituary - Write AI-generated obituaries for deleted code.

    Because every function deserves a proper farewell.
    """
    pass


@main.command()
@click.argument("filepath")
@click.option("--reason", "-r", default=None, help="Cause of death for this file.")
@click.option(
    "--from-git",
    is_flag=True,
    default=False,
    help="Read file content from git HEAD (for use in pre-commit hook).",
)
@click.option("--repo-root", default=None, help="Path to the repository root.")
def mourn(filepath: str, reason: Optional[str], from_git: bool, repo_root: Optional[str]) -> None:
    """
    Write an obituary for a deleted or soon-to-be-deleted file.

    FILEPATH is the path to the file to mourn.
    """
    repo_root = repo_root or get_repo_root() or os.getcwd()

    # Determine the display name (relative path is cleaner)
    try:
        display_name = os.path.relpath(filepath, repo_root)
    except ValueError:
        display_name = os.path.basename(filepath)

    # Get file content
    content: Optional[str] = None

    if from_git:
        content = get_file_content_from_git(filepath)
        if content is None:
            # Try relative path
            rel = os.path.relpath(filepath, repo_root) if repo_root else filepath
            content = get_file_content_from_git(rel)

    if content is None and os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as exc:
            console.print(f"[red]Error reading file: {exc}[/red]")
            sys.exit(1)

    if content is None:
        content = f"# {display_name}\n# (content not available)\n"
        console.print(
            f"[yellow]Warning: Could not read file content for {filepath}. "
            "Using placeholder.[/yellow]"
        )

    # Get git dates
    born, died_date = get_git_dates(filepath)
    died_str = died_date or str(date.today())

    # Get first non-empty, non-comment line as "last words"
    lines = content.splitlines()
    last_words = ""
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
            last_words = stripped[:80]
            break

    console.print(Panel(f"[bold yellow]Mourning[/bold yellow] {display_name}...", expand=False))

    with console.status("[bold green]Generating obituary...[/bold green]"):
        obituary = generate_obituary(
            filename=display_name,
            content=content,
            reason=reason,
            born=born,
            died=died_str,
        )

    metadata = {
        "born": born or "unknown",
        "died": died_str,
        "reason": reason or "Deleted (cause unknown)",
        "last_words": last_words,
    }

    entry = append_obituary(repo_root, display_name, obituary, metadata)

    console.print("\n[bold green]Obituary written:[/bold green]\n")
    console.print(Markdown(entry))
    console.print(f"\n[dim]Appended to {os.path.join(repo_root, 'GRAVEYARD.md')}[/dim]")


@main.command()
@click.option("--repo-root", default=None, help="Path to the repository root.")
def install(repo_root: Optional[str]) -> None:
    """Install the code-obituary pre-commit hook in the current git repository."""
    repo_root = repo_root or get_repo_root()
    if repo_root is None:
        console.print(
            "[red]Error: Not inside a git repository. "
            "Run this command from within a git repo.[/red]"
        )
        sys.exit(1)

    try:
        hook_path = install_hook(repo_root)
        console.print(
            Panel(
                f"[bold green]Hook installed successfully![/bold green]\n\n"
                f"Hook path: [cyan]{hook_path}[/cyan]\n\n"
                "Now, whenever you commit a deletion, code-obituary will automatically\n"
                "write an obituary to [cyan]GRAVEYARD.md[/cyan].",
                title="[bold]code-obituary[/bold]",
                expand=False,
            )
        )
    except RuntimeError as exc:
        console.print(f"[red]Error: {exc}[/red]")
        sys.exit(1)


@main.command()
@click.option("--repo-root", default=None, help="Path to the repository root.")
def view(repo_root: Optional[str]) -> None:
    """Display the contents of GRAVEYARD.md."""
    repo_root = repo_root or get_repo_root() or os.getcwd()
    content = read_graveyard(repo_root)

    if content.startswith("No GRAVEYARD.md"):
        console.print(f"[yellow]{content}[/yellow]")
    else:
        console.print(Markdown(content))


@main.command("list")
@click.option("--repo-root", default=None, help="Path to the repository root.")
def list_cmd(repo_root: Optional[str]) -> None:
    """List all obituaries in GRAVEYARD.md with their dates."""
    repo_root = repo_root or get_repo_root() or os.getcwd()
    obituaries = list_obituaries(repo_root)

    if not obituaries:
        console.print("[yellow]No obituaries found. The graveyard is empty.[/yellow]")
        return

    table = Table(title="[bold]Code Graveyard[/bold]", show_lines=True)
    table.add_column("File", style="cyan", no_wrap=True)
    table.add_column("Lived", style="magenta")
    table.add_column("Cause of Death", style="red")
    table.add_column("Obituary (excerpt)", style="dim")

    for obit in obituaries:
        excerpt = obit["body"][:80] + "..." if len(obit["body"]) > 80 else obit["body"]
        table.add_row(
            obit["filename"],
            obit["lived"],
            obit["cause"],
            excerpt,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(obituaries)} obituary(ies)[/dim]")


if __name__ == "__main__":
    main()
