# PTM Pipeline

Deploy phosphoproteomics PTM analysis pipeline to new projects.

## Installation

```bash
uv tool install git+https://github.com/wolski/ptm-pipeline
```

To update to the latest version:
```bash
uv tool upgrade ptm-pipeline
```

## Usage

### Initialize a new project

```bash
cd ~/Dropbox/DataAnalysis/o40XXX_NewProject
# DEA folders should already exist from prolfquapp

ptm-pipeline init
# Auto-detects DEA folders, generates ptm_config.yaml, copies pipeline files

# Then run the pipeline
snakemake -s SnakefileV2.smk --configfile ptm_config.yaml -j1 all
```

### Commands

**init** - Initialize pipeline in a project directory
```bash
ptm-pipeline init [DIRECTORY] [--name NAME] [--dry-run] [--force]
```

**validate** - Check that all dependencies are available
```bash
ptm-pipeline validate [DIRECTORY] [--quick]
```

**update** - Update pipeline files to latest version
```bash
ptm-pipeline update [DIRECTORY] [--dry-run]
```

**info** - Show discovered DEA folders (useful for debugging)
```bash
ptm-pipeline info [DIRECTORY]
```

## Expected Project Structure

Before running `ptm-pipeline init`, your project should have DEA folders:

```
o40XXX_NewProject/
├── DEA_YYYYMMDD_WUphospho_*/     # From prolfquapp phospho DEA
│   └── Inputs_WU_*/
│       └── phospho_annot_*.tsv  # Sample annotation
├── DEA_YYYYMMDD_WUprot_*/        # From prolfquapp protein DEA
└── ...
```

After `ptm-pipeline init`:

```
o40XXX_NewProject/
├── DEA_YYYYMMDD_WUphospho_*/
├── DEA_YYYYMMDD_WUprot_*/
├── ptm_config.yaml               # Generated config
├── SnakefileV2.smk              # Pipeline orchestration
├── helpers.py                    # Snakemake helpers
└── src/                          # R scripts and Rmd files
    ├── Analysis_DPA_DPU.Rmd
    ├── Analysis_CorrectFirst_DEA.Rmd
    ├── Analysis_n_to_c.Rmd
    └── ...
```

## Requirements

- Python 3.10+
- Snakemake
- R with packages: tidyverse, readxl, writexl, arrow, prolfquapp, prophosqua, clusterProfiler, ggseqlogo
- uv (for kinase-library access)

## Development

```bash
git clone https://github.com/wolski/ptm-pipeline
cd ptm-pipeline
uv sync
uv run ptm-pipeline --help
```

## License

MIT
