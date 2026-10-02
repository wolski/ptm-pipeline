"""Helper functions for the Snakefile: prophosqua's installed files, the
pipeline version and the results archives."""

import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile


def pipeline_version() -> str:
    """Version of the ptm-pipeline tool on PATH, as rendered into the landing page."""
    executable = shutil.which("ptm-pipeline")
    if executable is None:
        return "unknown"
    result = subprocess.run([executable, "--version"], capture_output=True, text=True, check=False)
    return result.stdout.strip() or "unknown"


def create_results_archive(folder: str, output: str, members: list[str]) -> None:
    """Package only declared final outputs, excluding stale legacy reports."""
    root = Path(folder).resolve()
    destination = Path(output)
    temporary = destination.with_name(destination.name + ".tmp")
    try:
        with ZipFile(temporary, "w", allowZip64=True) as archive:
            for member in sorted(set(members)):
                path = Path(member).resolve()
                relative = path.relative_to(root)
                if not path.is_file():
                    raise FileNotFoundError(path)
                compression = ZIP_STORED if path.suffix in (".h5mu", ".gz") else ZIP_DEFLATED
                archive.write(path, arcname=str(Path(root.name) / relative), compress_type=compression)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def get_kinase_files() -> tuple[str, list[str]]:
    """Resolve the installed adapter and the source files its calculations use."""
    executable = shutil.which("ptm-kinase")
    if executable is None:
        raise ValueError("ptm-kinase is missing; install the current ptm-pipeline package")
    result = subprocess.run([executable, "dependencies"], capture_output=True, text=True, check=True)
    return executable, result.stdout.splitlines()


def get_proptm3d() -> str:
    """Resolve the proptm3d command installed with ptm-pipeline."""
    executable = shutil.which("proptm3d")
    if executable is None:
        raise ValueError("proptm3d is missing; install the current ptm-pipeline package")
    return executable


def get_prophosqua_file(relpath: str) -> str:
    """Resolve a file shipped under prophosqua's inst/application.

    Every R script, report template and shell wrapper this pipeline runs lives
    in the installed package, not in the project. Resolving them here, at parse
    time, lets a rule declare the exact file it runs, and fails the parse rather
    than a rule halfway through a run when the package is missing or too old.
    Invalidation on reinstall comes from get_prophosqua_install_stamp().

    Args:
        relpath: Path below inst/application, e.g. "CMD_RENDER.R" or
            "bin/ptm.sh"

    Returns:
        Full path to the installed file

    Raises:
        ValueError: If the file is not found in the installed prophosqua
    """
    cmd = [
        'Rscript', '--vanilla', '-e',
        f'cat(system.file("application", "{relpath}", package = "prophosqua"))'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    path = result.stdout.strip()
    if not path or not os.path.exists(path):
        raise ValueError(
            f"prophosqua application file not found: {relpath}. "
            "Is prophosqua installed and up to date?"
        )
    return path


@lru_cache(maxsize=None)
def get_prophosqua_report(name: str) -> str:
    """Resolve one of prophosqua's report templates.

    Where a template lives is the package's business, not the pipeline's: the
    analysis QMDs are prophosqua's vignettes and install into its `doc/`.
    Asking `prophosqua::report_file()` keeps that rule in the package.

    Args:
        name: Template file name, e.g. "ptm_statistics.qmd"

    Returns:
        Full path to the installed template

    Raises:
        ValueError: If the package cannot resolve it -- which is also what
            happens when prophosqua was installed without its vignettes built.
    """
    cmd = [
        'Rscript', '--vanilla', '-e',
        f'cat(prophosqua::report_file("{name}"))'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    path = result.stdout.strip()
    if not path or not os.path.exists(path):
        raise ValueError(
            f"prophosqua report template not found: {name}. "
            f"{result.stderr.strip()}"
        )
    return path


def get_prophosqua_install_stamp() -> str:
    """Resolve a file of the installed prophosqua that every reinstall rewrites.

    A rule declares the wrapper it calls and the script or template that wrapper
    reaches, but the script's real work happens in the package's R code, which
    is not any of those files. Without this, editing a prophosqua function and
    reinstalling would leave every rule looking up to date -- the exact blindness
    that makes "I reinstalled prophosqua and the figure is still wrong" happen.

    Meta/package.rds is rewritten by every `R CMD INSTALL`, so declaring it makes
    a reinstall invalidate every rule that runs R. That is coarse on purpose: a
    reinstall can change any function any rule reaches, and there is no cheaper
    declaration that is still true.

    Returns:
        Full path to the installed package's Meta/package.rds

    Raises:
        ValueError: If prophosqua is not installed
    """
    cmd = [
        'Rscript', '--vanilla', '-e',
        'cat(system.file("Meta", "package.rds", package = "prophosqua"))'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    path = result.stdout.strip()
    if not path or not os.path.exists(path):
        raise ValueError(
            "prophosqua is not installed, or its installation is incomplete. "
            "Install it with: make -C <prophosqua checkout> install"
        )
    return path
