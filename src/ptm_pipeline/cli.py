"""CLI entry point for PTM pipeline."""

from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import cyclopts
from rich.console import Console

console = Console()

app = cyclopts.App(
    name="ptm-pipeline",
    help="PTM Pipeline - Deploy phosphoproteomics analysis pipeline to new projects.",
    version=version("ptm-pipeline"),
)


@app.command
def init(
    input_dir: Annotated[Path, cyclopts.Parameter(help="Directory containing DEA folders")] = Path("."),
    output_dir: Annotated[Path, cyclopts.Parameter(help="Output directory for pipeline files (defaults to current directory)")] = Path("."),
    *,
    name: Annotated[str | None, cyclopts.Parameter(name=["--name", "-n"], help="Experiment name (auto-detected if not provided)")] = None,
    dry_run: Annotated[bool, cyclopts.Parameter(help="Show what would be done without making changes")] = False,
    force: Annotated[bool, cyclopts.Parameter(name=["--force", "-f"], help="Overwrite existing files")] = False,
    default: Annotated[bool, cyclopts.Parameter(name=["--default", "-d"], help="Non-interactive mode: use defaults for all prompts")] = False,
):
    """Initialize PTM pipeline in a project directory.

    Discovers DEA folders from INPUT_DIR, writes pipeline files to OUTPUT_DIR.
    Use --default for fully non-interactive initialization with default settings.
    """
    from .init import init_project

    if not input_dir.exists():
        console.print(f"[red]Error:[/red] Input directory does not exist: {input_dir}")
        raise SystemExit(1)

    if not output_dir.exists():
        console.print(f"[red]Error:[/red] Output directory does not exist: {output_dir}")
        raise SystemExit(1)

    success = init_project(
        project_dir=output_dir,
        input_dir=input_dir,
        name=name,
        dry_run=dry_run,
        force=force,
        default=default,
    )

    raise SystemExit(0 if success else 1)


@app.command
def init_default(
    input_dir: Annotated[Path, cyclopts.Parameter(help="Directory containing DEA folders")] = Path("."),
    output_dir: Annotated[Path, cyclopts.Parameter(help="Output directory for pipeline files (created if needed, defaults to .)")] = Path("."),
):
    """Initialize PTM pipeline with all defaults (non-interactive).

    Discovers DEA folders from INPUT_DIR, writes pipeline files to OUTPUT_DIR.
    OUTPUT_DIR is created if it does not exist.

    Examples:
        ptm-pipeline init-default data/FP_TMT/ PTM_FP_TMT/
        ptm-pipeline init-default .
    """
    from .init import init_project

    if not input_dir.exists():
        console.print(f"[red]Error:[/red] Input directory does not exist: {input_dir}")
        raise SystemExit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    success = init_project(
        project_dir=output_dir,
        input_dir=input_dir,
        default=True,
        force=True,
    )

    raise SystemExit(0 if success else 1)


@app.command
def run(
    directory: Annotated[Path, cyclopts.Parameter(help="Project directory containing ptm_config.yaml and Snakefile")] = Path("."),
    *,
    cores: Annotated[int, cyclopts.Parameter(name=["--cores", "-j"], help="Number of cores for Snakemake")] = 1,
    dry_run: Annotated[bool, cyclopts.Parameter(name=["--dry-run", "-n"], help="Show what would be executed")] = False,
    target: Annotated[str, cyclopts.Parameter(help="Snakemake target")] = "all",
):
    """Run the PTM analysis pipeline.

    Executes Snakemake in the specified project directory.

    Examples:
        ptm-pipeline run data/PTM_FP_TMT/
        ptm-pipeline run data/PTM_FP_TMT/ --dry-run
        ptm-pipeline run data/PTM_FP_TMT/ -j4
    """
    import subprocess

    directory = directory.resolve()

    config_file = directory / "ptm_config.yaml"
    snakefile = directory / "Snakefile"

    if not config_file.exists():
        console.print(f"[red]Error:[/red] No ptm_config.yaml found in {directory}")
        console.print("Run 'ptm-pipeline init' or 'ptm-pipeline init-default' first.")
        raise SystemExit(1)

    if not snakefile.exists():
        console.print(f"[red]Error:[/red] No Snakefile found in {directory}")
        raise SystemExit(1)

    cmd = [
        "snakemake",
        "-s", str(snakefile),
        "--configfile", str(config_file),
        f"-j{cores}",
    ]
    if dry_run:
        cmd.append("-n")
    cmd.append(target)

    console.print(f"[bold]Running pipeline in:[/bold] {directory}")
    console.print(f"[dim]$ {' '.join(cmd)}[/dim]\n")

    result = subprocess.run(cmd, cwd=directory)
    raise SystemExit(result.returncode)


@app.command
def validate(
    directory: Annotated[Path, cyclopts.Parameter(help="Project directory to validate")] = Path("."),
    *,
    quick: Annotated[bool, cyclopts.Parameter(name=["--quick", "-q"], help="Skip slow checks (R packages, uv tools)")] = False,
):
    """Validate project setup for PTM pipeline.

    Checks that all required files, R packages, and tools are available.
    """
    from .validate import validate_project

    if not directory.exists():
        console.print(f"[red]Error:[/red] Directory does not exist: {directory}")
        raise SystemExit(1)

    success = validate_project(project_dir=directory, quick=quick)

    raise SystemExit(0 if success else 1)


@app.command
def update(
    directory: Annotated[Path, cyclopts.Parameter(help="Project directory to update")] = Path("."),
    *,
    dry_run: Annotated[bool, cyclopts.Parameter(help="Show what would be updated")] = False,
):
    """Update pipeline files to latest version.

    Copies new versions of Snakefile, helpers.py, and src/ files
    while preserving config.yaml.
    """
    from .init import copy_template_files, get_template_dir

    if not directory.exists():
        console.print(f"[red]Error:[/red] Directory does not exist: {directory}")
        raise SystemExit(1)

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
        console.print("\n[yellow]Dry run complete.[/yellow] No files were modified.")
    else:
        console.print(f"\n[green]Updated {len(copied)} files.[/green]")
        console.print("  ptm_config.yaml was preserved.")


@app.command
def clean(
    directory: Annotated[Path, cyclopts.Parameter(help="Project directory to clean")] = Path("."),
    *,
    dry_run: Annotated[bool, cyclopts.Parameter(help="Show what would be removed")] = False,
    force: Annotated[bool, cyclopts.Parameter(name=["--force", "-f"], help="Skip confirmation prompt")] = False,
):
    """Remove pipeline files created by init.

    Removes ptm_config.yaml, Snakefile, helpers.py, Makefile, and src/.
    DEA folders and other project data are preserved.
    """
    from .clean import clean_project

    if not directory.exists():
        console.print(f"[red]Error:[/red] Directory does not exist: {directory}")
        raise SystemExit(1)

    success = clean_project(
        project_dir=directory,
        dry_run=dry_run,
        force=force,
    )

    raise SystemExit(0 if success else 1)


@app.command
def info(
    directory: Annotated[Path, cyclopts.Parameter(help="Directory to scan for DEA folders")] = Path("."),
):
    """Show information about discovered DEA folders.

    Useful for debugging auto-discovery before running init.
    """
    from .discover import find_all_dea_folders, find_annotation_file, parse_contrasts
    from rich.table import Table

    if not directory.exists():
        console.print(f"[red]Error:[/red] Directory does not exist: {directory}")
        raise SystemExit(1)

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


def main():
    app()


if __name__ == "__main__":
    main()
