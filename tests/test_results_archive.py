import importlib.util
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "template"


def load_helpers():
    spec = importlib.util.spec_from_file_location("pipeline_helpers", TEMPLATE_DIR / "helpers.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fgcz_quarto_available() -> bool:
    if shutil.which("Rscript") is None or shutil.which("quarto") is None:
        return False
    check = subprocess.run(
        ["Rscript", "-e", "quit(status = !requireNamespace('fgczQuartoTemplate', quietly = TRUE))"],
        capture_output=True,
    )
    return check.returncode == 0


def test_results_archive_contains_only_declared_final_outputs(tmp_path):
    module = load_helpers()

    folder = tmp_path / "PTM_output"
    for relative in (
        "PTM_results.h5mu",
        "PTM_inputs.h5mu",
        "PTM_statistics.h5mu",
        "PTM_DPA/result_ptm_sea.cbor.gz",
        "PTM_DPA/Analysis_DPA_DPU.html",
        "ptm_statistics.html",
        "PTM_DPA/ptm_enrichment.html",
        "PTM_DPU/ptm_enrichment.html",
        "PTM_CF_DPU/ptm_enrichment.html",
        "PTM_results.xlsx",
    ):
        path = folder / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative)
    reports = [str(folder / "ptm_statistics.html")] + [
        str(folder / analysis / "ptm_enrichment.html")
        for analysis in ("PTM_DPA", "PTM_DPU", "PTM_CF_DPU")
    ]
    index = folder / "index.html"
    index.write_text("<html>ptm_statistics.html PTM_DPA/ptm_enrichment.html</html>")
    archive_path = tmp_path / "results.zip"
    module.create_results_archive(
        str(folder), str(archive_path),
        [str(folder / "PTM_results.h5mu"), str(folder / "PTM_results.xlsx"), str(index)] + reports,
    )

    with ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == {
            "PTM_output/PTM_results.h5mu",
            "PTM_output/PTM_results.xlsx",
            "PTM_output/index.html",
            "PTM_output/ptm_statistics.html",
            "PTM_output/PTM_DPA/ptm_enrichment.html",
            "PTM_output/PTM_DPU/ptm_enrichment.html",
            "PTM_output/PTM_CF_DPU/ptm_enrichment.html",
        }


@pytest.mark.skipif(not fgcz_quarto_available(), reason="needs Rscript, quarto and fgczQuartoTemplate")
def test_report_index_links_every_report_and_result_file(tmp_path):
    module = load_helpers()
    config = tmp_path / "ptm_config.yaml"
    config.write_text(
        "dir_out: PTM_output\n"
        "run_kinase: true\n"
        "fdr: 0.05\n"
        "log2fc: 0.5\n"
        "phospho_dea_dir: DEA_phospho\n"
        "protein_dea_dir: DEA_total\n"
        "contrasts: [KO_vs_WT]\n"
        "analyses:\n"
        "  dpa: {sheet: DPA, subdir: PTM_DPA}\n"
        "  dpu: {sheet: DPU, subdir: PTM_DPU}\n"
        "  cf: {sheet: CF, subdir: PTM_CF_DPU}\n"
    )
    index = tmp_path / "PTM_output" / "index.html"
    module.render_report_index(
        str(index),
        str(config),
        [str(TEMPLATE_DIR / "index.qmd"), str(TEMPLATE_DIR / "ptm-pipeline-overview.svg")],
    )
    page = index.read_text()
    for href in (
        "ptm_statistics.html",
        "PTM_DPA/ptm_enrichment.html",
        "PTM_DPU/ptm_enrichment.html",
        "PTM_CF_DPU/ptm_enrichment.html",
        "PTM_results.xlsx",
    ):
        assert f'href="{href}"' in page
    assert "PTM_results.h5mu" not in page
    assert ".zip" not in page
    assert "CorrectFirst DPU" in page
    assert "KO_vs_WT" in page
    assert not list((tmp_path / "PTM_output").glob(".index_qmd_*"))
