"""Project initialization logic."""

from pathlib import Path
import shutil
import importlib.resources

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from .discover import (
    find_dea_folders,
    find_all_dea_folders,
    find_annotation_file,
    parse_contrasts,
    get_experiment_name,
)
from .config import generate_config, write_config, config_to_yaml_string


console = Console()


def get_template_dir() -> Path:
    """Get path to template directory from package data."""
    # Try installed package location first
    try:
        import sys
        if sys.prefix != sys.base_prefix:
            # In a virtual environment
            template_path = Path(sys.prefix) / "share" / "ptm-pipeline" / "template"
            if template_path.exists():
                return template_path

        # Try site-packages location
        import ptm_pipeline
        pkg_dir = Path(ptm_pipeline.__file__).parent
        template_path = pkg_dir.parent.parent / "template"
        if template_path.exists():
            return template_path

        # Development mode - look relative to package
        template_path = pkg_dir.parent.parent.parent / "template"
        if template_path.exists():
            return template_path

    except Exception:
        pass

    raise FileNotFoundError(
        "Could not find template directory. "
        "Make sure the package is installed correctly."
    )


def copy_template_files(project_dir: Path, dry_run: bool = False) -> list[str]:
    """Copy template files to project directory.

    Returns list of copied file paths (relative to project_dir).
    """
    template_dir = get_template_dir()
    copied_files = []

    # Files to copy at root level
    root_files = ["SnakefileV2.smk", "helpers.py"]

    for filename in root_files:
        src = template_dir / filename
        dst = project_dir / filename
        if src.exists():
            if not dry_run:
                shutil.copy2(src, dst)
            copied_files.append(filename)

    # Copy src/ directory
    src_dir = template_dir / "src"
    dst_src_dir = project_dir / "src"

    if src_dir.exists():
        if not dry_run:
            if dst_src_dir.exists():
                shutil.rmtree(dst_src_dir)
            shutil.copytree(src_dir, dst_src_dir)

        for f in src_dir.rglob("*"):
            if f.is_file():
                rel_path = f.relative_to(template_dir)
                copied_files.append(str(rel_path))

    return copied_files


