---
name: fix-ptm-pipeline
description: Decide where a fix to the FGCZ PTM phosphoproteomics Snakemake pipeline belongs, and land it there instead of in the generated files of an analysis work directory. Use when changing PTM pipeline behaviour, reports, or figures for an order — a wrong or missing column in PTM_results.xlsx, a missing site annotation (SequenceWindow, posInProtein, modAA), a column that arrives suffixed .x/.y, a broken, empty, or invisible figure in Result_DPU.html or an Analysis_n_to_c, seqlogo, PTMSEA, KinaseLib, or MEA report, a defect in the DPA/DPU or CorrectFirst report, a Snakemake rule that will not rerun after an upstream change, or a prophosqua edit that never reaches the output. Explains the ptm-pipeline / prophosqua / prolfquappPTMreaders / prolfquapp / prolfqua layer stack, that a work directory now holds no R code at all, why a difference between two readers must be fixed in the readers rather than absorbed downstream, and how to port a fix upstream, reinstall, re-sync, and verify it with a pipeline run.
---

# Fix the PTM pipeline at its owner, not in the work directory

A PTM analysis work directory contains **no fixable code at all**. `Snakefile`,
`helpers.py`, `Makefile` and `ptm.sh` are generated, and `ptm-pipeline update`
rewrites all four:

```python
# ptm_pipeline/init.py, copy_template_files()
copied_files.extend(copy_shell_wrapper(project_dir, dry_run=dry_run))
copied_files.extend(remove_legacy_src(project_dir, dry_run=dry_run))       # deletes src/
copied_files.extend(remove_legacy_wrappers(project_dir, dry_run=dry_run))  # deletes ptm_*.sh
```

Only `ptm_config.yaml` is preserved. A project initialised before ptm-pipeline
0.3.0 may still carry a `src/` directory and per-command `ptm_*.sh` wrappers;
`update` deletes both. If you find R code in a work directory, it is a leftover,
not the thing that runs.

## The layer stack

```
<order work dir>/                       e.g. o41874_<order>
  ptm_config.yaml                       THE ONLY project-owned file
  Snakefile, helpers.py, Makefile,      generated - never the fix location
  ptm.sh
        ^ ptm-pipeline init / update
ptm-pipeline/template/                  Snakefile, helpers.py, Makefile. Wiring only:
                                        rules, inputs/outputs, targets, config surface
        ^ calls ptm.sh <command>
prophosqua                              ALL the analysis and ALL the reports:
  R/*.R                                   computation, plotting, data preparation
  inst/application/CMD_*.R                one front end per pipeline step
  inst/application/*.Rmd                  every report template
  inst/application/bin/ptm.sh             the one wrapper every rule invokes
        ^ imports
prolfquappPTMreaders                    reading site-level search output;
                                        site annotation (modAA, posInProtein,
                                        SequenceWindow) at read time
        ^ imports
prolfqua / prolfquapp                   statistics, LFQData, ProteinAnnotation,
                                        Contrasts, models
```

**Since prophosqua 0.3.0 / ptm-pipeline 0.3.0 every report template lives in
prophosqua**, including the three that used to sit in `template/src/`:

| Report | Template |
|:--|:--|
| `Analysis_DPA_DPU.html` | `prophosqua/inst/application/Analysis_DPA_DPU.Rmd` |
| `Analysis_CorrectFirst_DEA.html` | `prophosqua/inst/application/Analysis_CorrectFirst_DEA.Rmd` |
| `index.html` | `prophosqua/inst/application/create_top_index.Rmd` |
| `Result_DPU.html` | `prophosqua/inst/application/_Overview_PhosphoAndIntegration_site.Rmd` |
| `Analysis_n_to_c`, `Analysis_seqlogo`, `PTMSEA_*`, `Analysis_KinaseLib_*`, `Analysis_MEA` | `prophosqua/inst/application/Analysis_*.Rmd` |

Confirm rather than assume — the Snakefile resolves every one of them at parse
time and will tell you the exact file:

```bash
Rscript -e 'cat(system.file("application", "Analysis_n_to_c.Rmd", package = "prophosqua"))'
```

## Decide the owner before editing anything

