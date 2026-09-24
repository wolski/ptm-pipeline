---
title: CLI reference
---

# CLI reference

The project CLI exposes three command groups: `init`, `run` and `clean`. A bare `ptm-pipeline` shows help, and so does a bare group.

## Commands

--8<-- "README.md:cli-commands"

## Running to a depth

`run` is not all-or-nothing. Each depth stops at a natural boundary and writes its own archive, so a long analysis can be handed over, inspected or resumed without recomputing what is already done.

| Command | Stops after | Archive |
|---|---|---|
| `ptm-pipeline run stats` | `PTM_statistics.h5mu` | `<dir_out>_statistics.zip` |
| `ptm-pipeline run gsea` | `PTM_results.h5mu` and its enrichment artifacts | `<dir_out>_enrichment.zip` |
| `ptm-pipeline run` | reports, index and the Excel delivery | `<dir_out>.zip`, plus one archive per DEA input folder |

The depths are nested: `run gsea` includes everything `run stats` computes, and `run` includes both. Running a deeper target after a shallower one reuses the completed stages rather than repeating them, because Snakemake resolves them by file.

`<dir_out>_statistics.zip` carries `PTM_inputs.h5mu` beside the statistics container. `<dir_out>_enrichment.zip` carries the final MuData together with its per-analysis enrichment artifacts, which it names by relative path — the two travel together or neither can be read.

## Planning a run

`ptm-pipeline run dry` prints the jobs a run would execute and changes nothing. It plans the full workflow by default; `--target stats` or `--target gsea` plans one of the shallower depths.

```bash
ptm-pipeline run dry                    # plan the full workflow
ptm-pipeline run dry --target stats     # plan only up to the statistics archive
```

## Cleaning up

`clean` removes the outputs Snakemake declares and leaves the initialization files in place, so a project can be rerun without being set up again. `clean init` does the opposite, and `clean all` does both, outputs first. All three leave DEA input folders alone.

There is no `update` command. To refresh an initialized project with the current template, review its `ptm_config.yaml` and run `ptm-pipeline init --force`.

## Under Docker

The wrapper script takes the same commands, with the project directory as an argument:

```bash
./ptm-pipeline.sh init default DEA_data/ output/
./ptm-pipeline.sh run output/
```
