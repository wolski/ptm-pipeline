---
name: run-ptm-pipeline
description: Set up and run the FGCZ integrated PTM phosphoproteomics pipeline for an order with ptm-pipeline and Snakemake. Use this whenever a PTM or phospho analysis has to be produced or reproduced for an order — "run the PTM pipeline", "rerun order o4XXXX", "set up the integrated PTM analysis", "why is nothing rebuilding", "init the pipeline in this folder", "make all", "the run failed" — and also when the request only names its parts — ptm-pipeline init, ptm_config.yaml, contrasts, DPA/DPU/CorrectFirst, PTM_results.xlsx, index.html, PTMSEA, KinaseLib, MEA. Covers choosing the reader for the phospho DEA (FragPipe TMT single/multi-site, FragPipe LFQ combined_site_STY, Spectronaut), the site annotation the pipeline requires of that DEA, setting a second order up from an analogous one, init/validate/run, the data and reports tiers, running one step by hand with ptm.sh, reading a run log honestly, and what does and does not trigger a rerun.
---

# Run the integrated PTM pipeline

The pipeline turns **two finished prolfquapp DEA runs** into an integrated PTM
analysis: three statistical views of the same sites, kinase and site-set
enrichment for each, one HTML index, zips to deliver.

It re-quantifies nothing. Everything it reports is derived from the two DEA
workbooks, so a defect in the DEA output is a defect in every report downstream —
check the DEA first when numbers look wrong.

```
two DEA directories  ->  ptm-pipeline init  ->  snakemake all  ->  index.html + zips
   (prolfquapp)          (writes the workflow)   (58 jobs for a
                                                  6-contrast order)
```

## Before you start: does the input exist?

The pipeline needs two DEA output directories in the same folder:

| Input | Typical folder |
|:--|:--|
| Enriched phospho sample, **site level** | `DEA_*_WUphospho_*`, `DEA_*_WUcombined_*`, `DEA_*_*STY*` |
| Total proteome, **protein level** | `DEA_*_WUprot_*`, `DEA_*_WUtotal_*` |

```bash
ptm-pipeline info .          # what it discovers, before committing to anything
```

The commands below assume `ptm-pipeline` is on the PATH (`uv tool install`). From
a local checkout instead, prefix every one of them:
`uv run --project <ptm-pipeline checkout> ptm-pipeline ...` — which is also how to
run a version you are changing.

If a DEA run is missing or wrong, that is upstream work: use the
`prolfquapp-dea` skill, not this one. Both DEA runs must cover the **same
contrasts** — the pipeline pairs site and protein results per contrast, and a
contrast present on only one side yields rows it cannot pair.

## Choosing the reader for the phospho DEA

The `-s` value of the phospho DEA is where the quantification type enters, and
getting it wrong is the usual reason a DEA runs but produces something the
pipeline cannot use. The site-level readers live in **prolfquappPTMreaders**;
list them with
`Rscript -e 'names(prolfquappPTMreaders::prolfqua_preprocess_functions)'`.

| Quantification | The file to look for in the search output | `-s` |
|:--|:--|:--|
| FragPipe TMT, one site per row | `abundance_single-site_None.tsv` | `prolfquappPTMreaders.FP_singlesite` |
| FragPipe TMT, peptide-level multi-site | `abundance_multi-site_None.tsv` | `prolfquappPTMreaders.FP_multisite` |
| **FragPipe LFQ / DDA** | `combined_site_STY_79.9663.tsv` | `prolfquappPTMreaders.FP_combined_STY` |
| Spectronaut site report | site report `.tsv` | `prolfquappPTMreaders.BGS_site` |

The total proteome side is an ordinary protein-level DEA — `prolfquapp.MSSTATS`
for a FragPipe LFQ `MSstats.csv`, and whatever the search produced otherwise.

`FP_combined_STY` differs from the TMT readers in one visible way: it joins the
annotation by `SampleName` rather than by channel, so the dataset TSV for an LFQ
order names raw files, not TMT channels. Everything downstream of the reader is
the same — see below.

## The site annotation the pipeline requires

The phospho DEA workbook must carry, per site, `posInProtein`, `modAA` and
`SequenceWindow`. Without them `compute_dpa_dpu` stops immediately with

```
The phospho DEA result carries no site annotation ... rerun the DEA with the
current prolfquappPTMreaders.
```

That message means what it says: **the repair is upstream, not here.** The
annotation is produced at read time by
`prolfquappPTMreaders:::site_row_annotation()`, called from every site reader's
`preprocess_*` function, and handed to `ProteinAnnotation$new()` as `row_annot`;
from there it travels into the DEA workbook. Reinstall prolfquappPTMreaders and
rerun the DEA. Do not add the columns downstream — a reader that does not emit
them is the bug.

Two facts about the window that matter when it looks wrong:

- **It is always cut from the FASTA**, never taken from the search output, because
  what FragPipe ships disagrees between formats (a 15-mer in single-site, a
  peptide-style window in multi-site) and `combined_site_STY` ships none at all.
  A wrong window therefore means a wrong FASTA, not a wrong search export.
