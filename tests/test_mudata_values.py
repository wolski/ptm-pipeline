"""Portable R/Python values retain numeric types and scientific missingness."""

import tempfile
import unittest

import h5py
import numpy as np
import pandas as pd
from anndata.io import read_elem, write_elem

from ptm_pipeline.mudata_values import pack, unpack


class PortableValuesTest(unittest.TestCase):
    def test_mea_object_columns_remain_numeric(self):
        frame = pd.DataFrame(
            {"ES": pd.Series([0.2, -0.4], dtype=object), "kinase": ["AKT1", "AKT2"]}
        )
        actual = unpack(pack({"mea_results": frame}))["mea_results"]
        pd.testing.assert_frame_equal(
            actual.reset_index(drop=True), frame, check_dtype=False
        )
        self.assertEqual(actual["ES"].dtype.kind, "f")

    def test_missing_strings_are_distinct_from_empty_strings(self):
        frame = pd.DataFrame(
            {"annotation": ["", None, "NA"], "score": [1.0, np.nan, 3.0]}
        )
        actual = unpack(pack(frame)).reset_index(drop=True)
        pd.testing.assert_frame_equal(actual, frame, check_dtype=False)

    def test_empty_frame_retains_columns(self):
        frame = pd.DataFrame(
            {"term": pd.Series(dtype=str), "score": pd.Series(dtype=float)}
        )
        actual = unpack(pack(frame)).reset_index(drop=True)
        pd.testing.assert_frame_equal(actual, frame, check_dtype=False)

    def test_hdf5_roundtrip_preserves_missingness_and_single_rows(self):
        value = {"result": pd.DataFrame({"kinase": ["AKT1"], "score": [np.nan]})}
        with tempfile.TemporaryDirectory() as directory:
            with h5py.File(f"{directory}/values.h5", "w") as handle:
                write_elem(handle, "result", pack(value))
                recovered = unpack(read_elem(handle["result"]))
        pd.testing.assert_frame_equal(
            recovered["result"].reset_index(drop=True), value["result"]
        )

    def test_r_factor_missingness_is_retained(self):
        encoded = {"type": "factor", "values": ["case", "NA"], "missing": [False, True]}
        self.assertEqual(unpack(encoded).tolist(), ["case", None])


if __name__ == "__main__":
    unittest.main()
