"""User-facing commands for initializing, running, updating, cleaning and uploading PTM projects."""

import shutil
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import cyclopts
import yaml
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from . import bfabric_upload
from .clean import clean_project, output_directory
from .config import read_upload_target
from .init import init_project
from .update import install_pushed_commits, refresh_project, rerun_refresh

console = Console()

app = cyclopts.App(
    name="ptm-pipeline",
    help="Initialize, run, clean and upload a phosphoproteomics PTM analysis.",
    version=version("ptm-pipeline"),
)
init_app = cyclopts.App(
    name="init", help="Create pipeline files from paired DEA results."
)
run_app = cyclopts.App(
    name="run", help="Run the pipeline to a chosen depth; each depth writes a zip."
)
clean_app = cyclopts.App(
    name="clean",
    help=(
        "Remove pipeline outputs: the Snakefile's declared outputs, including the DEA zips "
        "and the proptm3d folder and bundle of a full run, and the dir_out tree. Keeps the initialization files "
        "(ptm_config.yaml, bfabric_upload.yaml, Snakefile, helpers.py, ptm.sh), so the project can be rerun. "
        "'clean init' removes only the initialization files, 'clean all' both. "
        "DEA input folders are never removed."
    ),
)
for group in (init_app, run_app, clean_app):
    app.command(group)


def _initialize(
    input_dir: Path,
    output_dir: Path,
    name: str | None,
    force: bool,
    *,
    noninteractive: bool,
    order_id: int | None,
    workunit_name: str | None,
    proptm3d: bool,
) -> None:
    if not input_dir.is_dir():
        console.print(f"[red]Input directory does not exist:[/red] {input_dir}")
        raise SystemExit(1)
    if noninteractive:
        output_dir.mkdir(parents=True, exist_ok=True)
    elif not output_dir.is_dir():
        console.print(f"[red]Output directory does not exist:[/red] {output_dir}")
        raise SystemExit(1)
    success = init_project(
        project_dir=output_dir,
        input_dir=input_dir,
        name=name,
        force=force,
        default=noninteractive,
        order_id=order_id,
        workunit_name=workunit_name,
        run_proptm3d=proptm3d,
    )
    if not success:
        raise SystemExit(1)


@init_app.default
def init(
    input_dir: Annotated[
        Path, cyclopts.Parameter(help="Directory containing DEA folders")
    ] = Path("."),
    output_dir: Annotated[
        Path, cyclopts.Parameter(help="Directory for pipeline files")
    ] = Path("."),
    *,
    name: Annotated[str | None, cyclopts.Parameter(help="Experiment name")] = None,
    force: Annotated[
        bool, cyclopts.Parameter(help="Overwrite an initialized project")
    ] = False,
    order_id: Annotated[
        int | None, cyclopts.Parameter(help="B-Fabric order the results are uploaded to")
    ] = None,
    workunit_name: Annotated[
        str | None,
        cyclopts.Parameter(help="Base workunit name for the uploads [default: experiment name]"),
    ] = None,
    proptm3d: Annotated[
        bool,
        cyclopts.Parameter(help="Prepare and bundle the proptm3d browser; needs 'ptm-pipeline setup ORGANISM' first"),
    ] = True,
) -> None:
    """Initialize interactively, prompting for experiment settings."""
    _initialize(
        input_dir,
        output_dir,
        name,
        force,
        noninteractive=False,
        order_id=order_id,
        workunit_name=workunit_name,
        proptm3d=proptm3d,
    )


@init_app.command(name="default")
def init_default(
    input_dir: Annotated[
        Path, cyclopts.Parameter(help="Directory containing DEA folders")
    ] = Path("."),
    output_dir: Annotated[
        Path, cyclopts.Parameter(help="Directory for pipeline files")
    ] = Path("."),
    *,
    name: Annotated[str | None, cyclopts.Parameter(help="Experiment name")] = None,
    force: Annotated[
        bool, cyclopts.Parameter(help="Overwrite an initialized project")
    ] = False,
    order_id: Annotated[
        int | None, cyclopts.Parameter(help="B-Fabric order the results are uploaded to")
    ] = None,
    workunit_name: Annotated[
        str | None,
        cyclopts.Parameter(help="Base workunit name for the uploads [default: experiment name]"),
    ] = None,
    proptm3d: Annotated[
        bool,
        cyclopts.Parameter(help="Prepare and bundle the proptm3d browser; needs 'ptm-pipeline setup ORGANISM' first"),
    ] = True,
) -> None:
    """Initialize without prompts, using discovered values and defaults."""
    _initialize(
        input_dir,
        output_dir,
        name,
        force,
        noninteractive=True,
        order_id=order_id,
        workunit_name=workunit_name,
        proptm3d=proptm3d,
    )


