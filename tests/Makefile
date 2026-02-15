# Integration tests: unzip, init, and run pipeline for each test dataset.
# Run from the tests/ directory:
#   make all       - unzip + init + run
#   make unzip     - unzip test datasets
#   make init      - initialize all test projects
#   make run       - run all pipelines
#   make clean     - remove PTM_* output dirs and unzipped data dirs
# Requires: ptm-pipeline installed

DATA_DIR   := data
ZIPS       := $(wildcard $(DATA_DIR)/*.zip)
DATA_DIRS  := $(basename $(ZIPS))
PTM_DIRS   := $(patsubst $(DATA_DIR)/%,$(DATA_DIR)/PTM_%,$(DATA_DIRS))

all: run

unzip:
	@for z in $(ZIPS); do \
		echo "Unzipping $$z ..."; \
		unzip -qo "$$z" -d $(DATA_DIR); \
	done

init: unzip
	@for d in $(DATA_DIRS); do \
		out=$(DATA_DIR)/PTM_$$(basename "$$d"); \
		echo "Initializing $$d -> $$out"; \
		ptm-pipeline init-default "$$d" "$$out"; \
	done
	@echo "All test projects initialized."

run: init
	@for d in $(PTM_DIRS); do \
		echo "Running pipeline in $$d"; \
		ptm-pipeline run "$$d"; \
	done
	@echo "All pipelines completed."

clean:
	rm -rf $(PTM_DIRS) $(DATA_DIRS)

.PHONY: all unzip init run clean
