# Plan: proptm3d prepare, bundle and upload inside ptm-pipeline

A full `ptm-pipeline run` also prepares and bundles the proptm3d browser; a new `ptm-pipeline upload ORDER_ID WORKUNIT_NAME` uploads the PTM results, the proptm3d bundle and the DEA zips to B-Fabric. proptm3d keeps `prepare`, `bundle`, `serve` and `cache`, and loses `upload`.

## Blocker found

- B-Fabric application 438 ("DEA", type import, storage 2) is `enabled: false`; 431 (PTM_Pipeline) and 434 (proptm3d) are enabled. Uploads to 438 will likely be refused until it is enabled.

## ptm-pipeline: run

- Dependency: `proptm3d @ git+https://github.com/prolfqua/proptm3d` in `pyproject.toml`, like `kinase-library`
- Two Snakefile rules after `zip`, both in `rule all`; `run stats` and `run gsea` unchanged
- `prepare_proptm3d`: input `<dir_out>.zip`, output `proptm3d_<dir_out>/`, calls `proptm3d.prepare.prepare_gsea()` in a `run:` block (Python API, so no PATH dependence on the tool's entry points)
- `bundle_proptm3d`: output `proptm3d_<dir_out>-all.zip`, calls `proptm3d.bundle.bundle_prepared_root()`
- Names match what `proptm3d prepare` and `bundle` write by default today
- `clean` deletes both, since they become declared outputs
- Needs the organism's AlphaFold cache; the pipeline does not download it, prepare fails with a hint without it
- `ptm-pipeline setup HUMAN|MOUSE` runs `proptm3d cache context`: `~/.cache/proptm3d` natively, `<folder>/.cache/proptm3d` under `ptm-pipeline.sh` (`XDG_CACHE_HOME=/work/.cache`)
- `run_proptm3d: false` (`init --no-proptm3d`) skips both rules and the bundle upload; the CI test projects use it

## ptm-pipeline: upload

- `ptm-pipeline upload ORDER_ID WORKUNIT_NAME [DIRECTORY]`, artifacts taken from `ptm_config.yaml`, no discovery cache
- `<dir_out>.zip` → 431, `proptm3d_<dir_out>-all.zip` → 434, the DEA zips (phospho, protein, peptide) → 438
- Same order ID and workunit name for all, credentials environment `app-431-ptm-pipeline`, as proptm3d does now
- One workunit per archive, named `<prefix>_<name>`: `ptm_pipeline`, `proptm3d`, `DEA_enriched`, `DEA_total`, `DEA_total_peptide`; order ID and base name asked by `init`, stored in `bfabric_upload.yaml`
- Validate every artifact and connect before creating any workunit; list them and ask `[y/N]` before uploading
- Moved from proptm3d: `bfabric_upload.py` (artifact classes, `upload_artifacts`, progress), plus a `DeaArtifact` for 438; `bfabric[transfer]` becomes a ptm-pipeline dependency

## proptm3d: removal

- Delete the `upload` command, `bfabric_upload.py`, `upload_cache.py`, their tests and the `record_preparation`/`record_bundle` calls
- Drop `bfabric[transfer]` from its dependencies; keep `prepared_history` (bare `bundle` lists from it)
- README, AGENTS.md, docs, CHANGELOG

## Order and verification

- 1: proptm3d removal, its tests green, pushed (ptm-pipeline installs it from GitHub)
- 2: ptm-pipeline rules, `run dry` on `o43207_PhosphoLFQ`, then a full run there
- 3: upload command with unit tests on mocked bfabric; a real upload only on your go, after 438 is enabled

