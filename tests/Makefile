# Integration tests: unzip, init, and run pipeline for each test dataset.
# Run from the tests/ directory:
#   make all       - unzip + init + run
#   make unzip     - unzip test datasets
#   make init      - initialize all test projects
#   make run       - run all pipelines
#   make clean     - remove PTM_* output dirs and unzipped data dirs
# Requires: ptm-pipeline installed
#
# Docker integration tests:
#   make docker-build                  - build image from ../Dockerfile
#   make docker-test                   - full Docker test (unzip + init + run + verify)
#   make docker-test IMAGE_REPO=ghcr.io/wolski/ptm-pipeline-ci IMAGE_VERSION=0.3.0

DATA_DIR   := data
ZIPS       := $(wildcard $(DATA_DIR)/*.zip)
DATA_DIRS  := $(basename $(ZIPS))
PTM_DIRS   := $(patsubst $(DATA_DIR)/%,$(DATA_DIR)/PTM_%,$(DATA_DIRS))

# Docker settings (overridable from CLI / CI)
IMAGE_REPO    ?= ptm-pipeline-ci
IMAGE_VERSION ?= local
IMAGE          = $(IMAGE_REPO):$(IMAGE_VERSION)
PTM_SH         = ../ptm-pipeline.sh --image-repo $(IMAGE_REPO) --image-version $(IMAGE_VERSION)

# --- Native targets ---

all: run

unzip:
	@for z in $(ZIPS); do \
		echo "Unzipping $$z ..."; \
		unzip -qo "$$z" -d $(DATA_DIR) || exit 1; \
	done

init: unzip
	@for d in $(DATA_DIRS); do \
		out=$(DATA_DIR)/PTM_$$(basename "$$d"); \
		echo "Initializing $$d -> $$out"; \
		ptm-pipeline init-default "$$d" "$$out" || exit 1; \
	done
	@echo "All test projects initialized."

run: init
	@for d in $(PTM_DIRS); do \
		echo "Running pipeline in $$d"; \
		ptm-pipeline run "$$d" || exit 1; \
	done
	@echo "All pipelines completed."

clean:
	rm -rf $(PTM_DIRS) $(DATA_DIRS)

# --- Docker targets ---

docker-build:
	docker build --platform linux/amd64 -t $(IMAGE) ..

docker-test: unzip docker-init docker-run docker-verify

docker-init:
	@for z in $(ZIPS); do \
		d=$${z%.zip}; \
		out=$(DATA_DIR)/PTM_$$(basename "$$d"); \
		echo "Docker init: $$d -> $$out"; \
		$(PTM_SH) init-default "$$d" "$$out" || exit 1; \
	done
	@echo "All Docker test projects initialized."

docker-run:
	@for d in $(PTM_DIRS); do \
		echo "Docker run: $$d"; \
		$(PTM_SH) run "$$d" || exit 1; \
	done
	@echo "All Docker pipelines completed."

docker-verify:
	@fail=0; \
	for d in $(PTM_DIRS); do \
		out=$$(grep "^dir_out:" "$$d/ptm_config.yaml" | awk '{print $$2}'); \
		if [ -d "$$d/$$out" ]; then \
			echo "  OK: $$d/$$out"; \
		else \
			echo "  FAIL: $$d/$$out missing"; \
			fail=1; \
		fi; \
	done; \
	if [ "$$fail" -ne 0 ]; then \
		echo ""; \
		echo "=== Some tests FAILED ==="; \
		exit 1; \
	fi; \
	echo ""; \
	echo "=== All tests passed ==="

help:
	@echo "Native targets:"
	@echo "  make all            unzip + init + run (native)"
	@echo "  make unzip          unzip test datasets"
	@echo "  make init           initialize all test projects"
	@echo "  make run            run all pipelines"
	@echo "  make clean          remove PTM_* output dirs and unzipped data dirs"
	@echo ""
	@echo "Docker targets:"
	@echo "  make docker-build   build image from ../Dockerfile"
	@echo "  make docker-test    full Docker test (unzip + init + run + verify)"
	@echo "  make docker-init    init test projects via Docker"
	@echo "  make docker-run     run pipelines via Docker"
	@echo "  make docker-verify  check that dir_out exists in each PTM_ dir"
	@echo ""
	@echo "Docker variables (overridable):"
	@echo "  IMAGE_REPO=$(IMAGE_REPO)  IMAGE_VERSION=$(IMAGE_VERSION)"

.PHONY: all unzip init run clean docker-build docker-test docker-init docker-run docker-verify help
