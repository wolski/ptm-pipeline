# ptm-pipeline 0.3.0

- The documentation site is built with Zensical, the renderer the anndata-omics-bridge packages use, instead of MkDocs Material. `mkdocs.yml` stays the configuration; the docs group installs `zensical` and `pymdown-extensions`, and both workflows run `zensical build --clean --strict`.

- Building the documentation is now a CI job as well as a deployment step, so a broken link, a missing include or a bad nav entry fails a pull request instead of only failing the Pages deploy on `main`.

- The public-dataset survey has moved out of this repository into `ptm_technote`, where the rest of the dataset evaluation lives. It is no longer part of the pipeline documentation site.

- The public-dataset survey now names PXD058857 (ARID1A x vemurafenib x trametinib in A375 melanoma) the primary candidate for the end-to-end demonstration, and records why: one TMT plex holds one complete replicate of the 2 x 2 x 2, so every contrast is within-plex and the plex belongs in the model as a block rather than being removed with ComBat. The deposit's current state is recorded with it - 100 files, 94.6 GB, PARTIAL, no enrichment-named files - along with the two questions for the authors that block a re-search.

- The public-dataset survey now records that MSV000085565's two TMT plexes are a proper block — every condition present in both — and points to `ptm_technote/TODO_dataset_factorial.md` for the verified channel-to-condition tables of both leading candidates.

- Store the six per-analysis stage artifacts compressed, and by what they are: the three completed enrichments as `result_*.json.gz`, gzipped string_gsea documents that any gzip reader opens and `protsea::read_gsea_json()` parses, and the three kinase preparations as `intermediate_*.cbor.gz`. `ptm-kinase-cbor` reads and writes gzipped artifacts to match. The final `PTM_results.h5mu` now names these files instead of copying them, which takes it from 2.3 GB to roughly its statistics size on a three-analysis order; it therefore has to stay beside its analysis folders.

- Name CBOR handoffs explicitly by role: three `result_*.cbor` enrichment outputs and three `intermediate_*.cbor` preparation files per analysis. Existing order outputs can be renamed in place without recalculating enrichment.
- Deliver only `PTM_results.xlsx` alongside the final H5MU and reports. The workbook contains statistics and enrichment tables; per-analysis Excel and RDS files are no longer pipeline outputs. `ptm3d` remains a separate visualization application with no Snakemake rule or pipeline dependency.
- `ptm-pipeline clean` and `clean all` now remove the configured PTM output directory after Snakemake cleanup, including reports and other files left by rules removed from the current workflow; DEA input folders remain protected.

- Expose only `init`, `run`, and `clean` in the project CLI. `init default` uses non-interactive defaults, `run dry` previews the full workflow, and `clean init`/`clean all` select cleanup scope. New projects no longer get a Makefile or obsolete data/reports targets.
- Render one enrichment report per DPA, DPU, and CorrectFirst analysis from the same parameterized QMD, and link all three from the index. Set a separate 5000-site maximum for kinase substrate GSEA; the 500-site PTM-SEA limit excluded every kinase set in o43037.
- Render only the PTM statistics and enrichment Quarto reports from their MuData stages. A lightweight index links them; the delivery archive includes only declared final outputs, so stale legacy reports and proptm3d files are omitted.
- Replace 18 full MuData enrichment handoffs with compact CBOR artifacts. The delivery archive includes only the final H5MU and excludes stage CBOR and obsolete stage H5MU files.
- Install the current MuData, report-template, and enrichment R dependencies before building prophosqua in the pipeline image, then build prophosqua without asking `remotes` to reinterpret the installed Bioconductor metadata.
- Preserve the native kinase-library MEA result as the same portable GSEA JSON
  used by the R enrichment methods, including ranked values, substrate sets,
  parameters, leading edges, source running scores, and hit positions.
- Updating an existing order adds the two MuData input paths from its configured DEA directories while preserving all analysis settings, so the updated workflow can run immediately.

- Import paired DEA AnnData once, then use MuData for every statistics, ranking, motif assignment, enrichment, and report input. Assemble the final container before reports and write the single Excel delivery workbook only after all reports finish. Discovery reads stored design/contrasts without a separate annotation file. Requires Python 3.12+, current prophosqua, and prolfquapp.

- Discover CSV and TSV annotations with case-insensitive design columns, preserve an editable configuration when discovery is incomplete, and order MEA result generation after motif assignment.

