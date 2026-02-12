# Makefile — developer shortcuts
# Usage: make <target>

.PHONY: install install-dev dev lint format test ingest clean

## Install production dependencies
install:
	pip install -r requirements.txt

## Install all dependencies (including dev/test tools)
install-dev:
	pip install -r requirements-dev.txt

## Start the development server with hot reload
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Start the production server
start:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

## Lint the codebase
lint:
	ruff check app/ tests/

## Auto-format the codebase
format:
	ruff format app/ tests/
	ruff check --fix app/ tests/

## Run all tests
test:
	pytest tests/ -v

## Pre-ingest documents from data/documents/ (optional — also done via /upload)
ingest:
	python -c "from app.services.ingest import ingest_directory; ingest_directory(save_to_disk=True)"

## Remove generated artefacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage
