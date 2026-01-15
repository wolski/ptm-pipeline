"""Clean up pipeline files created by init."""

from pathlib import Path
import shutil

from rich.console import Console
from rich.prompt import Confirm


console = Console()

# Files and directories created by init
PIPELINE_FILES = [
    "ptm_config.yaml",
    "Snakefile",
    "helpers.py",
    "Makefile",
]

PIPELINE_DIRS = [
    "src",
]


def get_files_to_remove(project_dir: Path) -> tuple[list[Path], list[Path]]:
    """Get lists of files and directories that would be removed.

    Returns:
        Tuple of (files, directories) that exist and would be removed.
    """
    files = []
    dirs = []

    for filename in PIPELINE_FILES:
        path = project_dir / filename
        if path.exists():
            files.append(path)

    for dirname in PIPELINE_DIRS:
        path = project_dir / dirname
        if path.exists() and path.is_dir():
            dirs.append(path)

    return files, dirs


def clean_project(
    project_dir: Path,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """Remove pipeline files from project directory.

    Args:
        project_dir: Path to project directory
        dry_run: If True, only show what would be done
        force: If True, skip confirmation prompt

    Returns:
        True if cleanup was successful
    """
    project_dir = project_dir.resolve()

    console.print(f"\n[bold]Cleaning PTM pipeline from:[/bold] {project_dir}\n")

    files, dirs = get_files_to_remove(project_dir)

    if not files and not dirs:
        console.print("[yellow]No pipeline files found to remove.[/yellow]")
        console.print("  (Looking for: ptm_config.yaml, Snakefile, helpers.py, Makefile, src/)")
        return True

    # Show what will be removed
    console.print("[bold]Files to remove:[/bold]")
    for f in files:
        console.print(f"  - {f.name}")

    console.print("\n[bold]Directories to remove:[/bold]")
    for d in dirs:
        # Count files in directory
        file_count = sum(1 for _ in d.rglob("*") if _.is_file())
        console.print(f"  - {d.name}/ ({file_count} files)")

    if dry_run:
        console.print("\n[yellow]Dry run complete.[/yellow] No files were removed.")
        return True

    # Confirm unless force
    if not force:
        console.print()
        if not Confirm.ask("[red]Remove these files?[/red]", default=False):
            console.print("Cancelled.")
            return False

    # Remove files
    console.print("\n[bold]Removing files...[/bold]")
    for f in files:
        try:
            f.unlink()
            console.print(f"  [red]Removed:[/red] {f.name}")
        except OSError as e:
            console.print(f"  [red]Error removing {f.name}:[/red] {e}")
            return False

    # Remove directories
    for d in dirs:
        try:
            shutil.rmtree(d)
            console.print(f"  [red]Removed:[/red] {d.name}/")
        except OSError as e:
            console.print(f"  [red]Error removing {d.name}/:[/red] {e}")
            return False

    console.print("\n[green]Cleanup complete.[/green]")
    console.print("  DEA folders and other project data were preserved.")

    return True
