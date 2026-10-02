"""Project initialization logic."""

from pathlib import Path
import shutil
import subprocess

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.panel import Panel
from rich.table import Table

from .discover import (
    find_all_dea_folders,
    find_dea_anndata,
    read_dea_contrasts,
    get_experiment_name,
)
from .config import UPLOAD_TARGET_FILE, config_to_yaml_string, generate_config, write_config, write_upload_target
from .clean import generated_makefile


console = Console()


def get_template_dir() -> Path:
    """Get path to template directory from package data."""
    try:
        import ptm_pipeline
        pkg_dir = Path(ptm_pipeline.__file__).parent

        # Prefer the template beside an editable source checkout. A virtual
        # environment may retain an older installed copy under share/.
        template_path = pkg_dir.parent.parent / "template"
        if template_path.exists():
            return template_path

        # Try one level above the normal editable-install layout.
        template_path = pkg_dir.parent.parent.parent / "template"
        if template_path.exists():
            return template_path

        import sys
        if sys.prefix != sys.base_prefix:
            template_path = Path(sys.prefix) / "share" / "ptm-pipeline" / "template"
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

    The project gets Snakefile, helpers.py and the ptm.sh wrapper. No R code or
    report template is copied, because there is none to copy -- every rule
    reaches its R script and report through that wrapper, which resolves them
    from the installed package.

    Returns list of copied file paths (relative to project_dir).
    """
    template_dir = get_template_dir()
    copied_files = []

    # Files to copy at root level
    root_files = ["Snakefile", "helpers.py"]

    for filename in root_files:
        src = template_dir / filename
        dst = project_dir / filename
        if src.exists():
            if not dry_run:
                shutil.copy2(src, dst)
            copied_files.append(filename)

    copied_files.extend(copy_shell_wrapper(project_dir, dry_run=dry_run))
    legacy_makefile = generated_makefile(project_dir)
    if legacy_makefile is not None:
        if not dry_run:
            legacy_makefile.unlink()
        console.print(f"  {'Would remove' if dry_run else 'Removed'} generated Makefile")

    return copied_files


def copy_shell_wrapper(project_dir: Path, dry_run: bool = False) -> list[str]:
    """Place prophosqua's ptm.sh wrapper in the project directory.

    The Snakefile calls the wrapper at its install path, so this copy is for a
    person at a prompt: running ./ptm.sh dpa_dpu by hand is running exactly what
    the pipeline runs, and ./ptm.sh help lists the steps. The wrapper resolves
    both its command list and each command's R script from the installed
    package, so the copy carries no analysis logic and cannot drift.
    """
    if dry_run:
        return ["ptm.sh"]

    result = subprocess.run(
        [
            "Rscript", "--vanilla", "-e",
            "invisible(prophosqua::copy_ptm_shell_script("
            f'{_r_string(str(project_dir))}))',
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        console.print(
            "[yellow]Warning:[/yellow] could not copy the prophosqua ptm.sh "
            "wrapper. The pipeline still runs -- it calls it at its install "
            "path -- but it will not be here to call by hand."
        )
        console.print(f"  {result.stderr.strip().splitlines()[-1:] or ''}")
        return []

    return sorted(p.name for p in project_dir.glob("ptm.sh"))


def _r_string(value: str) -> str:
    """Quote a path for interpolation into an R expression."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _select_folder(kind: str, folders: list[Path], default: bool) -> Path:
    """The first folder, or the one chosen when several are found and prompting is allowed."""
    if len(folders) == 1 or default:
        return folders[0]
    console.print(f"\n[yellow]Multiple {kind} DEA folders found:[/yellow]")
    for i, d in enumerate(folders):
        console.print(f"  {i + 1}. {d.name}")
    choice = Prompt.ask(
        "Select folder",
        choices=[str(i + 1) for i in range(len(folders))],
        default="1"
    )
    return folders[int(choice) - 1]


