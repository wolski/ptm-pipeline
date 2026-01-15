# PTM Pipeline

Deploy phosphoproteomics PTM analysis pipeline to new projects.

## Installation

```bash
uv tool install git+https://github.com/wolski/ptm-pipeline

# Update to latest version
uv tool upgrade ptm-pipeline
```

## Usage

```bash
cd ~/Dropbox/DataAnalysis/o40XXX_NewProject
# DEA folders should already exist from prolfquapp

ptm-pipeline init    # Auto-detect DEA folders, generate config
make                 # Run the pipeline (or: make all)
```

### Makefile Targets

| Target | Description |
|--------|-------------|
| `make help` | Show available targets |
| `make all` | Run the full pipeline |
| `make dry-run` | Show what would be executed |
| `make validate` | Validate project setup |
| `make clean` | Remove output files (keeps config) |
| `make install` | Install ptm-pipeline tool |
| `make upgrade` | Upgrade to latest version |
| `make update` | Update pipeline files (keeps config) |

### CLI Commands

| Command | Description |
|---------|-------------|
| `ptm-pipeline init [DIR] [--name NAME] [--dry-run] [--force]` | Initialize pipeline |
| `ptm-pipeline clean [DIR] [--dry-run] [--force]` | Remove pipeline files (keeps DEA data) |
| `ptm-pipeline validate [DIR] [--quick]` | Check dependencies |
| `ptm-pipeline update [DIR] [--dry-run]` | Update pipeline files |
| `ptm-pipeline info [DIR]` | Show discovered DEA folders |

## Project Structure

Before `ptm-pipeline init`:
```
o40XXX_NewProject/
├── DEA_*_WUphospho_*/    # or DEA_*_WUcombined_*, DEA_*_*STY*
│   └── Inputs_WU_*/
└── DEA_*_WUprot_*/       # or DEA_*_WUtotal_*
```

After `ptm-pipeline init`:
```
o40XXX_NewProject/
├── DEA_*/...
├── ptm_config.yaml       # Generated config
├── Makefile              # Convenience targets
├── SnakefileV2.smk       # Pipeline
├── helpers.py
└── src/                  # R/Rmd analysis files
```

## Requirements

- Python 3.10+, Snakemake, uv
- R packages: tidyverse, readxl, writexl, arrow, prolfquapp, prophosqua, clusterProfiler, ggseqlogo

## Development

```bash
git clone https://github.com/wolski/ptm-pipeline
cd ptm-pipeline
uv sync
uv run ptm-pipeline --help
```

### Managing uv.lock

Regenerate after changing `pyproject.toml` or to update dependencies:

```bash
uv lock                          # Regenerate lock file
uv lock --upgrade-package click  # Update specific package
uv sync                          # Sync environment
```

Commit `uv.lock` to ensure reproducible installs.

## License

MIT
