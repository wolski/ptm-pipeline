import pandas as pd

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
