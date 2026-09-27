import gzip
import json

import cbor2
import pandas as pd

from ptm_pipeline.mudata_kinase import _read_stage, _write_gsea_document, _write_stage, scan
from ptm_pipeline.mudata_values import unpack


def test_cbor_handoff_preserves_kinase_assignments(tmp_path):
    source = {"analysis": "DPU", "statistics_sha256": "a" * 64}
    output = tmp_path / "intermediate_kinase_assignments.cbor.gz"
    payload = {
        "term2gene": pd.DataFrame(
            {"term": ["CDK2", "PKACA"], "gene": ["AAAAAAASAAAAAAA", "BBBBBBBSBBBBBBB"]}
        )
    }

    _write_stage(source, output, "KinaseAssignments", payload)
    encoded = _read_stage(output, "KinaseAssignments")
    assert encoded["analysis"] == source["analysis"]
    assert encoded["statistics_sha256"] == source["statistics_sha256"]
    restored = unpack(encoded["result"])
    pd.testing.assert_frame_equal(restored["term2gene"].reset_index(drop=True), payload["term2gene"])


def test_motif_enrichment_is_a_gzipped_gsea_document(tmp_path):
    output = tmp_path / "result_mea.json.gz"
    document = {
        "data": {"a_vs_b": {"contrast": "a_vs_b", "categories": {}}},
        "rank_lists": {"a_vs_b": {"contrast": "a_vs_b", "entries": {"AAAAAAASAAAAAAA": 2.5}}},
    }

    _write_gsea_document(output, document)
    with gzip.open(output, "rt", encoding="utf-8") as handle:
        assert json.load(handle) == document
    assert list(tmp_path.iterdir()) == [output]


def test_scan_names_the_windows_it_was_given(tmp_path):
    source = {"analysis": "DPA", "statistics_sha256": "b" * 64}
    inputs = tmp_path / "intermediate_kinase_inputs.cbor.gz"
    windows = pd.DataFrame({"SequenceWindow": ["PETITIRSGPPSPLP", "RRRRRRRSAAAAAAA", "LLLLLLLSPLLLLLL"]})
    _write_stage(source, inputs, "KinaseInputs", {"seqwindows": windows})
    stored = _read_stage(inputs, "KinaseInputs")
    stored["settings"] = {"kin_type": "ser_thr", "threshold": 0}
    with gzip.open(inputs, "wb") as handle:
        cbor2.dump(stored, handle)
    output = tmp_path / "intermediate_kinase_assignments.cbor.gz"

    scan(inputs, output)
    term2gene = unpack(_read_stage(output, "KinaseAssignments")["result"])["term2gene"]
    assert set(term2gene["gene"]) == set(windows["SequenceWindow"])
