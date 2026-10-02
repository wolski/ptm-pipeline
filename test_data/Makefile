# Generate small test datasets from full source data, then zip for git.
# The o40094 and p40060 source DEAs are rerun first with ./rerun_deas.sh.
# Run from the test_data/ directory:
#   make all    - generate all test datasets
#   make zip    - zip test datasets into tests/data/*.zip
# Requires: uv

SCRIPTS = create_test_MiMB_ptm_pipeline_v2.py \
          create_test_o40094_Fabienne.py \
          create_test_p40060_DanielGao.py

TESTS_DATA  := ../tests/data
DATA_DIRS   := $(TESTS_DATA)/BGS_Spectronaut_DIA_example \
               $(TESTS_DATA)/FP_LFQ_example \
               $(TESTS_DATA)/FP_TMT_example
ZIPS        := $(addsuffix .zip,$(DATA_DIRS))

all: $(SCRIPTS)
	@echo "All test datasets generated."

$(SCRIPTS):
	uv run --no-project --with anndata $@

zip: $(ZIPS)
	@echo "All test datasets zipped."

$(TESTS_DATA)/%.zip: $(TESTS_DATA)/%
	cd $(TESTS_DATA) && rm -f $*.zip && zip -r $*.zip $*
	@echo "  Created $@"

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  all       Generate all test datasets (default)"
	@echo "  zip       Zip test datasets into tests/data/*.zip"
	@echo "  help      Show this help"

.PHONY: all zip help $(SCRIPTS)
