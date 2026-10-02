"""Upload a project's PTM delivery, proptm3d bundle and DEA zips to their B-Fabric applications."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar
from zipfile import BadZipFile, ZipFile

import yaml
from bfabric import Bfabric
from bfabric.operations.workunit import (
    FileDoneCallback,
    FileProgressCallback,
    UploadFileParam,
    UploadFilesParams,
    UploadStartCallback,
    UploadSummary,
    upload_files,
)
from proptm3d.bundle import validate_bundle

PTM_PIPELINE_APPLICATION_ID = 431
PROPTM3D_APPLICATION_ID = 434
DEA_APPLICATION_ID = 438
BFABRIC_CONFIG_ENVIRONMENT = "app-431-ptm-pipeline"


class UploadError(RuntimeError):
    """A transfer that returned without the expected successful upload."""


class UploadConfigurationError(RuntimeError):
    """A required saved B-Fabric application environment is unavailable."""


@dataclass(frozen=True, slots=True)
class UploadArtifact(ABC):
    """One archive, the B-Fabric application receiving it and its workunit-name prefix."""

    path: Path

    application_id: ClassVar[int]
    application_name: ClassVar[str]
    workunit_prefix: ClassVar[str]
    config_environment: ClassVar[str] = BFABRIC_CONFIG_ENVIRONMENT

    @abstractmethod
    def validate_contents(self, path: Path) -> None:
        """Raise if the resolved ZIP is not what this application expects."""

    def validate(self) -> Path:
        """Validate the archive and return its resolved path."""
        resolved = self.path.resolve()
        if not resolved.is_file():
            msg = f"{self.workunit_prefix} archive not found: {resolved}"
            raise FileNotFoundError(msg)
        if resolved.suffix.lower() != ".zip":
            msg = f"{self.workunit_prefix} archive must be a ZIP: {resolved}"
            raise ValueError(msg)
        self.validate_contents(resolved)
        return resolved

    def workunit_name(self, base_name: str) -> str:
        """The workunit name this archive is uploaded under."""
        return f"{self.workunit_prefix}_{base_name}"


@dataclass(frozen=True, slots=True)
class PtmPipelineArtifact(UploadArtifact):
    """The completed PTM Pipeline delivery, uploaded through application 431."""

    application_id: ClassVar[int] = PTM_PIPELINE_APPLICATION_ID
    application_name: ClassVar[str] = "PTM Pipeline"
    workunit_prefix: ClassVar[str] = "ptm_pipeline"

    def validate_contents(self, path: Path) -> None:
        """Require exactly one completed PTM results MuData file."""
        results = [name for name in _members(path) if Path(name).name == "PTM_results.h5mu"]
        if len(results) != 1:
            msg = f"Expected exactly one PTM_results.h5mu in {path}; found {len(results)}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class Proptm3dArtifact(UploadArtifact):
    """The portable proptm3d browser bundle, uploaded through application 434."""

    application_id: ClassVar[int] = PROPTM3D_APPLICATION_ID
    application_name: ClassVar[str] = "proptm3d"
    workunit_prefix: ClassVar[str] = "proptm3d"

    def validate_contents(self, path: Path) -> None:
        """Require a valid portable proptm3d bundle."""
        validate_bundle(path)


@dataclass(frozen=True, slots=True)
class DeaArtifact(UploadArtifact):
    """A prolfquapp DEA archive the PTM analysis used, uploaded through application 438."""

    application_id: ClassVar[int] = DEA_APPLICATION_ID
    application_name: ClassVar[str] = "DEA"

    def validate_contents(self, path: Path) -> None:
        """Require the DEA's AnnData result."""
        if not any(Path(name).name == "AnnData.h5ad" for name in _members(path)):
            msg = f"Expected a Results_WU_*/AnnData.h5ad in DEA archive {path}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class EnrichedDeaArtifact(DeaArtifact):
    """The phospho-site DEA of the enriched samples."""

    workunit_prefix: ClassVar[str] = "DEA_enriched"


@dataclass(frozen=True, slots=True)
class TotalDeaArtifact(DeaArtifact):
    """The protein-level DEA of the total proteome."""

    workunit_prefix: ClassVar[str] = "DEA_total"


@dataclass(frozen=True, slots=True)
class TotalPeptideDeaArtifact(DeaArtifact):
    """The peptide-level DEA of the total proteome."""

    workunit_prefix: ClassVar[str] = "DEA_total_peptide"