| Symptom | Owner | File |
|:--|:--|:--|
| Paths, contrasts, FDR/log2FC thresholds, `max_fig`, `run_kinase` for one order | work dir | `ptm_config.yaml` |
| Rule wiring, inputs/outputs, targets, config surface, zip/index | ptm-pipeline | `template/Snakefile`, `template/helpers.py` |
| DPA/DPU or CorrectFirst analysis logic | prophosqua | `R/compute_dpa_dpu.R`, `R/compute_cf_dea.R` |
| Combined-workbook contents, column selection | prophosqua | `R/combine_ptm_results.R` |
| DEA path resolution, reading a DEA workbook, site metadata recovery | prophosqua | `R/dea_io.R` |
| Enrichment computation | prophosqua | `R/ptmsea.R`, `R/compute_enrichment.R`, `R/prep_kinaselib.R`, `R/prep_ptmsigdb.R` |
| A step's CLI surface (arguments, defaults) | prophosqua | `inst/application/CMD_*.R` |
| Figure, caption, prose, or layout in any report | prophosqua | `inst/application/*.Rmd` |
| PTM plotting or data-preparation function those templates call | prophosqua | `R/plotNtoC.R`, `R/seqLogoDiff.R`, `R/feature_preparation.R`, `R/enrichment_visualization.R` |
| Site annotation missing, wrong, or shaped differently for one search engine | prolfquappPTMreaders | `R/site_row_annotation.R`, `R/preprocess_*.R` |
| `LFQData`, `ProteinAnnotation`, `Contrasts`, model fitting, moderation, imputation flags | prolfqua / prolfquapp | package `R/` |

## Two readers must not differ downstream

The pipeline reads site-level DEA output produced by several readers — FragPipe
TMT single-site and multi-site, FragPipe LFQ `combined_site_STY`, Spectronaut.
**They are required to return the same shape.** When a downstream step breaks
because one reader supplies something another does not — a column absent, a join
producing `modAA.x` / `modAA.y`, an annotation present for TMT and missing for
LFQ — the fix belongs in the readers, in the shared
`prolfquappPTMreaders:::site_row_annotation()`, and never in a downstream guard.

A downstream `drop_*`, `coalesce`, `any_of` or normalise wrapper that papers over
the difference is the wrong fix: it makes the next divergence silent instead of
loud. `compute_dpa_dpu()` deliberately does the opposite — it stops with

```
The phospho DEA result carries no site annotation ... rerun the DEA with the
current prolfquappPTMreaders.
```

rather than filling anything in. Keep it that way.

The site annotation itself is produced once, at read time, inside each reader's
`preprocess_*` function — after `LFQData$new()`, because it needs the collapsed
hierarchy keys back out of `lfqdata$data_long()`, and immediately before
`ProteinAnnotation$new()`, whose `row_annot` receives it. Windows are always cut
from the FASTA (what FragPipe ships disagrees between its own formats) and
positions come from the site index, not from FragPipe's `Start` column, which is
off by one for some sites.

## Workflow

Diagnosing in the work directory is fine and often fastest — that is where the
data and the failing render are. Only the **fix** has to move.

1. **Reproduce and locate.** Read the rule in `Snakefile`, then the log under
   `<dir_out>/<subdir>/logs/`. Identify the owning layer from the table above.
2. **Edit the owner.** If a `ptm-pipeline/template` file is involved, diff in
   **both** directions first — drift is not one-way, and the template sometimes
   holds the newer version:
   ```bash
   for f in Snakefile helpers.py Makefile; do diff -q <ptm-pipeline>/template/$f $f; done
   ```
3. **Log the change** where that repo requires it: `CHANGELOG.md` for
   `ptm-pipeline` (bullet under the current `pyproject.toml` version), `NEWS.md`
   for prophosqua / prolfquappPTMreaders / prolfqua / prolfquapp (bullet under the
   current `DESCRIPTION` version). Record the user-visible effect, not the
   implementation.
4. **Make it reachable.** An R package edit changes nothing until installed, and
   a reader edit changes nothing until the DEA is rerun:
   ```bash
   make -C <prophosqua> install            # runs document() first
   make -C <prolfquappPTMreaders> install  # then rerun both DEAs
   ```
5. **Sync the work directory** — always from the local checkout, since a
   `share/ptm-pipeline/template` copy inside a virtualenv can be stale:
   ```bash
   uv run --project <ptm-pipeline> ptm-pipeline update . --dry-run
   uv run --project <ptm-pipeline> ptm-pipeline update .
   ```
   Then prove the round trip: `Snakefile`, `helpers.py` and `Makefile` must match
   `<ptm-pipeline>/template/`.
6. **Verify with a run**, see below.

## Traps that cost real time

**A report can be up to date and still stale.** Anything a rule reads but does
not declare as an `input:` is invisible to Snakemake. Declare it, then prove the
propagation before believing it:

```bash
touch <the file the rule reads>
snakemake -n all          # must propose the cascade, not "Nothing to be done"
```

All 17 R rules declare the installed prophosqua's `Meta/package.rds`, so a
reinstall correctly reruns everything. Reader edits are *not* covered — they
reach the pipeline only through a rerun DEA.

**Every downstream report reads `PTM_results.xlsx`, not the RDS objects.** Which
columns reach the `DPA` / `DPU` / `CF` sheets is decided by the `site_annotation`
vector and the per-analysis `direct_cols` lists in
`prophosqua/R/combine_ptm_results.R`, and the select there **silently drops names
that are absent** (`existing <- select_spec[select_spec %in% names(data)]`). A
column can exist in `Result_DPU.xlsx` and be missing from every report. Check
`direct_cols` before suspecting the analysis. Sheet-level names also differ from
the analysis objects: DPU/CF export `diff.site` / `FDR.site` / `statistic.site`,
renamed from `diff_diff` / `FDR_I` / `tstatistic_I`. That column order is pinned
by a test, because people read the sheet as well as code.

