# ── livecheck Makefile ────────────────────────────────────────────────────────
# Usage:
#   make test        run tests
#   make lint        ruff + mypy
#   make build       build wheel + sdist
#   make publish     upload to PyPI
#   make clean       remove build artefacts

.PHONY: test lint fmt build publish clean install dev-install docs

PYTHON    := python
PIP       := pip
PACKAGE   := livecheck
DIST      := dist/
BUILD     := build/

## Install for development
dev-install:
	$(PIP) install -e ".[dev]"

## Install (production)
install:
	$(PIP) install .

## Run test suite
test:
	pytest tests/ -v --tb=short

## Run tests with coverage
cov:
	pytest tests/ -v --cov=$(PACKAGE) --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

## Lint (ruff)
lint:
	ruff check $(PACKAGE)
	mypy $(PACKAGE) --ignore-missing-imports

## Format (ruff)
fmt:
	ruff format $(PACKAGE) tests/
	ruff check --fix $(PACKAGE)

## Build wheel + sdist
build: clean
	$(PYTHON) -m build
	twine check dist/*

## Publish to TestPyPI
test-publish: build
	twine upload --repository testpypi dist/*

## Publish to PyPI
publish: build
	twine upload dist/*

## Remove build artefacts
clean:
	rm -rf $(DIST) $(BUILD) *.egg-info .coverage htmlcov/ .pytest_cache/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete

## Count patterns
patterns:
	@$(PYTHON) -c "import sys; sys.path.insert(0,'.'); from livecheck import list_patterns; print(len(list_patterns()), 'patterns')"

## Show package version
version:
	@$(PYTHON) -c "import sys; sys.path.insert(0,'.'); import livecheck; print(livecheck.__version__)"

## Interactive demo
demo:
	@$(PYTHON) -c "
from livecheck import validate, explain, suggest, generate, debug_rule
print('=== validate ===')
validate('alice@example.com', 'must be a valid email')
print('alice@example.com — PASS')
print()
print('=== explain ===')
print(explain('must be a valid password'))
print()
print('=== suggest ===')
print(suggest(42))
print()
print('=== generate ===')
print([generate('must be a valid email') for _ in range(3)])
"
