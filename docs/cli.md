---
title: CLI reference
---

# CLI reference

The project CLI exposes the command groups `init`, `run` and `clean`, and the commands `setup`, `update` and `upload`. A bare `ptm-pipeline` shows help, and so does a bare group.

## Commands

--8<-- "README.md:cli-commands"

## Setting up the AlphaFold cache

The proptm3d step of a full run reads the organism's AlphaFold structures and their precomputed structural context, which the pipeline does not download. `ptm-pipeline setup MOUSE` (or `HUMAN`) fills that cache once, by running `proptm3d cache context`; it takes several GB per organism.

| Run through | Cache |
|---|---|
| `ptm-pipeline` | `~/.cache/proptm3d`, shared by every project on the machine |
| `ptm-pipeline.sh` | `.cache/proptm3d` in the current folder, which the container mounts as `/work` |

A project without a cache, such as the CI test projects, sets `run_proptm3d: false` (`init default --no-proptm3d`): a full run then skips the proptm3d folder and bundle, and `upload` skips the bundle.

## Running to a depth

`run` is not all-or-nothing. Each depth stops at a natural boundary and writes its own archive, so a long analysis can be handed over, inspected or resumed without recomputing what is already done.

| Command | Stops after | Archive |
|---|---|---|
| `ptm-pipeline run stats` | `PTM_statistics.h5mu` | `<dir_out>_statistics.zip` |
| `ptm-pipeline run gsea` | `PTM_results.h5mu` and its enrichment artifacts | `<dir_out>_enrichment.zip` |
| `ptm-pipeline run` | reports, index, the Excel delivery and the proptm3d browser | `<dir_out>.zip`, one archive per DEA input folder, `proptm3d_<dir_out>-all.zip` |

The depths are nested: `run gsea` includes everything `run stats` computes, and `run` includes both. Running a deeper target after a shallower one reuses the completed stages rather than repeating them, because Snakemake resolves them by file.

`<dir_out>_statistics.zip` carries `PTM_inputs.h5mu` beside the statistics container. `<dir_out>_enrichment.zip` carries the final MuData together with its per-analysis enrichment artifacts, which it names by relative path — the two travel together or neither can be read.

## Planning a run

`ptm-pipeline run dry` prints the jobs a run would execute and changes nothing. It plans the full workflow by default; `--target stats` or `--target gsea` plans one of the shallower depths.

```bash
ptm-pipeline run dry                    # plan the full workflow
ptm-pipeline run dry --target stats     # plan only up to the statistics archive
```

## Cleaning up

`clean` removes the outputs Snakemake declares, among them the DEA zips and the proptm3d folder and bundle, and leaves the initialization files in place, so a project can be rerun without being set up again. `clean init` does the opposite, and `clean all` does both, outputs first. All three leave DEA input folders alone.

## Uploading to B-Fabric

`ptm-pipeline upload [DIR]` uploads the archives of a full run to the project's B-Fabric order, one workunit per archive. `init` asks for the order ID and a base workunit name (default: the experiment name; `init default` takes `--order-id` and `--workunit-name`) and writes them to `bfabric_upload.yaml`, kept apart from `ptm_config.yaml` so that changing them does not rerun the analysis. Each workunit is named by its archive's prefix and the base name:

| Archive | Workunit name | Application |
|---|---|---|
| `<dir_out>.zip` | `ptm_pipeline_<name>` | 431, PTM Pipeline |
| `proptm3d_<dir_out>-all.zip` | `proptm3d_<name>` | 434, proptm3d |
| phospho DEA zip | `DEA_enriched_<name>` | 438, DEA |
| total protein DEA zip | `DEA_total_<name>` | 438, DEA |
| total peptide DEA zip, when configured | `DEA_total_peptide_<name>` | 438, DEA |

The archive paths come from the project's `ptm_config.yaml`. Every archive is validated and every connection opened, with the saved credentials environment `app-431-ptm-pipeline`, before the first workunit is created; the command lists the archives and asks before uploading.

## Updating

`init` copies the Snakefile, `helpers.py` and `ptm.sh` into the project, and `run` uses those copies, so a new release reaches a project only when they are replaced. `ptm-pipeline update` does both halves:

1. installs the pushed commits from GitHub: prolfqua, prolfquapp and protsea with pak, prophosqua with its report vignettes built, and ptm-pipeline itself with `uv tool install --reinstall git+https://github.com/wolski/ptm-pipeline`; a package already at its pushed commit is skipped
2. with the newly installed tool, replaces the project's Snakefile, `helpers.py` and `ptm.sh`; `ptm_config.yaml` is kept
3. prints the jobs a run would now execute

```bash
ptm-pipeline update            # install the pushed commits, refresh this project, plan the run
ptm-pipeline update --no-install output/   # only refresh the project from the installed tool
```

Unpushed local commits are never installed. After a new prophosqua is installed, the plan reruns everything from `import_inputs`, because the installed package is an input of every prophosqua stage.

## Under Docker

The wrapper script takes the same commands, with the project directory as an argument:

```bash
./ptm-pipeline.sh init default DEA_data/ output/
./ptm-pipeline.sh run output/
```