- A project directory now holds no R code at all: `template/src/` is gone, and with it the
  seven scripts and report templates every project used to carry. Every rule calls
  `ptm.sh <command>` -- one wrapper from the installed prophosqua, which resolves the
  command's `CMD_*.R` from the install path. There is nothing left in a working directory
  that an edit can be lost from, and one place -- prophosqua -- where the analysis lives.
  `ptm-pipeline update` places `ptm.sh` in the project so the same steps can be run by
  hand, and deletes both a `src/` and the per-command `ptm_*.sh` wrappers of a project
  initialised before the move. `./ptm.sh help` lists the steps, read from the
  installation, so it cannot fall behind the package.
- No rule embeds R code any more. The seven `Rscript -e "rmarkdown::render(...)"` blocks and
  the generated `rmd_finder` snippet are replaced by `ptm.sh render`, which takes the
  report name and its parameters as arguments. `helpers.py` lost `get_prophosqua_vignette()` and
  `rmd_path_r_code()` and gained `get_prophosqua_file()`, which resolves any installed
  script, template or wrapper.
- Computing and reporting are separate rules, so a caption fix no longer costs a
  reanalysis. `analysis_dea` became `compute_dpa_dpu` plus `report_dpa_dpu`; `cf_dea` became
  `compute_cf_dea` plus `report_cf_dea` (about 15 seconds instead of about 85, with no
  downstream cascade); and the three enrichment reports each gained a compute rule.
- The documentation site gained a workflow diagram and a section on what the pipeline adds
  to the DEA results it reads -- the DPA table is the site-level DEA result with its
  protein-level counterpart joined alongside, and the diagram says which steps compute data,
  which render HTML, and which of them run once per analysis type. The diagram is a mermaid
  fence, so it renders both on the Pages site and in the file view on GitHub.
- Report templates are resolved by asking prophosqua where they are, rather than assuming
  `inst/application`. The analysis reports are that package's vignettes and install into its
  `doc/`; `helpers.py` gained `get_prophosqua_report()`, which calls the package's own
  resolver so the rule lives in one place. The Docker image already installs prophosqua with
  its vignettes built, so nothing about deployment changes.
- The documentation site is built with MkDocs and Material instead of Jekyll, matching the
  FGCZ Python project layout: a root `mkdocs.yml` names the nav, `uv sync --only-group docs`
  installs the toolchain, and `pages.yml` deploys what `mkdocs build --strict` produces, so a
  broken link or a missing include fails the build instead of shipping. Mermaid diagrams are
  rendered by the theme, so the pages no longer carry a hand-written mermaid loader, and the
  Methods page includes the root `METHODS.md` directly rather than the workflow copying it in.
  `uv run mkdocs serve` previews the site locally, which the Jekyll setup could not do without
  Ruby.
- The documentation site gained an R package dependency page: which of the R packages the
  pipeline calls depends on which, what each one owns, and the layer ordering
  prolfqua → prolfquapp → prophosqua that keeps the graph acyclic and decides how far
  upstream a fix belongs. Edges are read from the packages' `DESCRIPTION` files, which stay
  the only declaration of them.
- Two new targets name the tiers: `snakemake -j1 data` builds everything that writes data,
  `snakemake -j1 reports` everything that renders HTML from it.
- The enrichment result workbooks and RDS files -- PTM-SEA, kinase-library GSEA and MEA, six
  files per analysis type -- are declared rule outputs at last. They were written from inside
  a conditional chunk of a report and could not be declared, so a failed or empty enrichment
  left the previous run's workbook in place looking current.
- Reinstalling prophosqua now invalidates every rule that runs R. Each such rule declares
  the installed package's `Meta/package.rds`, which `R CMD INSTALL` rewrites, alongside the
  wrapper and script it names -- the work a script does happens in the package's R code,
  which is none of the files the rule used to name. A full rerun after a reinstall is the
  price of never again seeing a report that is up to date and wrong.
- `ptm_config.yaml` no longer carries a `src` key; nothing reads it. Existing config files
  keep working, the key is simply ignored. `ptm-pipeline validate` checks that the installed
  prophosqua ships the wrappers instead of checking for a `src/` directory.

- Stop shipping `src/dea_utils.R` and `src/feature_preparation.R` into every project. Their
  functions are now prophosqua exports, documented and tested there. A project no longer
  carries a copy that can drift from the package or shadow it, and the reports call the
  package directly instead of `source()`ing a file out of the working directory.
- `combine_ptm_results.R` takes seven arguments instead of eight; the utilities argument is
  gone with the file it pointed at.

- Rerun the analyses when the DEA results they read change, by declaring the DEA
  workbooks, normalized-abundance parquets and configuration YAMLs, and the sample
  annotation, as rule inputs. The DPA/DPU and CorrectFirst rules named only their
  own report source before and resolved the data themselves at render time, so
  rerunning a DEA, editing the annotation, or pointing `ptm_config.yaml` at another
  DEA directory left the whole pipeline reported as up to date.