@app.command
def setup(
    organism: Annotated[
        str, cyclopts.Parameter(help="Organism of the samples: HUMAN or MOUSE")
    ],
) -> None:
    """Download the organism's AlphaFold structures and precompute their structural context,
    which the proptm3d step of a full run reads. Once per machine; under ptm-pipeline.sh, the
    cache is kept in .cache/ of the current folder."""
    executable = shutil.which("proptm3d")
    if executable is None:
        console.print("[red]proptm3d is not installed; reinstall ptm-pipeline.[/red]")
        raise SystemExit(1)
    command = [executable, "cache", "context", organism]
    console.print(f"[dim]$ {' '.join(command)}[/dim]")
    result = subprocess.run(command, check=False)
    if result.returncode:
        raise SystemExit(result.returncode)


def _snakemake_command(directory: Path, target: str) -> tuple[Path, list[str]]:
    directory = directory.resolve()
    if not directory.is_dir():
        console.print(f"[red]Project directory does not exist:[/red] {directory}")
        raise SystemExit(1)
    snakefile = directory / "Snakefile"
    config_file = directory / "ptm_config.yaml"
    for path in (snakefile, config_file):
        if not path.is_file():
            console.print(f"[red]Missing pipeline file:[/red] {path}")
            console.print(
                "Run 'ptm-pipeline init' or 'ptm-pipeline init default' first."
            )
            raise SystemExit(1)
    # Snakemake accepts multiple --configfile values and would treat a trailing
    # target as another config filename. Put the target before the option.
    return directory, [
        "snakemake",
        target,
        "-s",
        str(snakefile),
        "--configfile",
        str(config_file),
    ]


def _execute(
    directory: Path,
    *,
    cores: int | None = None,
    flag: str | None = None,
    target: str = "all",
) -> None:
    directory, command = _snakemake_command(directory, target)
    if cores is not None:
        if cores < 1:
            console.print("[red]--cores must be a positive integer.[/red]")
            raise SystemExit(1)
        command.extend(("--cores", str(cores)))
    if flag is not None:
        command.append(flag)
    console.print(f"[bold]PTM pipeline:[/bold] {directory}")
    console.print(f"[dim]$ {' '.join(command)}[/dim]")
    try:
        result = subprocess.run(command, cwd=directory, check=False)
    except FileNotFoundError:
        console.print("[red]Snakemake is not installed or not on PATH.[/red]")
        raise SystemExit(1) from None
    if result.returncode:
        raise SystemExit(result.returncode)


@run_app.default
def run(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
    *,
    cores: Annotated[
        int, cyclopts.Parameter(name=["--cores", "-j"], help="Parallel cores")
    ] = 1,
) -> None:
    """Run the complete pipeline through the final reports and exports."""
    _execute(directory, cores=cores)


@run_app.command(name="stats")
def run_stats(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
    *,
    cores: Annotated[
        int, cyclopts.Parameter(name=["--cores", "-j"], help="Parallel cores")
    ] = 1,
) -> None:
    """Run through the statistics stage only, then archive it."""
    _execute(directory, cores=cores, target="stats")


@run_app.command(name="gsea")
def run_gsea(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
    *,
    cores: Annotated[
        int, cyclopts.Parameter(name=["--cores", "-j"], help="Parallel cores")
    ] = 1,
) -> None:
    """Run through the enrichment stages and the final MuData, without reports."""
    _execute(directory, cores=cores, target="gsea")


@run_app.command(name="dry")
def run_dry(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
    *,
    target: Annotated[
        str, cyclopts.Parameter(help="Target to plan: all, stats or gsea")
    ] = "all",
) -> None:
    """Show the jobs a run would execute without changing outputs."""
    _execute(directory, flag="--dry-run", target=target)


@app.command
def update(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
    *,
    install: Annotated[
        bool,
        cyclopts.Parameter(help="Install the pushed commits before refreshing the project"),
    ] = True,
) -> None:
    """Install the pushed commits of ptm-pipeline and its R packages, refresh the project's
    Snakefile, helpers.py and ptm.sh, and show the jobs a run would execute."""
    _snakemake_command(directory, "all")
    if install:
        install_pushed_commits()
        rerun_refresh(directory)
        return
    refresh_project(directory.resolve())
    _execute(directory, flag="--dry-run")


@clean_app.default
def clean(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
) -> None:
    """Remove declared outputs and the configured pipeline output tree."""
    _clean_outputs(directory)


@clean_app.command(name="init")
def clean_init(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
) -> None:
    """Remove only the initialization files (ptm_config.yaml, bfabric_upload.yaml, Snakefile, helpers.py, ptm.sh); keep outputs."""
    if not clean_project(directory):
        raise SystemExit(1)


