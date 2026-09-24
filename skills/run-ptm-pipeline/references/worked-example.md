# Worked example: two orders end to end

The same samples analysed twice, once by TMT and once by LFQ/DDA (o41874, six
contrasts from a factorial design). Both integrated pipelines were completed on
2026-08-21. Part 1-6 is the TMT-phospho integration in full; part 7 is the LFQ
integration.

Paths are those orders'; the shape is every order's. All commands run from the
order directory.

## 1. The two DEA runs (upstream, prolfquapp)

These are not part of the PTM pipeline. They must exist first, and they must
cover the same contrasts.

Phospho, single-site level:

```bash
./prolfqua_dea.sh \
  -i input_phospho_tmt/o41874_TMT2_enriched_labile_locFilterOn \
  -d phospho_dataset_factorial_generated.tsv \
  -y phospho_singlesite_config.yaml \
  -w phospho_single_o41874 \
  -s prolfquappPTMreaders.FP_singlesite \
  -o DEA_20260814_PI41555_O41874_WUphospho_single_o41874_vsn \
  --flat_outdir
```

Total proteome:

```bash
./prolfqua_dea.sh \
  -i input_total_lfq/o41874_LFQ_FPcomplete_enriched_ddaplus \
  -d total_dataset_factorial_generated.tsv \
  -y total_config.yaml \
  -w total_o41874 \
  -s prolfquapp.MSSTATS \
  -o DEA_20260814_PI41555_O41874_WUtotal_o41874_vsn \
  --flat_outdir
```

The LFQ path on this first integration is not a paste error. Its phospho side is
the TMT single-site quantification, while the recorded protein-level DEA reads
`msstats.csv` from the matching LFQ `enriched_ddaplus` search output. Part 7
uses a different LFQ protein input, `total_ddaplus`; the two source directories
must not be substituted for one another just because both expose `msstats.csv`.

The `-s` value is the reader for the search engine and quantification type;
getting it wrong is the usual cause of a DEA that runs but reports nothing
useful. See the `prolfquapp-dea` skill.

## 2. Initialise the pipeline

Preview first:

```bash
uv run --project <ptm-pipeline checkout> \
  ptm-pipeline init . . --dry-run
```

Then for real. Answers used for this order:

```text
Phospho folder:  DEA_20260814_PI41555_O41874_WUphospho_single_o41874_vsn
Protein folder:  DEA_20260814_PI41555_O41874_WUtotal_o41874_vsn
Experiment name: Reg_vs_Ima_at_M100916
FDR threshold:   0.25
log2FC threshold: 0.5
Max n-to-c plots: 10
Run kinase activity analysis: yes
```

An FDR of 0.25 is deliberate here: it is a discovery-stage phospho analysis, and
0.05 left too few sites to say anything about enrichment. Choose it per order,
not by habit.

Init finds the factorial annotation and its six contrasts on its own and writes
`ptm_config.yaml`, `Snakefile`, `helpers.py`, `Makefile`, `ptm.sh`. The
interesting part of the generated config:

```yaml
dir_out: PTM_Reg_vs_Ima_at_M100916
max_fig: 10
run_kinase: true
fdr: 0.25
log2fc: 0.5
phospho_dea_dir: DEA_20260814_PI41555_O41874_WUphospho_single_o41874_vsn
protein_dea_dir: DEA_20260814_PI41555_O41874_WUtotal_o41874_vsn
annot_file: DEA_20260814_PI41555_O41874_WUphospho_single_o41874_vsn/Inputs_WU_phospho_single_o41874/phospho_dataset_factorial_generated.tsv
contrasts:
  - Reg_vs_Ima_at_M100916
  - Veh_vs_Ima_at_M100916
  - Veh_vs_Reg
  - Veh_vs_Reg_at_M100916
  - Veh_vs_Reg_at_M150207
  - interaction_Veh_vs_Reg_at_M150207_vs_M100916
```

Init is not needed for a rerun once `ptm_config.yaml` and `Snakefile` exist.

## 3. Validate

```bash
uv run --project <ptm-pipeline checkout> \
  ptm-pipeline validate . --quick
```

## 4. Run

```bash
make dry-run
make all CORES=4
```

The Makefile passes the generated workflow and the order-specific settings to
Snakemake. The equivalent direct commands are:

```bash
snakemake -s Snakefile --configfile ptm_config.yaml -n all
snakemake -s Snakefile --configfile ptm_config.yaml -j4 all
```

