"""Install the pushed commits of the pipeline and refresh a project's copies of its files."""

import shutil
import subprocess
from pathlib import Path

from rich.console import Console

from .init import copy_template_files

console = Console()

REPOSITORY = "git+https://github.com/wolski/ptm-pipeline"
R_UPDATE = Path(__file__).with_name("update_r_packages.R")


def _run(command: list[str], what: str) -> None:
    console.print(f"[bold]{what}[/bold]")
    console.print(f"[dim]$ {' '.join(command)}[/dim]")
    try:
        result = subprocess.run(command, check=False)
    except FileNotFoundError:
        console.print(f"[red]{command[0]} is not installed or not on PATH.[/red]")
        raise SystemExit(1) from None
    if result.returncode:
        raise SystemExit(result.returncode)


def install_pushed_commits() -> None:
    """Install prolfqua, prolfquapp, protsea, prophosqua and ptm-pipeline from GitHub."""
    _run(["Rscript", "--vanilla", str(R_UPDATE)], "Installing the R packages from GitHub")
    _run(["uv", "tool", "install", "--reinstall", REPOSITORY], "Installing ptm-pipeline from GitHub")


def refresh_project(directory: Path) -> None:
    """Replace the project's copies of the pipeline files; ptm_config.yaml is kept."""
    copied = copy_template_files(directory)
    console.print(f"[bold]Refreshed in {directory}:[/bold] {', '.join(copied)}")


def rerun_refresh(directory: Path) -> None:
    """Refresh the project with the newly installed tool, so its files and copy rules apply."""
    executable = shutil.which("ptm-pipeline")
    if executable is None:
        console.print("[red]ptm-pipeline is not on PATH after the install.[/red]")
        raise SystemExit(1)
    _run([executable, "update", str(directory), "--no-install"], "Refreshing the project")