DEA_ARTIFACTS: dict[str, type[DeaArtifact]] = {
    "phospho_dea_dir": EnrichedDeaArtifact,
    "protein_dea_dir": TotalDeaArtifact,
    "protein_peptide_dea_dir": TotalPeptideDeaArtifact,
}


@dataclass(frozen=True, slots=True)
class UploadReceipt:
    """A completed upload together with the archive and workunit name it was made for."""

    artifact: UploadArtifact
    workunit_name: str
    summary: UploadSummary


@dataclass(frozen=True, slots=True)
class UploadProgressCallbacks:
    """Optional bfabricPy callbacks used to display transfer progress."""

    on_start: UploadStartCallback
    on_progress: FileProgressCallback
    on_file_done: FileDoneCallback


def project_artifacts(directory: Path) -> tuple[UploadArtifact, ...]:
    """The archives a full run of an initialized project writes, named as its Snakefile names them."""
    directory = directory.resolve()
    config = yaml.safe_load((directory / "ptm_config.yaml").read_text())
    dir_out = config["dir_out"]
    dea = tuple(
        artifact(directory / f"{Path(config[key]).name}.zip")
        for key, artifact in DEA_ARTIFACTS.items()
        if config.get(key)
    )
    browser = (
        (Proptm3dArtifact(directory / f"proptm3d_{dir_out}-all.zip"),)
        if config.get("run_proptm3d", True)
        else ()
    )
    return (PtmPipelineArtifact(directory / f"{dir_out}.zip"), *browser, *dea)


def _members(path: Path) -> list[str]:
    try:
        with ZipFile(path) as archive:
            return [member.filename for member in archive.infolist() if not member.is_dir()]
    except BadZipFile as error:
        msg = f"Invalid ZIP: {path}"
        raise ValueError(msg) from error


def _validate_target(order_id: int, base_name: str) -> None:
    if order_id <= 0:
        msg = "B-Fabric order ID must be a positive integer"
        raise ValueError(msg)
    if not base_name.strip():
        msg = "B-Fabric workunit name must not be empty"
        raise ValueError(msg)


def _upload(
    artifact: UploadArtifact,
    path: Path,
    client: Bfabric,
    order_id: int,
    workunit_name: str,
    progress: UploadProgressCallbacks | None,
) -> UploadSummary:
    summary = upload_files(
        client=client,
        params=UploadFilesParams(
            files=[UploadFileParam(path=path)],
            container_id=order_id,
            application_id=artifact.application_id,
            workunit_name=workunit_name,
        ),
        on_start=progress.on_start if progress else None,
        on_progress=progress.on_progress if progress else None,
        on_file_done=progress.on_file_done if progress else None,
    )
    if summary.workunit_id is None:
        msg = f"B-Fabric did not create workunit {workunit_name!r}"
        raise UploadError(msg)
    if summary.failures:
        failures = "; ".join(f"{failure.filename}: {failure.error}" for failure in summary.failures)
        msg = f"B-Fabric workunit {summary.workunit_id} was created, but upload failed: {failures}"
        raise UploadError(msg)
    if len(summary.uploads) != 1:
        msg = f"B-Fabric workunit {summary.workunit_id} did not report the transfer of {path.name}"
        raise UploadError(msg)
    return summary


def _connect(artifact: UploadArtifact) -> Bfabric:
    try:
        return Bfabric.connect(config_file_env=artifact.config_environment)
    except KeyError as error:
        msg = (
            f"Missing B-Fabric credentials environment {artifact.config_environment!r} "
            f"for application {artifact.application_id} ({artifact.application_name})"
        )
        raise UploadConfigurationError(msg) from error


def upload_artifacts(
    artifacts: tuple[UploadArtifact, ...],
    order_id: int,
    base_name: str,
    *,
    progress: UploadProgressCallbacks | None = None,
) -> list[UploadReceipt]:
    """Validate every archive, then connect every target, before creating any B-Fabric workunit."""
    _validate_target(order_id, base_name)
    paths = [artifact.validate() for artifact in artifacts]
    clients = [_connect(artifact) for artifact in artifacts]
    receipts = []
    for artifact, path, client in zip(artifacts, paths, clients, strict=True):
        name = artifact.workunit_name(base_name)
        summary = _upload(artifact, path, client, order_id, name, progress)
        receipts.append(UploadReceipt(artifact, name, summary))
    return receipts
