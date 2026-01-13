"""Configuration generation for PTM pipeline."""

from pathlib import Path
from datetime import date
import yaml


def generate_config(
    phospho_dir: Path,
    protein_dir: Path,
    annot_file: Path,
    contrasts: list[str],
    output_name: str | None = None,
    project_dir: Path | None = None,
    fdr: float = 0.25,
    log2fc: float = 0.5,
) -> dict:
    """Generate pipeline configuration dictionary.

    Args:
        phospho_dir: Path to phospho DEA folder
        protein_dir: Path to protein DEA folder
        annot_file: Path to annotation TSV file
        contrasts: List of contrast names
        output_name: Optional name for output directory
        project_dir: Project root for making paths relative
        fdr: FDR threshold for downstream analyses
        log2fc: log2 fold change threshold for downstream analyses

    Returns:
        Configuration dictionary ready for YAML serialization
    """
    # Make paths relative to project_dir if provided
    if project_dir:
        phospho_path = str(phospho_dir.relative_to(project_dir))
        protein_path = str(protein_dir.relative_to(project_dir))
        annot_path = str(annot_file.relative_to(project_dir))
    else:
        phospho_path = str(phospho_dir)
        protein_path = str(protein_dir)
        annot_path = str(annot_file)

    # Generate output directory name
    if output_name:
        dir_out = f"PTM_{output_name}"
    else:
        dir_out = f"PTM_{date.today().strftime('%Y%m%d')}"

    return {
        # Source directory
        "src": "src",

        # Output configuration
        "dir_out": dir_out,
        "max_fig": 10,

        # Significance thresholds for downstream analyses (seqlogo, n_to_c plots)
        "fdr": fdr,
        "log2fc": log2fc,

        # DEA directories
        "phospho_dea_dir": phospho_path,
        "protein_dea_dir": protein_path,
        "annot_file": annot_path,

        # Analysis types with their configurations
        "analyses": {
            "dpa": {
                "sheet": "DPA",
                "subdir": "PTM_DPA",
                "xlsx_input": "Result_DPA.xlsx",
                "stat_column": "statistic.site",
            },
            "dpu": {
                "sheet": "DPU",
                "subdir": "PTM_DPU",
                "xlsx_input": "Result_DPU.xlsx",
                "stat_column": "statistic.site",
            },
            "cf": {
                "sheet": "CF",
                "subdir": "PTM_CF_DPU",
                "xlsx_input": "CorrectFirst_PTM_usage_results.xlsx",
                "stat_column": "statistic.site",
            },
        },

        # Contrasts for MEA analysis
        "contrasts": contrasts,

        # KinaseLib settings
        "kinaselib": {
            "repo": "git+https://github.com/wolski/kinase-library",
            "kin_type": "ser_thr",
            "threshold": 95,
            "permutations": 1000,
        },

        # Thread settings
        "threads": {
            "mea": 4,
        },

        # PTMsigDB preprocessing
        "ptmsigdb": {
            "output_dir": "data/ptmsigdb",
            "keep_categories": "KINASE",
            "trim_to": 15,
        },
    }


def write_config(config: dict, output_path: Path) -> None:
    """Write configuration to YAML file."""
    with open(output_path, "w") as f:
        # Custom representer to avoid aliases
        yaml.Dumper.ignore_aliases = lambda *args: True
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def config_to_yaml_string(config: dict) -> str:
    """Convert config dict to YAML string for preview."""
    yaml.Dumper.ignore_aliases = lambda *args: True
    return yaml.dump(config, default_flow_style=False, sort_keys=False)
