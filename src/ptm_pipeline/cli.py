"""CLI entry point for PTM pipeline."""

from importlib.metadata import version
from pathlib import Path
import click
from rich.console import Console


console = Console()


@click.group()
@click.version_option(version=version("ptm-pipeline"))
def main():
    """PTM Pipeline - Deploy phosphoproteomics analysis pipeline to new projects."""
    pass


@main.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--name", "-n", help="Experiment name (auto-detected if not provided)")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files")
def init(directory: Path, name: str | None, dry_run: bool, force: bool):
    """Initialize PTM pipeline in a project directory.

    Discovers DEA folders, generates config.yaml, and copies pipeline files.

    DIRECTORY defaults to current directory if not specified.
    """
    from .init import init_project

    success = init_project(
        project_dir=directory,
        name=name,
        dry_run=dry_run,
        force=force,
    )

    raise SystemExit(0 if success else 1)


@main.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--quick", "-q", is_flag=True, help="Skip slow checks (R packages, uv tools)")
def validate(directory: Path, quick: bool):
    """Validate project setup for PTM pipeline.

    Checks that all required files, R packages, and tools are available.

    DIRECTORY defaults to current directory if not specified.
    """
    from .validate import validate_project

    success = validate_project(project_dir=directory, quick=quick)

    raise SystemExit(0 if success else 1)


@main.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--dry-run", is_flag=True, help="Show what would be updated")
def update(directory: Path, dry_run: bool):
    """Update pipeline files to latest version.

    Copies new versions of Snakefile, helpers.py, and src/ files
    while preserving config.yaml.

    DIRECTORY defaults to current directory if not specified.
    """
    from .init import copy_template_files, get_template_dir

    directory = directory.resolve()

    # Check config exists (don't update uninitialized projects)
    config_file = directory / "ptm_config.yaml"
    if not config_file.exists():
        console.print("[red]Error:[/red] No ptm_config.yaml found. Run 'ptm-pipeline init' first.")
        raise SystemExit(1)

    console.print(f"\n[bold]Updating PTM pipeline in:[/bold] {directory}\n")

    try:
        template_dir = get_template_dir()
        console.print(f"[dim]Template source: {template_dir}[/dim]\n")
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    copied = copy_template_files(directory, dry_run=dry_run)

    action = "Would update" if dry_run else "Updated"
    for f in copied:
        console.print(f"  {action}: {f}")

    if dry_run:
        console.print(f"\n[yellow]Dry run complete.[/yellow] No files were modified.")
    else:
        console.print(f"\n[green]Updated {len(copied)} files.[/green]")
        console.print("  ptm_config.yaml was preserved.")


@main.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--dry-run", is_flag=True, help="Show what would be removed")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def clean(directory: Path, dry_run: bool, force: bool):
    """Remove pipeline files created by init.

    Removes ptm_config.yaml, SnakefileV2.smk, helpers.py, Makefile, and src/.
    DEA folders and other project data are preserved.

    DIRECTORY defaults to current directory if not specified.
    """
    from .clean import clean_project

    success = clean_project(
        project_dir=directory,
        dry_run=dry_run,
        force=force,
    )

    raise SystemExit(0 if success else 1)


@main.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path), default=".")
def info(directory: Path):
    """Show information about discovered DEA folders.

    Useful for debugging auto-discovery before running init.
    """
    from .discover import find_all_dea_folders, find_annotation_file, parse_contrasts
    from rich.table import Table

    directory = directory.resolve()

    console.print(f"\n[bold]Scanning:[/bold] {directory}\n")

    folders = find_all_dea_folders(directory)

    if not folders["phospho"] and not folders["protein"]:
        console.print("[yellow]No DEA folders found.[/yellow]")
        console.print("[dim]Phospho patterns: DEA_*_WUphospho_*, DEA_*_WUcombined_*, DEA_*_*STY*[/dim]")
        console.print("[dim]Protein patterns: DEA_*_WUprot_*, DEA_*_WUtotal_*[/dim]")
        return

    # Phospho folders
    table = Table(title="Phospho DEA Folders")
    table.add_column("#", style="dim")
    table.add_column("Folder", style="green")
    table.add_column("Annotation File")

    for i, d in enumerate(folders["phospho"], 1):
        annot = find_annotation_file(d)
        annot_str = annot.name if annot else "[red]Not found[/red]"
        table.add_row(str(i), d.name, annot_str)

    if folders["phospho"]:
        console.print(table)
    else:
        console.print("[yellow]No phospho DEA folders found[/yellow]")
        console.print("[dim]  Patterns: DEA_*_WUphospho_*, DEA_*_WUcombined_*, DEA_*_*STY*[/dim]")

    console.print()

    # Protein folders
    table = Table(title="Protein DEA Folders")
    table.add_column("#", style="dim")
    table.add_column("Folder", style="green")

    for i, d in enumerate(folders["protein"], 1):
        table.add_row(str(i), d.name)

    if folders["protein"]:
        console.print(table)
    else:
        console.print("[yellow]No protein DEA folders found (DEA_*_WUprot_* or DEA_*_WUtotal_*)[/yellow]")

    # Show contrasts from first phospho folder
    if folders["phospho"]:
        annot = find_annotation_file(folders["phospho"][0])
        if annot:
            contrasts = parse_contrasts(annot)
            console.print(f"\n[bold]Contrasts from {annot.name}:[/bold]")
            for c in contrasts:
                console.print(f"  - {c}")


if __name__ == "__main__":
    main()
