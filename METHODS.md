# Materials and Methods

This section describes the computational workflow and software components used by the ptm-pipeline for integrated post-translational modification (PTM) and total proteome analysis.

## Differential Expression Analysis (prolfqua / prolfquapp)

Quantitative differential expression analysis of proteomics data is performed using **prolfqua**, an R package that implements moderated linear models for protein-level and PTM-level statistical testing. **prolfquapp** provides the application layer for batch processing and standardized reporting of differential expression results.

- Wolski WE, Nanni P, Grossmann J, d'Errico M, Schlapbach R, Panse C.
  "prolfqua: A Comprehensive R-Package for Proteomics Differential Expression Analysis."
  *Journal of Proteome Research* 22(4):1092--1104, 2023.
  DOI: [10.1021/acs.jproteome.2c00441](https://doi.org/10.1021/acs.jproteome.2c00441)

- Wolski WE, Grossmann J, Schwarz L, Leary P, Trker C, Nanni P, Schlapbach R, Panse C.
  "prolfquapp -- A User-Friendly Command-Line Tool Simplifying Differential Expression Analysis in Quantitative Proteomics."
  *Journal of Proteome Research* 24(2):955--965, 2025.
  DOI: [10.1021/acs.jproteome.4c00911](https://doi.org/10.1021/acs.jproteome.4c00911)

## PTM Data Preprocessing (prolfquappPTMReaders)

Search engine and quantification outputs (e.g., Spectronaut from Biognosys, FragPipe) are read and preprocessed using the **prolfquappPTMReaders** R package, which standardizes site-level quantification data for downstream analysis by prolfquapp.

- Wolski W.
  "prolfqua/prolfquappPTMreaders: 0.1.0." Zenodo, 2025.
  DOI: [10.5281/zenodo.15845243](https://doi.org/10.5281/zenodo.15845243)

## Integrated PTM Analysis (prophosqua)

The integrated PTM analysis is carried out using **prophosqua**, which implements three complementary statistical approaches:

- **DPA** (Differential PTM Abundance): tests for changes in PTM-site intensity between conditions.
- **DPU** (Differential PTM Usage): tests whether the ratio of PTM-site to total protein intensity changes, identifying regulation independent of protein abundance.
- **CorrectFirst**: applies protein-level correction before testing PTM sites, an alternative approach to distinguish PTM-specific regulation from protein expression changes.

References:

- Wolski W, Dittmann A, Panse C, Kunz L, Grossmann J.
  "Integrated Analysis of Post-Translational Modifications and Total Proteome: Methods for Distinguishing Abundance from Usage Changes."
  *Methods in Molecular Biology*, 2025 (submitted).

- Grossmann J, Wolski W.
  "prolfqua/prophosqua: 0.3.0." Zenodo, 2025.
  DOI: [10.5281/zenodo.15845272](https://doi.org/10.5281/zenodo.15845272)

## Kinase Activity Analysis

Kinase activity inference is supported through two complementary approaches:

### PTMsigDB / PTM-SEA

Enrichment analysis of phosphorylation sites is performed using the **PTM Signatures Database** (PTMsigDB) and the PTM Set Enrichment Analysis (PTM-SEA) method, which adapts gene set enrichment analysis to phosphosite-level data.

- Krug K, Mertins P, Zhang B, Hornbeck P, Raju R, Ahmad R, Szucs M, Mundt F, Forestier D, Jane-Valbuena J, Keshishian H, Gillette MA, Tamayo P, Mesirov JP, Jaffe JD, Carr SA, Mani DR.
  "A Curated Resource for Phosphosite-specific Signature Analysis."
  *Molecular & Cellular Proteomics* 18(3):576--593, 2019.
  DOI: [10.1074/mcp.TIR118.000943](https://doi.org/10.1074/mcp.TIR118.000943)

### Kinase Library

Motif-based kinase activity inference is performed using the **Kinase Library**, which predicts kinase-substrate relationships from phosphorylation site sequence motifs via motif enrichment analysis (MEA).

- Johnson JL, Yaron TM, Huntsman EM, Kerelsky A, Song J, Regber A, Chiang TY, Sber G, Braber N, Kim B, Lee ER, Khanin R, Mano Y, Van de Pette M, Sinha S, Lowe SW, Neilson L, et al.
  "An atlas of substrate specificities for the human serine/threonine kinome."
  *Nature* 613(7945):759--766, 2023.
  DOI: [10.1038/s41586-022-05575-3](https://doi.org/10.1038/s41586-022-05575-3)

## Pipeline Orchestration (ptm-pipeline)

The analysis workflow is orchestrated using **Snakemake** and deployed to analysis projects via the `ptm-pipeline` command-line tool. The pipeline coordinates all steps from data preprocessing through differential expression, PTM-specific analyses, and kinase activity inference.

- Wolski WE.
  "wolski/ptm-pipeline: 0.1.1." Zenodo, 2025.
  DOI: [10.5281/zenodo.18349420](https://doi.org/10.5281/zenodo.18349420)