The commands above ran 58 jobs with four workers in about 11 minutes on a quiet
laptop. The result is `PTM_Reg_vs_Ima_at_M100916/index.html` and the zip beside
it.

Then confirm it actually succeeded:

```bash
L=$(ls -t .snakemake/log/*.snakemake.log | head -1)
grep -cE "Error in rule|WorkflowError" "$L"   # 0
grep -E "steps \(100%\) done" "$L"
```

## 5. Stage by stage, when working through a problem

In this order:

```bash
snakemake -j4 dea
snakemake -j4 combine
snakemake -j4 n_to_c_all
snakemake -j4 seqlogo_all
snakemake -j4 ptmsea_all
snakemake -j4 kinaselib_all
snakemake -j4 vis_mea_all
snakemake -j4 top_index
snakemake -j4 zip
```

Or by tier, which is usually what you want: `snakemake -j4 data` then
`snakemake -j4 reports`.

## 6. Delivering

`<dir_out>.zip` holds the reports and data products. It is large — for this
order 316 MB, most of it the saved analysis objects that let a report re-render
without a refit.

## 7. The same samples again, from LFQ/DDA

A second order over the same biology, quantified label-free. Working directory
`p41874_<order>_DDA/`, FragPipe LFQ output, phospho site file
`combined_site_STY_79.9663.tsv`.

Both DEA inputs differ from part 1. The phospho side uses the
`FP_combined_STY` reader and its dataset TSV names raw files instead of TMT
channels; the protein side uses the separate `total_ddaplus` search output.

```bash
./prolfqua_dea.sh \
  -i input_phospho_lfq/o41874_LFQ_FPcomplete_enriched_ddaplus \
  -d phospho_lfq_dataset.tsv \
  -y phospho_lfq_config.yaml \
  -w phospho_lfq_site_o41874 \
  -s prolfquappPTMreaders.FP_combined_STY \
  -o DEA_20260821_PI41555_O41874_WUphospho_lfq_site_o41874_vsn \
  --flat_outdir

./prolfqua_dea.sh \
  -i input_total_lfq/o41874_LFQ_FPcomplete_total_ddaplus \
  -d total_lfq_dataset.tsv \
  -y total_lfq_config.yaml \
  -w total_lfq_o41874 \
  -s prolfquapp.MSSTATS \
  -o DEA_20260821_PI41555_O41874_WUtotal_lfq_o41874_vsn \
  --flat_outdir
```

Both YAMLs are the TMT order's, copied, with `zipdir_name` and
`project_spec.workunit_Id` changed and nothing else. Note that
`total_lfq_config.yaml` still reads `software: DIANN` — the `-s` flag overrides
it, and the DEA log's parameter dump is what tells you which reader actually ran.

The phospho dataset TSV was taken from the TMT order verbatim (the group labels
are what matter, and they are the same); the total one was rebuilt for the LFQ
run names but with those same group labels. Same groups, so prolfquapp generated
the same six contrast names, so `ptm_config.yaml` is the TMT order's config with
only `phospho_dea_dir`, `protein_dea_dir` and `annot_file` changed:

```yaml
dir_out: PTM_Reg_vs_Ima_at_M100916
phospho_dea_dir: DEA_20260821_PI41555_O41874_WUphospho_lfq_site_o41874_vsn
protein_dea_dir: DEA_20260821_PI41555_O41874_WUtotal_lfq_o41874_vsn
annot_file: DEA_20260821_PI41555_O41874_WUphospho_lfq_site_o41874_vsn/Inputs_WU_phospho_lfq_site_o41874/phospho_lfq_dataset.tsv
```

Init, validate and run are then identical to parts 2-4: 58 jobs, completed with
four workers in about 31 minutes, with no rule behaving differently for LFQ
than for TMT.

Confirm the parity on one site rather than trusting it — the same site should get
the same window in both orders:

```r
x <- readxl::read_xlsx("<dir_out>/PTM_results.xlsx", sheet = "DPA")
subset(x, grepl("A0A1B0GTU1_S108", site), c(site, posInProtein, modAA, SequenceWindow))
# A0A1B0GTU1_S108~SVLPTVPEsPEEEVK   108   S   VLPTVPESPEEEVKA   -- in both orders
```

Sizes for this order, for planning disk: DEA phospho 759 MB, DEA total 548 MB,
integration 830 MB, and the three zips 466 / 152 / 593 MB. The FragPipe search
output zips are 11.8 GB and 5.3 GB, which macOS `unzip` refuses — extract them
with Python's `zipfile`.