- **Decoys must be filtered, and the DEA yaml is where that is configured.**
  `processing_options.pattern_decoys` (`^REV_|^rev_`) reaches the reader; with it
  unset, `rev_` entries share cleaned protein ids and windows get cut out of
  reversed sequences. The symptom is a silent one: windows that validate as
  15-mers but are not centred on the modified residue.

TMT and LFQ readers emit this identically, on purpose, so no downstream step has
to know which quantification produced the sites. If you find yourself wanting to
special-case one of them, that is a reader defect — `fix-ptm-pipeline`.

## Setup

Work in the order directory itself; every command below assumes it as the
working directory.

```bash
# 1. preview, always
ptm-pipeline init . . --dry-run

# 2. initialise (interactive: asks for the two folders, the experiment name,
#    FDR, log2FC, max figures, whether to run kinase analysis)
ptm-pipeline init . .

# non-interactive, for CI or an unattended rerun
ptm-pipeline init-default . .
```

Init discovers the factorial annotation file and its contrasts by itself. It
writes `ptm_config.yaml`, `Snakefile`, `helpers.py`, `Makefile` and `ptm.sh`,
and nothing else — there is no `src/` and no R code in the project.

`ptm_config.yaml` carries the order-specific settings. The generated Makefile
passes that config and the generated `Snakefile` to Snakemake; use its targets
for the normal run.

```bash
make validate                      # 19 checks: files, R packages, tools
ptm-pipeline validate . --quick    # the 10 file/tool checks, no R package probing
```

Validate before running. It fails in seconds on a missing R package; the
pipeline would fail on it twenty minutes in.

## Run

```bash
make dry-run                       # read the plan first, every time
make all CORES=4                   # run through the supported Makefile interface
```

Those targets expand to the commands below. The explicit arguments show how the
order settings reach the workflow and are also useful when running a target the
Makefile does not expose:

```bash
snakemake -s Snakefile --configfile ptm_config.yaml -n all
snakemake -s Snakefile --configfile ptm_config.yaml -j4 all
```

A 6-contrast order is 58 jobs. Two completed orders over the same samples took
about 11 and 31 minutes with four workers; actual duration depends on the inputs
and machine load. Renders get per-rule intermediate directories, so four workers
are safe; the kinase-library motif scans are the memory-hungry step if the
machine is small.

Two tier targets exist because computing and reporting are separate rules:

```bash
snakemake -j4 data                 # everything that writes data products
snakemake -j4 reports              # everything that renders HTML from them
```

That split is the reason a caption fix costs a render and not a reanalysis.
Stage targets also exist for working through the pipeline piece by piece:
`dea`, `combine`, `n_to_c_all`, `seqlogo_all`, `ptmsea_all`, `kinaselib_all`,
`vis_mea_all`, `top_index`, `zip`.

If a previous run was interrupted, `snakemake --unlock` first.

## Read the log, not the exit status

`snakemake ... | tail` reports `tail`'s status, so a failed workflow can look
like a success. After any run:

```bash
L=$(ls -t .snakemake/log/*.snakemake.log | head -1)
grep -cE "Error in rule|WorkflowError" "$L"    # must be 0
grep -E "steps \(100%\) done" "$L"             # must be there
```

A failing rule's own log is under `<dir_out>/<subdir>/logs/` — read that, not
the Snakemake traceback, to see what the R step actually said.

## What you get

```
<dir_out>/                         # from ptm_config.yaml, e.g. PTM_<experiment>
├── index.html                     # start here; links every report
├── PTM_results.xlsx               # sheets DPA, DPU, CF + normalized abundances
├── PTM_results.rds
├── PTM_DPA/                       # differential PTM abundance
├── PTM_DPU/                       # differential PTM usage (+ Result_DPU.html)
└── PTM_CF_DPU/                    # CorrectFirst
    ├── Analysis_n_to_c.html, Analysis_seqlogo.html
    ├── PTMSEA/                    # site-set enrichment, report + workbook + rds
    └── KinaseLib/                 # motif enrichment, GSEA and MEA
```

`all` also produces **three** zips beside the directories — `<dir_out>.zip` and
one for each DEA directory — because the two DEA runs are delivered with the
integration, not separately.

**Every downstream report reads `PTM_results.xlsx`**, not the RDS objects. A
column missing from a report is usually missing from that workbook.

What the three analyses mean — and when DPU rather than DPA answers the
question — is the `phosphoproteomics-ptm-analysis` skill. In short: DPA is the
site-level DEA result with the protein-level result joined alongside; DPU tests
the site against its protein (difference of the two log2 fold changes); and
CorrectFirst corrects site abundances by protein abundance before modelling
instead of comparing two finished models.

## Run one step by hand

`ptm.sh` is the entry point every rule uses. It resolves the step's R code from
the installed prophosqua, so running a step by hand runs exactly what the
pipeline runs:

```bash
./ptm.sh help                      # the steps, read from the installation
./ptm.sh dpa_dpu --help            # one step's own options
./ptm.sh render --report Analysis_seqlogo.Rmd \
    --output_file Analysis_seqlogo.html --output_dir <dir_out>/PTM_DPA \
    xlsx_file=<dir_out>/PTM_results.xlsx sheet=DPA
```