@clean_app.command(name="all")
def clean_all(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
) -> None:
    """Remove pipeline outputs, then the initialization files."""
    _clean_outputs(directory)
    if not clean_project(directory):
        raise SystemExit(1)


def _clean_outputs(directory: Path) -> None:
    try:
        output = output_directory(directory)
    except (OSError, TypeError, ValueError, yaml.YAMLError) as error:
        console.print(f"[red]Cannot clean pipeline outputs:[/red] {error}")
        raise SystemExit(1) from None
    _execute(directory, flag="--delete-all-output")
    if output.is_dir():
        shutil.rmtree(output)
        console.print(f"Removed pipeline output directory: {output}")


@dataclass(slots=True)
class _TerminalUploadProgress:
    """Render bfabricPy transfer callbacks as persistent terminal progress bars."""

    progress: Progress
    tasks: dict[str, TaskID] = field(default_factory=dict)
    totals: dict[str, int] = field(default_factory=dict)

    def on_start(self, total_files: int, total_bytes: int) -> None:
        """Report size after bfabricPy finishes setup and duplicate checks."""
        noun = "file" if total_files == 1 else "files"
        self.progress.console.print(
            f"Starting transfer: {total_files} {noun}, {total_bytes / 1024**2:.1f} MiB"
        )

    def on_progress(self, filename: str, bytes_done: int, total: int) -> None:
        """Update the progress bar for one transferred file."""
        task_id = self.tasks.get(filename)
        if task_id is None:
            task_id = self.progress.add_task(filename, total=total)
            self.tasks[filename] = task_id
        self.totals[filename] = total
        self.progress.update(task_id, completed=bytes_done, total=total)

    def on_file_done(self, filename: str, success: bool) -> None:
        """Mark one transfer as finished while retaining its final bar."""
        task_id = self.tasks.get(filename)
        if task_id is None:
            task_id = self.progress.add_task(filename, total=1)
            self.tasks[filename] = task_id
        mark = "[green]✓[/]" if success else "[red]✗[/]"
        if success:
            self.progress.update(
                task_id,
                completed=self.totals.get(filename, 1),
                description=f"{mark} {filename}",
                refresh=True,
            )
        else:
            self.progress.update(task_id, description=f"{mark} {filename}", refresh=True)


@contextmanager
def _upload_progress() -> Iterator[bfabric_upload.UploadProgressCallbacks | None]:
    """Provide live upload callbacks only for an interactive terminal."""
    if not sys.stderr.isatty():
        yield None
        return
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=Console(file=sys.stderr),
    )
    reporter = _TerminalUploadProgress(progress)
    with progress:
        yield bfabric_upload.UploadProgressCallbacks(
            on_start=reporter.on_start,
            on_progress=reporter.on_progress,
            on_file_done=reporter.on_file_done,
        )


@app.command
def upload(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
) -> None:
    """Upload a full run's archives to the project's B-Fabric order, one workunit each.

    The order ID and base workunit name come from bfabric_upload.yaml, written
    by init. Workunit names are the base name prefixed per archive:
    ptm_pipeline (PTM results, application 431), proptm3d (bundle, 434),
    DEA_enriched, DEA_total and DEA_total_peptide (DEA zips, 438). Every archive
    is validated and every connection opened before the first workunit is created.
    """
    try:
        order_id, base_name = read_upload_target(directory.resolve())
        artifacts = bfabric_upload.project_artifacts(directory)
        for artifact in artifacts:
            artifact.validate()
        console.print(f"B-Fabric order {order_id}; archives and workunit names:")
        for artifact in artifacts:
            size = artifact.path.stat().st_size / 1024**2
            console.print(
                f"  {artifact.workunit_name(base_name)} -> application {artifact.application_id} "
                f"({artifact.application_name})"
            )
            console.print(f"    {artifact.path.resolve()} ({size:.1f} MiB)")
        answer = input(f"Upload as {len(artifacts)} separate workunits? [y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            console.print("Upload cancelled.")
            return
        with _upload_progress() as progress:
            receipts = bfabric_upload.upload_artifacts(
                artifacts, order_id, base_name, progress=progress
            )
    except (OSError, KeyError, ValueError, RuntimeError, yaml.YAMLError) as error:
        console.print(f"[red]{error}[/red]")
        raise SystemExit(2) from None
    for receipt in receipts:
        uploaded = receipt.summary.uploads[0]
        console.print(
            f"Uploaded {uploaded.filename} as {receipt.workunit_name}: "
            f"workunit {receipt.summary.workunit_id}, resource {uploaded.resource_id}"
        )
    console.print("B-Fabric now performs its server-side storage checks.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