def init_project(
    project_dir: Path,
    input_dir: Path | None = None,
    name: str | None = None,
    dry_run: bool = False,
    force: bool = False,
    default: bool = False,
    order_id: int | None = None,
    workunit_name: str | None = None,
    run_proptm3d: bool = True,
) -> bool:
    """Initialize PTM pipeline in project directory.

    Args:
        project_dir: Path to project directory (where pipeline files are written)
        input_dir: Path to directory containing DEA folders (defaults to project_dir)
        name: Optional experiment name (auto-detected if not provided)
        dry_run: If True, only show what would be done
        force: If True, overwrite existing files
        default: If True, use defaults for all prompts (non-interactive)
        order_id: B-Fabric order the upload command targets; prompted for if missing
        workunit_name: Base workunit name for the uploads; defaults to the experiment name
        run_proptm3d: Prepare and bundle the proptm3d browser in a full run

    Returns:
        True if initialization was successful
    """
    project_dir = project_dir.resolve()
    input_dir = input_dir.resolve() if input_dir else project_dir

    console.print(f"\n[bold]Initializing PTM pipeline in:[/bold] {project_dir}")
    if input_dir != project_dir:
        console.print(f"[bold]Discovering DEA folders in:[/bold] {input_dir}")
    console.print()

    # Check if already initialized
    config_file = project_dir / "ptm_config.yaml"
    snakefile = project_dir / "Snakefile"

    if (config_file.exists() or snakefile.exists()) and not force:
        if default:
            console.print("[red]Pipeline files already exist; use --force to overwrite.[/red]")
            return False
        if not Confirm.ask("Pipeline files already exist. Overwrite them?", default=False):
            return False

    # Discover DEA folders
    console.print("[bold]Discovering DEA folders...[/bold]")
    all_folders = find_all_dea_folders(input_dir)

    if not all_folders["phospho"]:
        console.print("[red]Error:[/red] No phospho DEA folder found")
        console.print("  Expected patterns: DEA_*_WUphospho_*, DEA_*_WUcombined_*, DEA_*_*STY*")
        return False

    if not all_folders["protein"]:
        console.print("[red]Error:[/red] No protein DEA folder found (DEA_*_WUprot_* or DEA_*_WUtotal_*)")
        return False

    # Select folders if multiple found
    phospho_dir = _select_folder("phospho", all_folders["phospho"], default)
    protein_dir = _select_folder("protein", all_folders["protein"], default)
    # Optional peptide-level total DEA, carried into the MuData.
    protein_peptide_dir = (
        _select_folder("protein peptide", all_folders["protein_peptide"], default)
        if all_folders["protein_peptide"] else None
    )

    # Show selected folders
    table = Table(title="Selected DEA Folders")
    table.add_column("Type", style="cyan")
    table.add_column("Folder", style="green")
    table.add_row("Phospho", phospho_dir.name)
    table.add_row("Protein", protein_dir.name)
    if protein_peptide_dir is not None:
        table.add_row("Protein peptide", protein_peptide_dir.name)
    console.print(table)

    console.print("\n[bold]Reading DEA AnnData artifacts...[/bold]")
    enriched_h5ad = find_dea_anndata(phospho_dir)
    total_h5ad = find_dea_anndata(protein_dir)
    unresolved: list[str] = []
    for key, artifact in (("enriched_h5ad", enriched_h5ad), ("total_h5ad", total_h5ad)):
        if artifact is None:
            console.print(f"[red]Missing {key}: Results_WU_*/AnnData.h5ad[/red]")
            unresolved.append(key)
        else:
            console.print(f"  {key}: {artifact.relative_to(input_dir)}")
    contrasts = read_dea_contrasts(enriched_h5ad) if enriched_h5ad else []
    if not contrasts:
        unresolved.append("contrasts")
    elif total_h5ad and contrasts != read_dea_contrasts(total_h5ad):
        raise ValueError("Enriched and total DEA artifacts have different contrasts")
    for contrast in contrasts:
        console.print(f"    - {contrast}")
    total_peptide_h5ad = find_dea_anndata(protein_peptide_dir) if protein_peptide_dir else None
    if protein_peptide_dir is not None and total_peptide_h5ad is None:
        console.print("[red]Missing total_peptide_h5ad: Results_WU_*/AnnData.h5ad[/red]")
        unresolved.append("total_peptide_h5ad")
    elif total_peptide_h5ad is not None:
        if contrasts and contrasts != read_dea_contrasts(total_peptide_h5ad):
            raise ValueError("Peptide-level total DEA artifact has different contrasts than the paired DEAs")
        console.print(f"  total_peptide_h5ad: {total_peptide_h5ad.relative_to(input_dir)}")

    # Get experiment name - suggest first contrast as default
    if not name:
        default_name = contrasts[0] if contrasts else get_experiment_name(phospho_dir)
        if default:
            name = default_name
            console.print(f"\n[bold]Experiment name:[/bold] {name}")
        else:
            console.print(f"\n[bold]Suggested experiment name:[/bold] {default_name}")
            name = Prompt.ask("Experiment name", default=default_name)

    # Get significance thresholds
    if default:
        fdr = 0.25
        log2fc = 0.5
    else:
        console.print("\n[bold]Significance thresholds for downstream analyses:[/bold]")
        fdr = float(Prompt.ask("FDR threshold", default="0.25"))
        log2fc = float(Prompt.ask("log2FC threshold", default="0.5"))

    # Analysis options
    if default:
        run_kinase = True
    else:
        console.print("\n[bold]Analysis options:[/bold]")
        run_kinase = Confirm.ask("Run kinase activity analysis?", default=True)

    console.print("\n[bold]B-Fabric upload:[/bold]")
    if default:
        workunit_name = workunit_name or name
        if order_id is None:
            console.print(f"  [yellow]No --order-id; set order_id in {UPLOAD_TARGET_FILE} before uploading[/yellow]")
    else:
        while order_id is None or order_id <= 0:
            if order_id is not None:
                console.print("[red]The order ID must be a positive number[/red]")
            order_id = IntPrompt.ask("B-Fabric order ID")
        workunit_name = workunit_name or Prompt.ask("Workunit name", default=name)
    console.print(f"  Order {order_id}, workunit name {workunit_name}")

    # Generate config
    console.print("\n[bold]Generating configuration...[/bold]")
    config = generate_config(
        phospho_dir=phospho_dir,
        protein_dir=protein_dir,
        enriched_h5ad=enriched_h5ad,
        total_h5ad=total_h5ad,
        contrasts=contrasts,
        output_name=name,
        project_dir=project_dir,
        fdr=fdr,
        log2fc=log2fc,
        run_kinase=run_kinase,
        run_proptm3d=run_proptm3d,
        protein_peptide_dir=protein_peptide_dir,
        total_peptide_h5ad=total_peptide_h5ad,
    )

    if dry_run:
        console.print("\n[yellow]Dry run - ptm_config.yaml would contain:[/yellow]")
        console.print(Panel(config_to_yaml_string(config), title="ptm_config.yaml"))
    else:
        write_config(config, config_file)
        console.print(f"  Written: ptm_config.yaml")
        write_upload_target(project_dir, order_id, workunit_name)
        console.print(f"  Written: {UPLOAD_TARGET_FILE}")

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
    elif unresolved:
        console.print("[yellow]Pipeline initialized, but incomplete.[/yellow]")
        console.print(
            f"\nDiscovery could not fill: {', '.join(unresolved)}"
            f"\nSet them by hand in {config_file}, then run: ptm-pipeline run"
        )
        return False
    else:
        console.print("[green]Pipeline initialized successfully![/green]")
        console.print("\nNext steps:")
        console.print(f"  1. Review ptm_config.yaml")
        console.print("  2. Run: ptm-pipeline run")

    return True
