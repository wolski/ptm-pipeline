---
title: Imputation, modelling and reporting
---

# Imputation, modelling and reporting

Decision: every analysis is computed from all models, imputed or not, and reports, counts and the proptm3d viewer are to show only rows whose site-level estimate is not imputed. Today they still show all rows; see the implementation status at the end.

## Terms

| Term | Meaning |
|:--|:--|
| `lm_impute` | prolfqua's model: one `lm` per feature. A feature whose `lm` cannot be fitted, because a group has no observation or fewer than two residual degrees of freedom remain, is refitted with its missing values at the limit of detection (LOD) and a variance borrowed from the fitted features. Its rows carry `estimate_type == "lod_imputed"`; all others `"observed"`. |
| `imputedData` | Layer written by prolfquapp >= 2.10.5 for an `lm_impute` DEA: `transformedData` with every missing cell filled by `predict()` of the feature's model, through `prolfqua::impute_from_model()`. Decoys are not modelled and stay NA. |
| route `complete` | No cell is missing. |
| route `fitted` | The missing cells come from the feature's `lm` fitted on its observed values. |
| route `lod_refit` | The missing cells come from the LOD refit. |
| `imputation` | varm block beside `imputedData` with `n_observed` and `n_imputed` per feature; each feature's route is in `uns/prolfquapp/varm_annotations/imputation/route`. |
| `n_protein_imputed` | CorrectFirst result column: how many of the corrected values in a row's fit used an imputed protein value. |

## CorrectFirst variants

All three correct `site − protein + median_s`, where `median_s` is the sample's median observed protein abundance, and fit the right-hand side of the model formula the DEAs recorded (`uns$prolfquapp$formula`). Each variant produces a layer of corrected abundances, samples × sites, and a results table.

| Variant | Result key | Protein values | Site values | Model on corrected values | Sites with a value in the layer |
|:--|:--|:--|:--|:--|:--|
| CF | `correct_first` | observed; a sample drops when its protein is missing there | observed | `lm_impute` | n_CF: site and protein observed in at least one common sample |
| A | `correct_first_protein_imputed` | `imputedData`, imputed with prolfqua `lm_impute` | observed | `lm_impute` | n_A: every site whose protein the protein DEA modelled |
| B | `correct_first_site_protein_imputed` | `imputedData`, imputed with prolfqua `lm_impute` | `imputedData`, imputed with prolfqua `lm`: fitted values fill sporadic gaps; a site missing a whole group, or with fewer than two residual degrees of freedom, stays missing | none: not fitted, layer only | n_B = n_A: B fills gaps only in sites that already have observed values |

CF and A results count their imputed protein values in `n_protein_imputed`; an imputed protein value leaves a row `observed`, as for DPU. B is not fitted: its filled site values are the site model's own predictions, so a fit on them would count them as observations and reuse the site's data. B is kept as its layer, for work that needs complete values, such as heatmaps, PCA or clustering.

Expected sizes:

- Sites: n_CF ≤ n_A = n_B ≤ n_sites, the sites of `enriched`; the n_A sites are the site axis of `enriched_CF`
- n_CF = n_A when no protein value is missing, as in the benchmark simulations
- n_B < n_sites when a site's protein was not modelled by the protein DEA; no variant corrects such a site
- Values per layer: CF ≤ A ≤ B; A fills the protein side, B also the sporadic site gaps

## Where the layers go

All of CorrectFirst lives in the `enriched_CF` modality, which replaces `cf`. It has its own sites: those of `enriched` whose protein the proteome quantified, n_A of them, in the enriched order, and it lines up with `enriched` by site id. Every matrix has the modality's shape, n_samples × n_A; a site a variant does not correct is an all-NA column in its matrix and `FALSE` in its results' `__present` mask.

| Slot | Content | Sites with a value in o43037 |
|:--|:--|:--|
| `var` | the sites of `enriched` whose protein the proteome quantified | 26,201 |
| `X` | CF | 25,349 |
| `layers/correct_first_protein_imputed` | A | 26,201 |
| `layers/correct_first_site_protein_imputed` | B, not fitted | 26,201 |
| `varm/<key>__<contrast>`, `__present` | results of CF and A | as the matrices |
| `uns/prophosqua` | CF report data | – |

`enriched` keeps the site DEA's own layers and the DPA and DPU results.

## What is computed and what is shown

| Analysis | Computed from | Shown in reports, counts and proptm3d |
|:--|:--|:--|
| DPA | site `lm_impute` models, imputed and not | rows whose site `estimate_type` is `observed` |
| DPU | site and protein `lm_impute` models, imputed and not | rows whose site `estimate_type` is `observed`; the protein estimate may be imputed |
| CF, A | `lm_impute` on the corrected values | rows whose `estimate_type` is `observed`: no LOD refit in the CF model; the protein value may be imputed |
| B | not fitted | nothing; B is its layer only |

A and B are stored in `PTM_statistics.h5mu` and `PTM_results.h5mu` only; no report, workbook or viewer shows them yet.

## Implementation status

| Decision | Status |
|:--|:--|
| prolfquapp writes `imputedData` and `imputation` (schema 2.1.0) | done, prolfquapp 2.10.5 |
| CF, A and B computed with the DEA formula | done, prophosqua |
| Where the layers go | done: `enriched_CF` with its own sites, prophosqua |
| CF and A rows count their imputed protein values; B is its layer only | done, prophosqua |
| Reports show and count only non-imputed site estimates | to do; the reports show all rows today |
| proptm3d shows and counts only non-imputed site estimates | to do; proptm3d still reads `mod/cf`, and today it shows all rows with an Estimate filter (default All), counts imputed rows in "Sites with results", and flags a row as imputed when the site or the protein estimate is |
| Non-imputed rows of `lm_impute` equal those of `lm` | open: `diff` and `df` are identical; `std.error`, `statistic`, `p.value` and `FDR` differ (in a 300-protein simulation by up to 0.02, 0.12, 0.007 and 0.14), because the imputed rows enter the empirical-Bayes variance prior and the FDR adjustment |
