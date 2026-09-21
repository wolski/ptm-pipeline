# AGENTS.md

This file provides guidance to coding agents working in this repository.

## Changelog

Record every change to this project's code or user-visible behaviour in `CHANGELOG.md` at the repository root (Python
projects use `CHANGELOG.md`, not the R `NEWS.md`). Add a bullet under the heading for the current version
(`pyproject.toml`), creating a new version heading when a change opens one. Log the user-visible effect, not the
implementation detail. Do not log changes that only touch agent-instruction or repository meta files (`AGENTS.md`,
`CLAUDE.md`, and similar) unless explicitly asked.

## Project Overview

PTM Pipeline is a deployment tool for phosphoproteomics PTM (Post-Translational Modification) analysis. It scaffolds Snakemake-based workflows into projects that already have DEA (Differential Expression Analysis) output from `prolfquapp`.

## Commands

```bash
# Development
uv sync                              # Install dependencies
uv run ptm-pipeline --help           # Run CLI in development mode

# Documentation (MkDocs + Material, deployed by .github/workflows/pages.yml)
uv sync --only-group docs            # Install the docs toolchain
uv run mkdocs serve                  # Preview at http://127.0.0.1:8000
uv run mkdocs build --strict         # Build into public/ exactly as CI does

# CLI commands
ptm-pipeline init                       # Interactive initialization
ptm-pipeline init default               # Non-interactive initialization
ptm-pipeline run                        # Complete workflow
ptm-pipeline run dry                    # Preview complete workflow
ptm-pipeline clean                      # Remove declared outputs
ptm-pipeline clean init                 # Remove initialization files
ptm-pipeline clean all                  # Remove both
```

## Architecture

```
src/ptm_pipeline/
├── cli.py          # Cyclopts CLI entry point (init, run, clean)
├── discover.py     # Auto-detection of DEA folders and annotation files
├── init.py         # Project initialization and template copying
├── config.py       # YAML config generation
└── clean.py        # Initialization-file cleanup

template/                # Copied to target projects on init
├── Snakefile            # Workflow rules
└── helpers.py           # Workflow helpers
```

There is no `template/src/`. A project holds no R code: every rule calls
`ptm.sh <command>`, the one wrapper from the installed prophosqua's
`inst/application/bin`, which resolves that command's `CMD_*.R` from the install
path. `ptm-pipeline init` copies `ptm.sh` into the project so a person can run the same entry point by hand. To change analysis behaviour, edit prophosqua and reinstall it. Initialization no longer generates a Makefile; the CLI owns running and cleanup.

## Key Patterns

**DEA Folder Discovery** (`discover.py`):
- Phospho patterns: `DEA_*_WUphospho_*`, `DEA_*_WUcombined_*`, `DEA_*_*STY*`
- Protein patterns: `DEA_*_WUprot_*`, `DEA_*_WUtotal_*`
- Annotation files: `Inputs_*/*_annot_*.tsv` or `Inputs_*/*_dataset*.tsv`

**Template Location** (`init.py`):
- Three fallback paths: development (`./template`), installed (`importlib.resources`), system (`share/ptm-pipeline/template`)

**Analysis Types** (Snakemake):
- DPA: Differential PTM Abundance
- DPU: Differential PTM Usage
- CF: CorrectFirst (protein-corrected analysis)

## Dependencies

- Python: uv (not pip) - see pyproject.toml
- R packages: prolfquapp, prophosqua, tidyverse, readxl, writexl, arrow, clusterProfiler, ggseqlogo
- External: Snakemake, kinase-library (accessed via `uv tool run`)
