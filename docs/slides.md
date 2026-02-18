---
title: "ptm-pipeline"
subtitle: Automated Integrated Phosphoproteomics Analysis
author: Witold Wolski
date: 2026-02-17
---

## The Problem

- Phosphoproteomics experiments produce two datasets: phospho-sites and total protein
- Changes in phosphorylation can reflect true signaling OR simply protein abundance changes
- Distinguishing these requires multiple complementary statistical analyses
- Manual orchestration is error-prone and hard to reproduce

## What ptm-pipeline Does

ptm-pipeline deploys a complete, reproducible Snakemake workflow on top of prolfquapp differential expression results.

**Input:** DEA output folders from prolfquapp (phospho + total protein)

**Output:** Integrated HTML reports with:

- Differential PTM analysis (3 statistical approaches)
- Kinase activity inference (2 methods)
- Sequence motif analysis
- Publication-ready figures and Excel tables

## prophosqua: Integrated PTM Analysis

**prophosqua** implements three complementary statistical approaches to distinguish PTM-specific regulation from protein abundance changes.

- Integrates phospho-site and total protein quantification
- Uses moderated linear models (prolfqua) for statistical testing
- Generates per-contrast HTML reports with volcano plots, heatmaps, and result tables

Wolski W, Dittmann A, Panse C, Kunz L, Grossmann J.
"Integrated Analysis of Post-Translational Modifications and Total Proteome: Methods for Distinguishing Abundance from Usage Changes."
*Methods in Molecular Biology*, 2025.

GitHub: https://github.com/prolfqua/prophosqua

DOI: 10.5281/zenodo.15845272

## Three Complementary Statistical Approaches

| Analysis | What it tests | When to use |
|----------|--------------|-------------|
| **DPA** | Change in phospho-site intensity | Standard phospho differential analysis |
| **DPU** | Change in phospho-to-protein ratio | Regulation independent of protein abundance |
| **CorrectFirst** | Phospho-sites after protein-level correction | Isolate PTM-specific changes |

All three are computed automatically for every contrast.

Statistical framework: moderated linear models via prolfqua/prophosqua.

**CorrectFirst** based on: Demeulemeester et al., "msqrob2PTM: Differential Abundance and Differential Usage Analysis of MS-Based Proteomics Data at the PTM and Peptidoform Level." *MCP* 23(2):100708, 2024.

**DPU** based on: Kohler et al., "MSstatsPTM: Statistical Relative Quantification of Posttranslational Modifications in Bottom-Up Mass Spectrometry-Based Proteomics." *MCP* 22(1):100477, 2023.

## Kinase Activity Inference

Two complementary approaches for predicting upstream kinase activity:

**Kinase Library** (Johnson et al., Nature 2023)

- Motif-based prediction from phospho-site sequence context
- Motif Enrichment Analysis (MEA) identifies active kinases
- Sequence logo visualization of enriched motifs

**PTM-SEA** (Krug et al., MCP 2019)

- Site-set enrichment using the PTM Signatures Database (PTMsigDB)
- Adapts GSEA to phosphosite-level data
- Identifies enriched kinase-substrate and perturbation signatures

## Workflow: Input to Output

```
prolfquapp DEA results (phospho + protein)
        |
        v
  ptm-pipeline init     <- auto-discovers DEA folders
        |
        v
  Snakemake workflow     <- orchestrates all steps
        |
        v
  HTML reports + PTM_results.xlsx
```

## Workflow: Analysis Steps

For each contrast, the pipeline runs DPA, DPU, and CorrectFirst analysis.

For each analysis type:

- Kinase activity inference (Kinase Library + PTM-SEA)
- N-to-C terminal phospho-site distribution
- Sequence motif analysis (seqlogo)

Combined output:

- Integrated results table (Excel + HTML index)

## Usage - Two Commands

**Native (requires R + Python environment):**

```
ptm-pipeline init      # auto-detect data, generate config
make all               # run the full pipeline
```

**Docker (zero local setup):**

```
ptm-pipeline.sh init-default DEA_data/ output/
ptm-pipeline.sh run output/
```

Docker image is pulled automatically on first use.

## Supported Input Formats

| Search Engine | Quantification | Status |
|--------------|---------------|--------|
| FragPipe | TMT | Tested |
| FragPipe | LFQ | Tested |
| Spectronaut (Biognosys) | DIA | Tested |

Input data is preprocessed by prolfquappPTMReaders, which standardizes site-level quantification across search engines.

## Software Stack

| Component | Role |
|-----------|------|
| **prolfqua** / **prolfquapp** | Differential expression analysis |
| **prolfquappPTMReaders** | Search engine output parsing |
| **prophosqua** | Integrated PTM analysis (DPA, DPU, CF) |
| **Kinase Library** | Motif-based kinase activity prediction |
| **PTM-SEA** / **PTMsigDB** | Phosphosite-set enrichment |
| **Snakemake** | Workflow orchestration |
| **ptm-pipeline** | Deployment tool and CLI |

## Reproducibility

- Fully containerized via Docker (prolfquapp base image)
- CI/CD: every commit triggers integration tests on 3 datasets
- Configurable via single YAML file (FDR, log2FC thresholds)
- Versioned on GitHub and archived on Zenodo
- Example reports available from CI artifacts

GitHub: https://github.com/wolski/ptm-pipeline

Docs: https://wolski.github.io/ptm-pipeline

DOI: 10.5281/zenodo.18349420
