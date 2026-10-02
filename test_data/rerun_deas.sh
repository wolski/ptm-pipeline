#!/bin/bash
# Rerun the four source DEAs with the installed prolfquapp, from the inputs their
# earlier runs kept in Inputs_WU_*, into <project>/rerun/, so the
# create_test_*.py subsets carry the current AnnData.h5ad. Rerun whenever
# prolfquapp changes what it writes. The TMT example uses the DEAs of
# MiMB_ptm_pipeline_v2 as they are; rerun those with its run_dea.fish.
# Run from test_data/: ./rerun_deas.sh [YYYYMMDD]
set -euo pipefail

STAMP=${1:-20261002}
DEA=$(Rscript --vanilla -e "cat(system.file('application/CMD_DEA_V2.R', package = 'prolfquapp'))")

# Keeps only the named contrasts of a ContrastName/Contrast annotation, so the
# DEA fits no more contrasts than the test subset carries; any other annotation
# is copied as it is.
restrict_contrasts() {
    local annotation=$1 out=$2 keep=$3
    awk -F'\t' -v OFS='\t' -v keep="$keep" '
        NR == 1 {
            n = split(keep, kept, ",")
            for (i = 1; i <= n; i++) wanted[kept[i]] = 1
            for (i = 1; i <= NF; i++) { if ($i == "ContrastName") cn = i; if ($i == "Contrast") ct = i }
            print; next
        }
        cn && ct && $cn != "" && $cn != "NA" && !($cn in wanted) { $cn = "NA"; $ct = "NA" }
        { print }' "$annotation" > "$out"
}

# project, earlier DEA, workunit, reader, annotation, config, kept contrasts
run_dea() {
    local project=$1 earlier=$2 workunit=$3 reader=$4 annotation=$5 config=$6 keep=${7:-}
    local inputs="$project/$earlier/Inputs_WU_$workunit"
    local rerun="$project/rerun"
    local out="$rerun/DEA_${STAMP}_WU${workunit}_vsn"
    mkdir -p "$rerun"
    restrict_contrasts "$inputs/$annotation" "$rerun/${workunit}_$annotation" "$keep"
    # The pipeline reads the imputedData layer, which only lm_impute writes.
    sed -E 's/^(  model:).*/\1 lm_impute/; s/^(  model_missing:).*/\1 yes/' "$inputs/$config" > "$rerun/${workunit}_$config"
    echo "DEA $out"
    Rscript --vanilla "$DEA" -i "$inputs" -d "$rerun/${workunit}_$annotation" -y "$rerun/${workunit}_$config" \
        -w "$workunit" -s "$reader" -o "$out" --flat_outdir > "$out.log" 2>&1
}

BGS_CONTRASTS=no_ERK_vs_ERK,no_ERK_vs_ERK_at_NoRux

run_dea p40060_DanielGao DEA_20260113_WUcombined_STY_batch_vsn combined_STY_batch \
    prolfquappPTMreaders.FP_combined_STY combined_sty_dataset_with_batch.tsv config_phospho.yaml &
run_dea p40060_DanielGao DEA_20260113_WUtotal_proteome_batch_vsn total_proteome_batch \
    prolfquapp.MSSTATS dataset_with_batch.tsv config.yaml &
wait

# The Spectronaut reports are 0.9 and 4.7 GB; one at a time.
run_dea o40094_Fabienne DEA_20260109_WUphospho_ERK_vsn phospho_ERK \
    prolfquappPTMreaders.BGS_site phospho_annot_ERK_RUX.tsv config_no_miss.yaml "$BGS_CONTRASTS"
run_dea o40094_Fabienne DEA_20260109_WUprot_ERK_vsn prot_ERK \
    prolfquapp.BGS prot_annot_ERK_RUX.tsv config.yaml "$BGS_CONTRASTS"
echo "All four DEAs rerun."
