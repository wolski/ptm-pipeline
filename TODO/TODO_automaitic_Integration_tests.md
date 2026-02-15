
~/projects/ptm-pipeline/test_data

uv run create_test_PTM_example_analysis_v2.py
uv run create_test_p40060_DanielGao.py
uv run create_test_o40094_Fabienne.py

~/projects/ptm-pipeline/tests/data/BGS_Spectronaut_example

uv tool install ~/projects/ptm-pipeline/

uv tool install git+https://github.com/wolski/ptm-pipeline

ptm-pipeline init_default
make all