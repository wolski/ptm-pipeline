"""Helper functions for Snakefile

This module contains utility functions for finding DEA directories
and constructing file paths used by the Snakemake pipeline.
"""

import glob


def get_parquet_path(dea_dir: str) -> str:
    """Get parquet file path from a DEA directory.

    Finds the lfqdata_normalized.parquet file within the Results_WU_* subdirectory.

    Args:
        dea_dir: Path to DEA output directory (e.g., "DEA_setup/DEA_20260109_WUphospho_SHP2_vsn")

    Returns:
        Path to the normalized parquet file

    Raises:
        ValueError: If no parquet file is found
    """
    pattern = f"{dea_dir}/Results_WU_*/lfqdata_normalized.parquet"
    matches = glob.glob(pattern)
    if not matches:
        raise ValueError(f"No parquet file found in {dea_dir}")
    return matches[0]


def build_analysis_lookups(dir_out: str, analyses_config: dict) -> dict:
    """Build lookup dictionaries for analysis configurations.

    Args:
        dir_out: Base output directory
        analyses_config: Dictionary of analysis configurations

    Returns:
        Dictionary containing:
        - types: List of analysis type keys
        - dirs: Dict mapping analysis -> output directory
        - sheets: Dict mapping analysis -> Excel sheet name
        - xlsx_inputs: Dict mapping analysis -> input Excel filename
        - stat_columns: Dict mapping analysis -> statistic column name
    """
    return {
        "types": list(analyses_config.keys()),
        "dirs": {k: f"{dir_out}/{v['subdir']}" for k, v in analyses_config.items()},
        "sheets": {k: v["sheet"] for k, v in analyses_config.items()},
        "xlsx_inputs": {k: v["xlsx_input"] for k, v in analyses_config.items()},
        "stat_columns": {k: v["stat_column"] for k, v in analyses_config.items()},
    }
