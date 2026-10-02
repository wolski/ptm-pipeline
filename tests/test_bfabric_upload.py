"""Tests for uploading a project's PTM delivery, proptm3d bundle and DEA zips to B-Fabric."""

import json
import stat
from zipfile import ZipFile, ZipInfo

import pytest
import yaml
from bfabric.operations.workunit import FileFailure, FileUpload, UploadSummary

from ptm_pipeline import bfabric_upload, cli
from ptm_pipeline.config import read_upload_target, write_upload_target

DEA_DIRS = {
    "phospho_dea_dir": "DEA_X_WUphospho_site_vsn",
    "protein_dea_dir": "DEA_X_WUtotal_prot_vsn",
    "protein_peptide_dea_dir": "DEA_X_WUtotal_peptide_vsn",
}
WORKUNIT_NAMES = [
    "ptm_pipeline_PKD1_vs_WT",
    "proptm3d_PKD1_vs_WT",
    "DEA_enriched_PKD1_vs_WT",
    "DEA_total_PKD1_vs_WT",
    "DEA_total_peptide_PKD1_vs_WT",
]


def _write(archive, name, contents):
    entry = ZipInfo(name)
    entry.external_attr = (stat.S_IFREG | 0o644) << 16
    archive.writestr(entry, contents)


def _bundle(path):
    with ZipFile(path, "w") as archive:
        manifest = {"kind": "proptm3d-static-bundle", "schema_version": "1", "layout": "single", "methods": ["DPA"]}
        _write(archive, "bundle.json", json.dumps(manifest))
        _write(archive, "index.html", "<ptm-browser-app></ptm-browser-app>")
        _write(archive, "data/run.json", "{}")
    return path


def _zip(path, member):
    with ZipFile(path, "w") as archive:
        _write(archive, member, b"contents")
    return path


@pytest.fixture
def project(tmp_path):
    config = {"dir_out": "PTM_X", **DEA_DIRS}
    (tmp_path / "ptm_config.yaml").write_text(yaml.safe_dump(config))
    write_upload_target(tmp_path, 123, "PKD1_vs_WT")
    _zip(tmp_path / "PTM_X.zip", "PTM_X/PTM_results.h5mu")
    _bundle(tmp_path / "proptm3d_PTM_X-all.zip")
    for directory in DEA_DIRS.values():
        _zip(tmp_path / f"{directory}.zip", f"{directory}/Results_WU_x/AnnData.h5ad")
    return tmp_path


def _summary(params, workunit_id):
    path = params.files[0].path
    return UploadSummary(
        workunit_id=workunit_id,
        uploads=[FileUpload(filename=path.name, resource_id=700 + workunit_id, storage_path=path.name)],
    )


def test_project_artifacts_follow_the_snakefile_names(project):
    artifacts = bfabric_upload.project_artifacts(project)

    assert [artifact.path.name for artifact in artifacts] == [
        "PTM_X.zip",
        "proptm3d_PTM_X-all.zip",
        "DEA_X_WUphospho_site_vsn.zip",
        "DEA_X_WUtotal_prot_vsn.zip",
        "DEA_X_WUtotal_peptide_vsn.zip",
    ]
    assert [artifact.workunit_name("PKD1_vs_WT") for artifact in artifacts] == WORKUNIT_NAMES


def test_project_artifacts_skip_an_unconfigured_peptide_dea(project):
    config = yaml.safe_load((project / "ptm_config.yaml").read_text())
    del config["protein_peptide_dea_dir"]
    (project / "ptm_config.yaml").write_text(yaml.safe_dump(config))

    names = [artifact.workunit_prefix for artifact in bfabric_upload.project_artifacts(project)]

    assert names == ["ptm_pipeline", "proptm3d", "DEA_enriched", "DEA_total"]


def test_project_artifacts_skip_the_bundle_when_proptm3d_is_off(project):
    config = yaml.safe_load((project / "ptm_config.yaml").read_text())
    (project / "ptm_config.yaml").write_text(yaml.safe_dump({**config, "run_proptm3d": False}))

    names = [artifact.workunit_prefix for artifact in bfabric_upload.project_artifacts(project)]

    assert "proptm3d" not in names and names[0] == "ptm_pipeline"


def test_upload_creates_one_named_workunit_per_archive(project, monkeypatch):
    connections = []
    calls = []
    monkeypatch.setattr(
        bfabric_upload.Bfabric, "connect", lambda **kwargs: connections.append(kwargs) or object()
    )

    def fake_upload_files(*, client, params, **_callbacks):
        calls.append(params)
        return _summary(params, 450 + len(calls))

    monkeypatch.setattr(bfabric_upload, "upload_files", fake_upload_files)

    receipts = bfabric_upload.upload_artifacts(
        bfabric_upload.project_artifacts(project), 123, "PKD1_vs_WT"
    )

    assert connections == [{"config_file_env": "app-431-ptm-pipeline"}] * 5
    assert [params.application_id for params in calls] == [431, 434, 438, 438, 438]
    assert [params.workunit_name for params in calls] == WORKUNIT_NAMES
    assert all(params.container_id == 123 and len(params.files) == 1 for params in calls)
    assert [receipt.workunit_name for receipt in receipts] == WORKUNIT_NAMES