Use it to try something out. Snakemake does not know about a file written this
way, so produce deliverables through the targets.

## What triggers a rerun

Rules declare the files they read, so the usual answer is "the right thing
happens" — but two cases surprise people:

- **Reinstalling prophosqua reruns every R rule**, all 17 of them, because each
  declares the installed package's `Meta/package.rds`. That is deliberate: a
  reinstall can change any function any rule reaches, and the alternative is a
  report that is up to date and wrong.
- **Rerunning a DEA rebuilds what the pipeline derives from it**, because the
  DEA workbooks are declared inputs.

Prefer declaring a missing input over `--forcerun`: forcing fixes today's output
and leaves the blindness in place. `--forceall` is almost never the right answer.

## A second order from an existing one

Two quantifications of the same samples (a TMT order and an LFQ/DDA order, say)
should end up with the same group names, the same contrast names and the same
`ptm_config.yaml` contrasts, so the two integrations can be read side by side.
The cheapest way there is to copy the sibling's inputs rather than regenerate
them:

1. Copy the sibling's dataset TSV and DEA config YAML. In the YAML change only
   `zipdir_name` and `project_spec.workunit_Id`; leave the processing options
   alone so the two runs differ in quantification and nothing else.
2. If the sample naming differs between quantifications — TMT channels versus raw
   file names — the dataset TSV has to be rebuilt for the new run names, but keep
   the **group labels** identical. Same groups means prolfquapp generates the same
   contrast names, which means `ptm_config.yaml` can be copied verbatim apart from
   `dir_out`, `phospho_dea_dir`, `protein_dea_dir` and `annot_file`.
3. Run both DEAs, then init and run the pipeline as above.

Sanity-check the parity afterwards on one site: the same `site` should get the
same `SequenceWindow` in both orders' `PTM_results.xlsx`.

## Traps worth knowing before they cost you an afternoon

- **`-s` on the command line overrides `software:` in the DEA YAML.** A copied
  sibling config can say `software: DIANN` while the run is in fact
  `prolfquapp.MSSTATS`; the YAML key is not what ran. Read the reader from the
  DEA log's parameter dump, not from the config.
- **Enrichment results move between runs.** PTM-SEA and the kinase-library GSEA
  set no seed, so two runs of identical code differ slightly in NES and in which
  sets clear the reporting cutoff. Do not treat a small change as evidence that
  something was fixed or broken.
- **`.xlsx` bytes always differ** between runs — writexl embeds a timestamp.
  Compare workbooks by content (read both and compare cells), not by checksum.
  `.rds` files are deterministic and can be compared byte for byte.
- **macOS `unzip` cannot read a zip over 4 GB** — it reports "start of central
  directory not found". Search outputs reach that size routinely. Use Python:
  `python3 -c "import zipfile;zipfile.ZipFile('x.zip').extractall('out')"`.
- **Docker runs a published prophosqua.** `./ptm-pipeline.sh` installs
  prophosqua from GitHub inside the image, so local prophosqua changes do not
  reach it until they are pushed.

## Configuration

`ptm_config.yaml`, the keys worth touching:

| Key | Meaning |
|:--|:--|
| `dir_out` | Output directory name |
| `fdr`, `log2fc` | Significance thresholds used throughout the reports |
| `max_fig` | Cap on per-report figures (n-to-c, seqlogo) |
| `run_kinase` | Set false to skip all kinase-library work |
| `contrasts` | The contrast names; must exist in both DEA runs |
| `annot_file` | Annotation the CorrectFirst model uses |
| `gsea.n_perm`, `gsea.min_size`, `gsea.max_size` | Enrichment parameters |
| `kinaselib.kin_type`, `.threshold`, `.permutations` | Motif scan and MEA |
| `ptmsigdb.keep_sources`, `.trim_to` | Which PTMsigDB sub-sources, window width |
| `threads.mea` | Threads for motif enrichment |

`analyses` maps the three analysis types to their sheet, subdirectory, input
workbook and ranking statistic. Changing it changes what the whole downstream
fan-out is keyed on — leave it alone unless that is the point.

## Docker, when there is no local R

```bash
./ptm-pipeline.sh init-default DEA_data/ output/
./ptm-pipeline.sh run output/
./ptm-pipeline.sh validate output/
```

## A full worked example

`references/worked-example.md` is two real orders of the same samples end to
end — a TMT one and an LFQ/DDA one: both DEA commands for each, the init
answers, the generated config, the run, and the stage-by-stage alternative. Read
it when setting up a new order and you want a concrete template rather than the
general shape.

## Related skills

- `prolfquapp-dea` — produce or fix the two DEA runs this pipeline reads.
- `proteomics-data-analysis/skills/fix-ptm-pipeline/SKILL.md` — something is
  wrong in a report, a column, or a rule:
  which layer owns the fix, and how to land it there instead of in the work
  directory.
- `phosphoproteomics-ptm-analysis` — what DPA, DPU and CorrectFirst mean and
  which one answers a given biological question.