- Track the MEA result workbook and RDS as outputs of the MEA report rule, so a
  failed render no longer leaves a stale workbook that looks current, and they can
  be requested as targets.
- Render the DPU integration overview in a private directory instead of the project
  working directory. The prophosqua template and its bibliography were copied into
  the project root and the bibliography left behind, and two concurrent renders
  could overwrite each other's knitr intermediates.
- Resolve the DEA input files deterministically when a DEA directory holds more
  than one `Results_WU_*` subdirectory.
- Export the per-site and per-protein `estimate_type` columns to the combined
  `PTM_results.xlsx`. The N-to-C reports read that workbook, so without those
  columns every site was drawn as if it had been measured; imputed estimates are
  distinguishable again.
- Stop shadowing `prophosqua::prepare_ntoc_data()` with a project-level copy that
  labelled every site `observed` regardless of how it was estimated. The N-to-C
  reports now use the package function, which reads the exported `estimate_type`
  columns, and mark limit-of-detection imputed estimates as such.
- Rerender every report built from a prophosqua template when the installed
  prophosqua changes, by declaring the template as a rule input. Reinstalling the
  package previously left the reports untouched, so a corrected figure or caption
  silently did not reach the output.
- Report the number of fitted models correctly in the CorrectFirst report. It read
  a field name that no longer exists on the model object and so stated "Built
  models for 0 PTM sites" on every run.
- Draw the CorrectFirst PCA as a static figure instead of an undersized plotly
  widget that left a band of empty page beneath it.
- Describe what each section of the CorrectFirst report does, which files the
  analysis writes and where to find them, and report the counts as prose and
  tables instead of raw console output.
- Accept sample annotations that spell the control column `CONTROL` as well as
  `Control`, and stop with a clear message when an annotation carries the expected
  columns but marks no control and treatment groups, instead of deriving an empty
  set of contrasts and failing later.
- Build the kinase-library MEA inputs from the combined `PTM_results.xlsx`, the
  workbook PTM-SEA and the KinaseLib GSEA already read, instead of the raw
  per-analysis workbooks. All three enrichment analyses now share one input,
  one column convention and one place where the ranking statistic is declared
  (`stat_column` in `ptm_config.yaml`). The generated `.rnk` and seqwindow files
  are unchanged.
- Render every per-analysis report into its own intermediates directory instead
  of the shared working directory. Running the report rules with `-j2` or more
  previously let the three analysis types overwrite each other's knitr
  intermediates, so all three N-to-C, seqlogo, PTM-SEA, MEA or KinaseLib reports
  could end up containing the same analysis. Parallel runs are now safe.
- Derive the DPU kinase-library input from the usage statistics of the DPU
  workbook (`tstatistic_I`, `diff_diff`, `FDR_I`) instead of its site
  statistics, which are identical to the DPA ones. DPU MEA tests differential
  PTM usage now and no longer duplicates the DPA result.
- Rerun the N-to-C, seqlogo and kinase-library preparation steps when
  `src/feature_preparation.R` changes, by declaring it as a rule input.
- Rank the kinase-library MEA input files by the moderated t-statistic
  (`statistic.site`), the statistic the `.rnk` column has always been named
  after and the one PTM-SEA and the KinaseLib GSEA already use. The files were
  ranked by the log2 fold change (`diff.site`) before, so all three enrichment
  analyses now share one ranking statistic and MEA results change accordingly.
- Support prolfqua DEA outputs whose YAML declares a sample column other than
  `Name`, including the current `sampleName` schema.
- Prefer templates from an editable source checkout over stale copies retained
  in a virtual environment.
- Use the supported `LFQData` accessors from prolfqua 1.7 for CorrectFirst
  phosphosite normalization.
- Impute a separate copy of CorrectFirst data for PCA when phosphosites contain
  missing measurements; statistical modeling continues to use the original data.
- Match FASTA-style total-proteome identifiers to bare phosphosite UniProt
  accessions, with a one-to-one mapping check before protein correction.
- Recover exact FragPipe single-site positions and sequence windows from the
  preserved DEA input so DPA, DPU, CorrectFirst, and kinase analyses share the
  same validated site metadata.
- Recognize the current prolfqua `WaldTest` contrast label as a fitted moderated
  linear model instead of discarding all CorrectFirst results.
- Preserve the canonical `protein_Id` column in CorrectFirst exports when site
  annotations are added, enabling N-to-C grouping and combined output.
- Began tracking user-visible changes in `CHANGELOG.md`. For changes before this version, see the git history.