def test_upload_validates_every_archive_before_connecting(project, monkeypatch):
    _zip(project / "DEA_X_WUtotal_prot_vsn.zip", "notes.txt")
    monkeypatch.setattr(
        bfabric_upload.Bfabric,
        "connect",
        lambda **_kwargs: pytest.fail("invalid archives must not connect to B-Fabric"),
    )

    with pytest.raises(ValueError, match="AnnData.h5ad"):
        bfabric_upload.upload_artifacts(bfabric_upload.project_artifacts(project), 123, "x")


def test_upload_reports_a_missing_archive(project):
    (project / "proptm3d_PTM_X-all.zip").unlink()

    with pytest.raises(FileNotFoundError, match="proptm3d archive not found"):
        bfabric_upload.upload_artifacts(bfabric_upload.project_artifacts(project), 123, "x")


def test_upload_connects_every_application_before_creating_workunits(project, monkeypatch):
    connections = []

    def connect(**kwargs):
        connections.append(kwargs)
        if len(connections) == 3:
            raise KeyError("app-431-ptm-pipeline")
        return object()

    monkeypatch.setattr(bfabric_upload.Bfabric, "connect", connect)
    monkeypatch.setattr(
        bfabric_upload,
        "upload_files",
        lambda **_kwargs: pytest.fail("no workunit may be created after a failed preflight"),
    )

    with pytest.raises(bfabric_upload.UploadConfigurationError, match="438"):
        bfabric_upload.upload_artifacts(bfabric_upload.project_artifacts(project), 123, "x")


@pytest.mark.parametrize(
    ("order_id", "base_name", "error"),
    [(0, "x", "positive integer"), (123, "  ", "must not be empty")],
)
def test_upload_validates_target_before_connecting(project, monkeypatch, order_id, base_name, error):
    monkeypatch.setattr(
        bfabric_upload.Bfabric,
        "connect",
        lambda **_kwargs: pytest.fail("invalid input must not connect to B-Fabric"),
    )

    with pytest.raises(ValueError, match=error):
        bfabric_upload.upload_artifacts(bfabric_upload.project_artifacts(project), order_id, base_name)


def test_upload_reports_a_created_but_failed_workunit(project, monkeypatch):
    monkeypatch.setattr(bfabric_upload.Bfabric, "connect", lambda **_kwargs: object())
    monkeypatch.setattr(
        bfabric_upload,
        "upload_files",
        lambda **_kwargs: UploadSummary(
            workunit_id=456,
            failures=[FileFailure(filename="PTM_X.zip", resource_id=789, error="transfer stopped")],
        ),
    )

    with pytest.raises(bfabric_upload.UploadError, match=r"workunit 456.*transfer stopped"):
        bfabric_upload.upload_artifacts(bfabric_upload.project_artifacts(project), 123, "x")


@pytest.mark.parametrize(
    ("target", "error"),
    [
        ({"order_id": None, "workunit_name": "x"}, "positive B-Fabric order ID"),
        ({"order_id": 123, "workunit_name": ""}, "must not be empty"),
    ],
)
def test_read_upload_target_rejects_an_incomplete_target(tmp_path, target, error):
    (tmp_path / "bfabric_upload.yaml").write_text(yaml.safe_dump(target))

    with pytest.raises(ValueError, match=error):
        read_upload_target(tmp_path)


def test_read_upload_target_names_the_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="bfabric_upload.yaml"):
        read_upload_target(tmp_path)


@pytest.mark.parametrize(("answer", "uploads"), [("y", 1), ("n", 0)])
def test_cli_upload_lists_workunit_names_and_asks_before_uploading(
    project, monkeypatch, capsys, answer, uploads
):
    calls = []

    def upload_artifacts(artifacts, order_id, base_name, *, progress):
        calls.append((order_id, base_name))
        return [
            bfabric_upload.UploadReceipt(
                artifact,
                artifact.workunit_name(base_name),
                UploadSummary(
                    workunit_id=450 + index,
                    uploads=[FileUpload(filename=artifact.path.name, resource_id=1, storage_path="x")],
                ),
            )
            for index, artifact in enumerate(artifacts)
        ]

    monkeypatch.setattr(cli.bfabric_upload, "upload_artifacts", upload_artifacts)
    monkeypatch.setattr("builtins.input", lambda _prompt: answer)

    cli.upload(project)

    output = capsys.readouterr().out
    assert "B-Fabric order 123" in output
    assert "DEA_total_peptide_PKD1_vs_WT -> application 438" in output
    assert len(calls) == uploads
    if uploads:
        assert calls == [(123, "PKD1_vs_WT")]
        assert "as DEA_enriched_PKD1_vs_WT: workunit 452" in output
    else:
        assert "Upload cancelled." in output


def test_cli_upload_reports_invalid_archives_without_traceback(project, capsys):
    (project / "PTM_X.zip").unlink()

    with pytest.raises(SystemExit) as error:
        cli.upload(project)

    assert error.value.code == 2
    assert "ptm_pipeline archive not found" in capsys.readouterr().out
