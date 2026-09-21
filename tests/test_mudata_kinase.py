import cbor2
import pandas as pd

from ptm_pipeline.mudata_kinase import _read_stage, _write_stage
from ptm_pipeline.mudata_values import pack, unpack


def test_motif_enrichment_payload_preserves_json_text():
    payload = {
        "mea_results": pd.DataFrame({"contrast": ["A_vs_B"], "NES": [1.5]}),
        "gsea_json": '{"data":{"A_vs_B":{}},"rank_lists":{"A_vs_B":{}}}',
    }

    restored = unpack(pack(payload))

    pd.testing.assert_frame_equal(
        restored["mea_results"].reset_index(drop=True),
        payload["mea_results"].reset_index(drop=True),
        check_dtype=False,
    )
    assert restored["gsea_json"] == payload["gsea_json"]


def test_cbor_handoff_preserves_kinase_results(tmp_path):
    source = {"analysis": "DPU", "statistics_sha256": "a" * 64}
    output = tmp_path / "MotifEnrichment.cbor"
    payload = {
        "mea_results": pd.DataFrame({"contrast": ["a_vs_b", "c_vs_b"], "NES": [1.5, -2.0]}),
        "gsea_json": '{"data":{},"rank_lists":{}}',
    }

    _write_stage(source, output, "MotifEnrichment", payload)
    with output.open("rb") as handle:
        encoded = cbor2.load(handle)
    assert encoded["stage"] == "MotifEnrichment"
    assert encoded["statistics_sha256"] == source["statistics_sha256"]
    restored = unpack(_read_stage(output, "MotifEnrichment")["result"])
    pd.testing.assert_frame_equal(restored["mea_results"].reset_index(drop=True), payload["mea_results"])
    assert restored["gsea_json"] == payload["gsea_json"]
