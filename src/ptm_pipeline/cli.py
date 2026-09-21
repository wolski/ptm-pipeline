"""Three user-facing commands for initializing, running, and cleaning PTM projects."""

import subprocess
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import cyclopts
from rich.console import Console

from .clean import clean_project
from .init import init_project

console = Console()

app = cyclopts.App(
    name="ptm-pipeline",
    help="Initialize, run, and clean a phosphoproteomics PTM analysis.",
    version=version("ptm-pipeline"),
)
init_app = cyclopts.App(
    name="init", help="Create pipeline files from paired DEA results."
)
run_app = cyclopts.App(name="run", help="Run the complete Snakemake pipeline.")
clean_app = cyclopts.App(name="clean", help="Remove outputs or initialization files.")
for group in (init_app, run_app, clean_app):
    app.command(group)


def _initialize(
    input_dir: Path,
    output_dir: Path,
    name: str | None,
    force: bool,
    noninteractive: bool,
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
) -> None:
    """Initialize interactively, prompting for experiment settings."""
    _initialize(input_dir, output_dir, name, force, noninteractive=False)


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
) -> None:
    """Initialize without prompts, using discovered values and defaults."""
    _initialize(input_dir, output_dir, name, force, noninteractive=True)


def _snakemake_command(directory: Path) -> tuple[Path, list[str]]:
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
    # 'all' as another config filename. Put the target before the option.
    return directory, [
        "snakemake",
        "all",
        "-s",
        str(snakefile),
        "--configfile",
        str(config_file),
    ]


def _execute(
    directory: Path, *, cores: int | None = None, flag: str | None = None
) -> None:
    directory, command = _snakemake_command(directory)
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


@run_app.command(name="dry")
def run_dry(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
) -> None:
    """Show the jobs a full run would execute without changing outputs."""
    _execute(directory, flag="--dry-run")


@clean_app.default
def clean(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
) -> None:
    """Remove outputs declared by the Snakemake workflow."""
    _execute(directory, flag="--delete-all-output")


@clean_app.command(name="init")
def clean_init(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
) -> None:
    """Remove files created by initialization, preserving analysis outputs."""
    if not clean_project(directory):
        raise SystemExit(1)


@clean_app.command(name="all")
def clean_all(
    directory: Annotated[
        Path, cyclopts.Parameter(help="Initialized project directory")
    ] = Path("."),
) -> None:
    """Remove workflow outputs, then initialization files."""
    _execute(directory, flag="--delete-all-output")
    if not clean_project(directory):
        raise SystemExit(1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
