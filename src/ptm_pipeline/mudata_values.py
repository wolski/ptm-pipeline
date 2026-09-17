"""Decode and encode the portable report values stored by prophosqua in MuData."""

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd


def _vector(value: Any) -> np.ndarray:
    return np.asarray([] if value is None else value).reshape(-1)


def unpack(value: Mapping[str, Any]) -> Any:
    """Decode a stored R value for the kinase-library DataFrame APIs."""
    readers = {
        "null": lambda item: None,
        "atomic": _unpack_atomic,
        "list": _unpack_list,
        "data.frame": _unpack_frame,
        "factor": lambda item: _unpack_atomic({**item, "storage": "character"}),
    }
    return readers[value["type"]](value)


def _unpack_atomic(value: Mapping[str, Any]) -> Any:
    data = _vector(value["values"])
    missing = _vector(value.get("missing")).astype(bool)
    if missing.any():
        data = (
            data.astype(object)
            if value["storage"] == "character"
            else data.astype(float)
        )
        data[missing] = None if value["storage"] == "character" else np.nan
    dimensions = _vector(value.get("dimensions"))
    if len(dimensions):
        return data.reshape(tuple(dimensions.astype(int)), order="F")
    names = _vector(value.get("names"))
    if len(names):
        return dict(zip(names, data, strict=True))
    return data.item() if data.size == 1 else data


def _unpack_list(value: Mapping[str, Any]) -> Any:
    items = [unpack(item) for _, item in sorted(value["items"].items())]
    names = _vector(value.get("names"))
    return dict(zip(names, items, strict=True)) if len(names) else items


def _unpack_frame(value: Mapping[str, Any]) -> pd.DataFrame:
    columns = unpack(value["columns"])
    frame = pd.DataFrame({name: _vector(column) for name, column in columns.items()})
    frame.index = _vector(value["row_names"])
    return frame


def pack(value: Any) -> dict[str, Any]:
    """Encode complete Python results in the R stage reader's portable schema."""
    if value is None:
        return {"type": "null"}
    if isinstance(value, pd.DataFrame):
        return {
            "type": "data.frame",
            "row_names": np.asarray(
                [str(i + 1) for i in range(len(value))], dtype=object
            ),
            "columns": pack(
                {name: value[name].infer_objects().to_numpy() for name in value.columns}
            ),
        }
    if isinstance(value, Mapping):
        return {
            "type": "list",
            "names": np.asarray(list(value), dtype=object),
            "items": {
                f"item_{i:06d}": pack(item)
                for i, item in enumerate(value.values(), start=1)
            },
        }
    array = np.asarray(value)
    missing = pd.isna(array)
    storage = {"b": "logical", "i": "integer", "u": "integer", "f": "double"}.get(
        array.dtype.kind, "character"
    )
    if storage == "character":
        array = np.where(missing, "", array).astype(str).astype(object)
    return {
        "type": "atomic",
        "storage": storage,
        "values": array.reshape(-1, order="F"),
        "missing": missing.reshape(-1, order="F"),
        "names": None,
        "dimensions": None,
        "dimnames": {"type": "null"},
    }