**Imputation is flagged by `estimate_type`, not `modelName`.** Values are
`observed`, `lod_imputed`, `missing_fallback`. A manual colour or linetype scale
keyed on the old vocabulary silently renders points transparent or drops a
linetype rather than erroring.

**Never put `$...$` math in a `fig.cap`** for a bookdown HTML report. Pandoc
renders the caption to HTML and bookdown injects it unescaped into
`<img aria-label="...">`; the quote closes the attribute and megabytes of base64
land in the page as visible text. Keep typeset math inside the plot
(`expression(-log[10](FDR))`). Detect it with
`grep 'aria-label="[^"]*<span class="math' <report>.html` — must be 0.

**Verify a rendered report in a browser, not in the source.** Both defects above
pass a regex over the HTML and a check of the extracted PNGs. Serve the file
(`python3 -m http.server`) because headless browsers refuse `file:` URLs, append
a `?v=` cache-buster, and check `img.naturalWidth > 0`, a `body.scrollWidth`
close to the viewport, and no unexpected `<pre><code>##` blocks.

**Enrichment workbooks are outputs now.** The compute/report split means
`compute_ptmsea_*` and the kinase-library compute rules always write their
`.xlsx` and `.rds`, so the Snakefile declares them — unlike the old combined
rules, where an enrichment with no significant sets wrote nothing and a declared
output would have been a rule failure. Do not reintroduce a conditional export in
a compute step; guard the *report*, which is what
`has_ptmsea_results` / `has_gsea_results` still do.

**Editing `ptm.sh` has an `R CMD check` trap.** `R CMD check` puts a stub
`Rscript` on PATH that prints *"'Rscript' should not be used without a path"* and
exits 1, so any wrapper a test spawns must resolve R the way Writing R Extensions
§1.6 asks:

```bash
RSCRIPT="${R_HOME:+${R_HOME}/bin/}Rscript"
```

A test that passes under `devtools::test()` and fails under `R CMD check` is
usually this, not `R_TESTS`.

**prolfqua_fml R packages gate commits on Air and lintr.** `make hooks` sets
`core.hooksPath=.githooks`, and that pre-commit hook runs `air format` and
`lintr::lint_package()` as a hard gate. Air reformats as part of the commit — re-read
the file afterwards rather than assuming your diff is what landed; to confirm a
reformat is behaviour-preserving, compare *parsed* code, not text. And `.lintr`
pins some exclusions **by line number** (`"R/R6_ProteinAnnotation.R" = 297` in
prolfquapp), so moving a function definition breaks the gate on a file you did not
otherwise touch — update the number in the same commit.

## Verify the repair

A full run is ~15-25 min at `-j4`, so batch pending fixes into one run rather
than paying for several.

```bash
snakemake -n all                    # confirm the intended jobs, and only those
snakemake -j4 all
```

`snakemake --unlock` first if a previous run was interrupted. Prefer declaring
the missing input over reaching for `--forcerun`: a forced run fixes today's
output and leaves the blindness in place.

Use the tier targets when the fix is report-only: `snakemake -j4 reports`
re-renders without recomputing, which is what makes a caption fix cheap.

**Read the log, not the exit status.** A `snakemake ... | tail` pipeline reports
`tail`'s status, so a failed workflow can look like success:

```bash
L=$(ls -t .snakemake/log/*.snakemake.log | head -1)
grep -cE "Error in rule|WorkflowError" "$L"   # must be 0
grep -E "steps \(100%\) done" "$L"
```

Then confirm the artefact itself changed — size and mtime of the report, the
column present in the workbook, the figure visible in a browser — and deliver
the render into the project rather than validating a copy in a scratch
directory. `.xlsx` bytes always differ between runs (writexl embeds a
timestamp), so compare workbooks by content; `.rds` is byte-comparable.

## Related

- `proteomics-data-analysis/skills/run-ptm-pipeline/SKILL.md` — set up and run the pipeline, choose the reader for the
  phospho DEA, and read a run honestly. Use it for the run this skill's fix has
  to be verified by.
- `proteomics-data-analysis/skills/fix-prolfqua-dea-app/SKILL.md` — when the
  upstream DEA workunit itself is the problem, before its output reaches this
  pipeline.
- `phosphoproteomics-ptm-analysis` — what DPA, DPU and CorrectFirst *mean* and
  which prophosqua function computes them. This skill routes a fix to its owner;
  that one explains the analysis it is a fix to.
- `r-development` — for the prophosqua / prolfquappPTMreaders package edit itself.
- `bookdown` — for report rendering mechanics beyond the caption trap above.