def init_project(
    project_dir: Path,
    name: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """Initialize PTM pipeline in project directory.

    Args:
        project_dir: Path to project directory
        name: Optional experiment name (auto-detected if not provided)
        dry_run: If True, only show what would be done
        force: If True, overwrite existing files

    Returns:
        True if initialization was successful
    """
    project_dir = project_dir.resolve()

    console.print(f"\n[bold]Initializing PTM pipeline in:[/bold] {project_dir}\n")

    # Check if already initialized
    config_file = project_dir / "ptm_config.yaml"
    snakefile = project_dir / "SnakefileV2.smk"

    if (config_file.exists() or snakefile.exists()) and not force:
        console.print(
            "[yellow]Warning:[/yellow] Pipeline files already exist. "
            "Use --force to overwrite."
        )
        if not Confirm.ask("Continue anyway?"):
            return False

    # Discover DEA folders
    console.print("[bold]Discovering DEA folders...[/bold]")
    all_folders = find_all_dea_folders(project_dir)

    if not all_folders["phospho"]:
        console.print("[red]Error:[/red] No phospho DEA folder found")
        console.print("  Expected patterns: DEA_*_WUphospho_*, DEA_*_WUcombined_*, DEA_*_*STY*")
        return False

    if not all_folders["protein"]:
        console.print("[red]Error:[/red] No protein DEA folder found (DEA_*_WUprot_* or DEA_*_WUtotal_*)")
        return False

    # Select folders if multiple found
    phospho_dir = all_folders["phospho"][0]
    protein_dir = all_folders["protein"][0]

    if len(all_folders["phospho"]) > 1:
        console.print("\n[yellow]Multiple phospho DEA folders found:[/yellow]")
        for i, d in enumerate(all_folders["phospho"]):
            console.print(f"  {i + 1}. {d.name}")
        choice = Prompt.ask(
            "Select folder",
            choices=[str(i + 1) for i in range(len(all_folders["phospho"]))],
            default="1"
        )
        phospho_dir = all_folders["phospho"][int(choice) - 1]

    if len(all_folders["protein"]) > 1:
        console.print("\n[yellow]Multiple protein DEA folders found:[/yellow]")
        for i, d in enumerate(all_folders["protein"]):
            console.print(f"  {i + 1}. {d.name}")
        choice = Prompt.ask(
            "Select folder",
            choices=[str(i + 1) for i in range(len(all_folders["protein"]))],
            default="1"
        )
        protein_dir = all_folders["protein"][int(choice) - 1]

    # Show selected folders
    table = Table(title="Selected DEA Folders")
    table.add_column("Type", style="cyan")
    table.add_column("Folder", style="green")
    table.add_row("Phospho", phospho_dir.name)
    table.add_row("Protein", protein_dir.name)
    console.print(table)

    # Find annotation file
    console.print("\n[bold]Looking for annotation file...[/bold]")
    annot_file = find_annotation_file(phospho_dir)

    if not annot_file:
        console.print("[red]Error:[/red] No annotation file found in phospho DEA folder")
        console.print("  Expected: Inputs_*/*_annot_*.tsv or Inputs_*/*_dataset*.tsv")
        return False

    console.print(f"  Found: {annot_file.relative_to(project_dir)}")

    # Parse contrasts
    console.print("\n[bold]Parsing contrasts...[/bold]")
    contrasts = parse_contrasts(annot_file)

    if not contrasts:
        console.print("[yellow]Warning:[/yellow] No contrasts found in annotation file")
        contrasts = ["contrast1"]  # Placeholder
    else:
        console.print(f"  Found {len(contrasts)} contrast(s):")
        for c in contrasts:
            console.print(f"    - {c}")

    # Get experiment name - suggest first contrast as default
    if not name:
        if contrasts and contrasts[0] != "contrast1":
            default_name = contrasts[0]
        else:
            default_name = get_experiment_name(phospho_dir)
        console.print(f"\n[bold]Suggested experiment name:[/bold] {default_name}")
        name = Prompt.ask("Experiment name", default=default_name)

    # Get significance thresholds
    console.print("\n[bold]Significance thresholds for downstream analyses:[/bold]")
    fdr = float(Prompt.ask("FDR threshold", default="0.25"))
    log2fc = float(Prompt.ask("log2FC threshold", default="0.5"))

    # Generate config
    console.print("\n[bold]Generating configuration...[/bold]")
    config = generate_config(
        phospho_dir=phospho_dir,
        protein_dir=protein_dir,
        annot_file=annot_file,
        contrasts=contrasts,
        output_name=name,
        project_dir=project_dir,
        fdr=fdr,
        log2fc=log2fc,
    )

    if dry_run:
        console.print("\n[yellow]Dry run - ptm_config.yaml would contain:[/yellow]")
        console.print(Panel(config_to_yaml_string(config), title="ptm_config.yaml"))
    else:
        write_config(config, config_file)
        console.print(f"  Written: ptm_config.yaml")

    # Copy template files
    console.print("\n[bold]Copying pipeline files...[/bold]")

    try:
        copied = copy_template_files(project_dir, dry_run=dry_run)
        for f in copied[:5]:  # Show first 5
            console.print(f"  {'Would copy' if dry_run else 'Copied'}: {f}")
        if len(copied) > 5:
            console.print(f"  ... and {len(copied) - 5} more files")
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        return False

    # Success message
    console.print("\n" + "=" * 60)
    if dry_run:
        console.print("[yellow]Dry run complete.[/yellow] No files were modified.")
    else:
        console.print("[green]Pipeline initialized successfully![/green]")
        console.print("\nNext steps:")
        console.print(f"  1. Review ptm_config.yaml")
        console.print(f"  2. Run: snakemake -s SnakefileV2.smk --configfile ptm_config.yaml -n all  # dry-run")
        console.print(f"  3. Run: snakemake -s SnakefileV2.smk --configfile ptm_config.yaml -j1 all")

    return True
