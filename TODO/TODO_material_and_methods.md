We need a Materials and Methods section for our package. It could go in README.md or a different markdown file, but basically we need to describe the whole stack, starting with differential expression analysis using prolfqua and prolfquapp — obviously we must cite here prolfqua and prolfquapp publications and MiMB. Next we need to briefly describe prophosqua; the issue here is that prophosqua is not published yet, but we just submitted an article to Methods in Molecular Biology (see MiMB vignette for title and authors). I think we still should reference this. Finally, we need to reference the publications for KinaseLib and PTMsigDB. All the references are also in the MiMB vignette. Last but not least, Zenodo references for prophosqua, ptm-pipeline, and prolfquappPTMReaders.

---

## Plan: Create `METHODS.md` in ptm-pipeline repo root

### Target file
- **Create**: `METHODS.md` in the repo root
- **Edit**: `README.md` — add a link to METHODS.md

### Reference source
- All citations verified from: `prophosqua/vignettes/doi_references_key.bib`
- MiMB vignette: `prophosqua/vignettes/MiMBIntegratedPTM.Rmd`

### Structure of METHODS.md

#### 1. Differential Expression Analysis (prolfqua / prolfquapp)
- Describe: quantitative proteomics differential expression using prolfqua's moderated linear models; prolfquapp provides the application layer for batch processing
- Cite:
  - Wolski et al. (2023) "prolfqua: Generating Comprehensive Reports..." *J. Proteome Research*. DOI: `10.1021/acs.jproteome.2c00441`
  - Wolski et al. (2025) "Streamlining Differential Expression Analysis..." *J. Proteome Research*. DOI: `10.1021/acs.jproteome.4c00911`

#### 2. Integrated PTM Analysis (prophosqua)
- Describe: three analysis modes — DPA (differential PTM abundance), DPU (differential PTM usage), CorrectFirst (protein-corrected analysis)
- Note: submitted to Methods in Molecular Biology, not yet published
- Cite:
  - Wolski, Dittmann, Panse, Kunz, Grossmann (2025) "Integrated Analysis of Post-Translational Modifications and Total Proteome: Methods for Distinguishing Abundance from Usage Changes." *Methods in Molecular Biology* (submitted).
  - Zenodo: prophosqua v0.1.0. DOI: `10.5281/zenodo.15845272`

#### 3. PTM Data Preprocessing (prolfquappPTMReaders)
- Brief mention: R package for reading and preprocessing PTM data outputs from prolfquapp
- Cite:
  - Zenodo: prolfquappPTMReaders v0.1.0. DOI: `10.5281/zenodo.15845243`

#### 4. Kinase Activity Analysis
Two approaches:

- **PTMsigDB / PTM-SEA**: enrichment analysis using the PTM Signatures Database
  - Krug et al. (2019) "A Curated Resource for Phosphosite-specific Signature Analysis." *Mol. Cell. Proteomics* 18(3). DOI: `10.1074/mcp.TIR118.000943`

- **KinaseLib**: motif-based kinase activity inference via motif enrichment analysis (MEA)
  - Johnson et al. (2023) "An atlas of substrate specificities for the human serine/threonine kinome." *Nature* 613. DOI: `10.1038/s41586-022-05575-3`

#### 5. Pipeline Orchestration (ptm-pipeline)
- Describe: Snakemake-based workflow orchestration, deployed via `ptm-pipeline init`
- Cite:
  - Zenodo: ptm-pipeline v0.1.1. DOI: `10.5281/zenodo.18349420`

#### 6. References
Formatted reference list at the bottom.

### Verification
- All DOIs verified against `doi_references_key.bib`
- All packages from TODO covered: prolfqua, prolfquapp, prophosqua, prolfquappPTMReaders, KinaseLib, PTMsigDB, ptm-pipeline
- All three Zenodo DOIs included (prophosqua, ptm-pipeline, prolfquappPTMReaders)

