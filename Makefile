# ==============================================================================
# TelemetryFlow Python MCP Server Makefile - Python Implementation
# Version: 1.1.2
# ==============================================================================

# Build variables
PACKAGE_NAME := tfo-mcp
VERSION := 1.1.2
COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_DATE := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")
PYTHON_VERSION := $(shell python --version 2>&1 | cut -d ' ' -f 2)

# Directories
BUILD_DIR := build
DIST_DIR := dist
SRC_DIR := src
TESTS_DIR := tests

# Python tooling
PYTHON := python
PIP := pip
PYTEST := pytest
RUFF := ruff
MYPY := mypy
BLACK := black

# Default target
.DEFAULT_GOAL := help

# ==============================================================================
# DEVELOPMENT
# ==============================================================================

.PHONY: build
build: ## Build wheel package
	@echo "Building $(PACKAGE_NAME)..."
	@mkdir -p $(BUILD_DIR)
	$(PIP) install build
	$(PYTHON) -m build
	@echo "Build complete: $(DIST_DIR)/"

.PHONY: build-release
build-release: clean ## Build optimized release package
	@echo "Building release $(PACKAGE_NAME)..."
	$(PIP) install build
	$(PYTHON) -m build
	@echo "Release build complete: $(DIST_DIR)/"

.PHONY: run
run: ## Run the MCP server
	@echo "Running $(PACKAGE_NAME)..."
	tfo-mcp serve

.PHONY: run-debug
run-debug: ## Run the server in debug mode
	@echo "Running $(PACKAGE_NAME) in debug mode..."
	tfo-mcp serve --debug

.PHONY: install
install: ## Install the package
	@echo "Installing $(PACKAGE_NAME)..."
	$(PIP) install -e .
	@echo "Installation complete"

.PHONY: clean
clean: ## Clean build artifacts
	@echo "Cleaning..."
	@rm -rf $(BUILD_DIR) $(DIST_DIR)
	@rm -rf *.egg-info/ src/*.egg-info/
	@rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	@rm -rf htmlcov/ .coverage coverage.xml
	@rm -rf coverage-*.out coverage-*.html coverage-summary.txt
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete"

# ==============================================================================
# DEPENDENCIES
# ==============================================================================

.PHONY: deps
deps: ## Download dependencies
	@echo "Downloading dependencies..."
	$(PIP) install -e .
	@echo "Dependencies downloaded"

.PHONY: deps-dev
deps-dev: ## Install development dependencies
	@echo "Installing development dependencies..."
	$(PIP) install -e ".[dev]"
	pre-commit install
	@echo "Development dependencies installed"

.PHONY: deps-all
deps-all: ## Install all optional dependencies
	@echo "Installing all dependencies..."
	$(PIP) install -e ".[all]"
	pre-commit install
	@echo "All dependencies installed"

.PHONY: deps-update
deps-update: ## Update dependencies
	@echo "Updating dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -e ".[all]"
	@echo "Dependencies updated"

.PHONY: deps-refresh
deps-refresh: ## Refresh all dependencies (clean and re-download)
	@echo "Refreshing dependencies..."
	$(PIP) cache purge
	$(PIP) install --upgrade pip
	$(PIP) install --force-reinstall -e ".[all]"
	@echo "Dependencies refreshed"

.PHONY: deps-check
deps-check: ## Check for dependency vulnerabilities
	@echo "Checking dependencies for vulnerabilities..."
	@if command -v pip-audit >/dev/null 2>&1; then \
		pip-audit; \
	else \
		echo "pip-audit not installed. Run: pip install pip-audit"; \
	fi

.PHONY: deps-lock
deps-lock: ## Generate requirements lock file
	@echo "Generating requirements lock..."
	$(PIP) freeze > requirements.lock
	@echo "Lock file generated: requirements.lock"

.PHONY: deps-tree
deps-tree: ## Show dependency tree
	@echo "Dependency tree..."
	@if command -v pipdeptree >/dev/null 2>&1; then \
		pipdeptree; \
	else \
		echo "pipdeptree not installed. Run: pip install pipdeptree"; \
	fi

# ==============================================================================
# CODE QUALITY
# ==============================================================================

.PHONY: fmt
fmt: ## Format code
	@echo "Formatting code..."
	$(BLACK) $(SRC_DIR) $(TESTS_DIR)
	$(RUFF) check --fix $(SRC_DIR) $(TESTS_DIR)
	@echo "Code formatted"

.PHONY: fmt-check
fmt-check: ## Check code formatting
	@echo "Checking code format..."
	$(BLACK) --check $(SRC_DIR) $(TESTS_DIR)
	@echo "Code format check passed"

.PHONY: lint
lint: ## Run linters
	@echo "Running linter..."
	$(RUFF) check $(SRC_DIR) $(TESTS_DIR)
	@echo "Lint complete"

.PHONY: lint-fix
lint-fix: ## Run linters with auto-fix
	@echo "Running linter with auto-fix..."
	$(RUFF) check --fix $(SRC_DIR) $(TESTS_DIR)
	@echo "Lint fix complete"

.PHONY: typecheck
typecheck: ## Run type checking
	@echo "Running type check..."
	$(MYPY) $(SRC_DIR)
	@echo "Type check complete"

.PHONY: check
check: fmt-check lint typecheck ## Run all code quality checks
	@echo "All checks passed"

# ==============================================================================
# TESTING
# ==============================================================================

.PHONY: test
test: ## Run tests
	@echo "Running tests..."
	$(PYTEST) $(TESTS_DIR) -v
	@echo "Tests complete"

.PHONY: test-cov
test-cov: ## Run tests with coverage
	@echo "Running tests with coverage..."
	@mkdir -p $(BUILD_DIR)
	$(PYTEST) $(TESTS_DIR) -v --cov=$(SRC_DIR)/tfo_mcp --cov-report=html:$(BUILD_DIR)/htmlcov --cov-report=xml:$(BUILD_DIR)/coverage.xml --cov-report=term
	@echo "Coverage report: $(BUILD_DIR)/htmlcov/index.html"

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	$(PYTEST) $(TESTS_DIR)/unit -v
	@echo "Unit tests complete"

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	$(PYTEST) $(TESTS_DIR)/integration -v
	@echo "Integration tests complete"

.PHONY: test-e2e
test-e2e: ## Run E2E tests only
	@echo "Running E2E tests..."
	$(PYTEST) $(TESTS_DIR)/e2e -v
	@echo "E2E tests complete"

.PHONY: test-all
test-all: ## Run all tests (unit, integration, e2e)
	@echo "Running all tests..."
	$(PYTEST) $(TESTS_DIR) -v --tb=short
	@echo "All tests complete"

.PHONY: test-fast
test-fast: ## Run tests without slow markers
	@echo "Running fast tests..."
	$(PYTEST) $(TESTS_DIR) -v -m "not slow"
	@echo "Fast tests complete"

.PHONY: ci-test
ci-test: fmt-check lint typecheck test ## Run CI pipeline (format, lint, typecheck, test)
	@echo "CI pipeline complete"

# ==============================================================================
# CI-SPECIFIC TARGETS (GitHub Actions)
# ==============================================================================

.PHONY: ci-deps
ci-deps: ## Install dependencies for CI (no pre-commit hooks)
	@echo "Installing CI dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@echo "CI dependencies installed"

.PHONY: test-unit-ci
test-unit-ci: ## Run unit tests for CI with coverage output
	@echo "Running unit tests for CI..."
	$(PYTEST) $(TESTS_DIR)/unit -v --cov=$(SRC_DIR)/tfo_mcp --cov-report=xml:coverage-unit.xml --cov-report=term
	@echo "Unit tests complete"

.PHONY: test-integration-ci
test-integration-ci: ## Run integration tests for CI with coverage output
	@echo "Running integration tests for CI..."
	$(PYTEST) $(TESTS_DIR)/integration -v --cov=$(SRC_DIR)/tfo_mcp --cov-report=xml:coverage-integration.xml --cov-report=term
	@echo "Integration tests complete"

.PHONY: test-e2e-ci
test-e2e-ci: ## Run E2E tests for CI
	@echo "Running E2E tests for CI..."
	$(PYTEST) $(TESTS_DIR)/e2e -v
	@echo "E2E tests complete"

.PHONY: ci-build
ci-build: ## Build package for CI
	@echo "Building for CI..."
	$(PIP) install build
	$(PYTHON) -m build
	@echo "CI build complete"

.PHONY: deps-verify
deps-verify: ## Verify dependencies
	@echo "Verifying dependencies..."
	$(PIP) check
	@echo "Dependencies verified"

.PHONY: coverage-report
coverage-report: ## Generate merged coverage report
	@echo "Generating coverage report..."
	@if command -v coverage >/dev/null 2>&1; then \
		coverage combine coverage-unit.xml coverage-integration.xml 2>/dev/null || true; \
		coverage report; \
		coverage html -d coverage-html; \
		echo "Coverage report generated: coverage-html/index.html"; \
	else \
		echo "coverage not installed"; \
	fi

# ==============================================================================
# DOCKER
# ==============================================================================

DOCKER_IMAGE := telemetryflow-mcp-python
DOCKER_TAG := $(VERSION)

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) -t $(DOCKER_IMAGE):latest .
	@echo "Docker image built"

.PHONY: docker-run
docker-run: ## Run Docker container
	@echo "Running Docker container..."
	docker run --rm -it \
		-e ANTHROPIC_API_KEY \
		$(DOCKER_IMAGE):latest

.PHONY: docker-push
docker-push: ## Push Docker image
	@echo "Pushing Docker image..."
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push $(DOCKER_IMAGE):latest

.PHONY: docker
docker: docker-build docker-run ## Build and run Docker container

.PHONY: docker-compose-up
docker-compose-up: ## Start docker-compose services
	docker compose up -d

.PHONY: docker-compose-down
docker-compose-down: ## Stop docker-compose services
	docker compose down

.PHONY: docker-compose-full
docker-compose-full: ## Start all docker-compose services (including optional)
	docker compose --profile full up -d

.PHONY: docker-compose-logs
docker-compose-logs: ## Show docker-compose logs
	docker compose logs -f

# ==============================================================================
# CI/CD
# ==============================================================================

.PHONY: ci
ci: deps-dev fmt-check lint typecheck test ## Run CI pipeline
	@echo "CI pipeline complete"

.PHONY: ci-validate
ci-validate: ## Validate CI configuration
	@echo "Validating CI configuration..."
	$(PIP) check
	@echo "CI configuration valid"

# ==============================================================================
# RELEASE
# ==============================================================================

.PHONY: release
release: clean build-release ## Create release artifacts
	@echo "Creating release $(VERSION)..."
	@mkdir -p $(DIST_DIR)/release
	@cp $(DIST_DIR)/*.whl $(DIST_DIR)/release/ 2>/dev/null || true
	@cp $(DIST_DIR)/*.tar.gz $(DIST_DIR)/release/ 2>/dev/null || true
	@echo "Release artifacts created in $(DIST_DIR)/release"
	@ls -la $(DIST_DIR)/release/

.PHONY: publish
publish: ## Publish to PyPI
	@echo "Publishing to PyPI..."
	@if command -v twine >/dev/null 2>&1; then \
		twine upload $(DIST_DIR)/*; \
	else \
		echo "twine not installed. Run: pip install twine"; \
	fi

.PHONY: publish-test
publish-test: ## Publish to Test PyPI
	@echo "Publishing to Test PyPI..."
	@if command -v twine >/dev/null 2>&1; then \
		twine upload --repository testpypi $(DIST_DIR)/*; \
	else \
		echo "twine not installed. Run: pip install twine"; \
	fi

# ==============================================================================
# UTILITIES
# ==============================================================================

.PHONY: version
version: ## Show version information
	@echo "TelemetryFlow Python MCP Server (Python)"
	@echo "Version:        $(VERSION)"
	@echo "Commit:         $(COMMIT)"
	@echo "Build Date:     $(BUILD_DATE)"
	@echo "Python Version: $(PYTHON_VERSION)"

.PHONY: validate-config
validate-config: ## Validate configuration file
	@echo "Validating configuration..."
	tfo-mcp validate
	@echo "Configuration valid"

.PHONY: init-config
init-config: ## Generate default configuration file
	@echo "Generating configuration..."
	tfo-mcp init-config
	@echo "Configuration generated"

.PHONY: info
info: ## Show server information
	tfo-mcp info

.PHONY: docs
docs: ## Generate documentation
	@echo "Generating documentation..."
	@if command -v pdoc >/dev/null 2>&1; then \
		pdoc --html --output-dir docs/api $(SRC_DIR)/tfo_mcp; \
		echo "Documentation generated in docs/api/"; \
	else \
		echo "pdoc not installed. Run: pip install pdoc"; \
	fi

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	@echo "Starting documentation server..."
	@if command -v pdoc >/dev/null 2>&1; then \
		pdoc --http localhost:8080 $(SRC_DIR)/tfo_mcp; \
	else \
		echo "pdoc not installed. Run: pip install pdoc"; \
	fi

.PHONY: pre-commit
pre-commit: ## Run pre-commit hooks on all files
	@echo "Running pre-commit..."
	pre-commit run --all-files

.PHONY: pre-commit-update
pre-commit-update: ## Update pre-commit hooks
	@echo "Updating pre-commit hooks..."
	pre-commit autoupdate

# ==============================================================================
# SECURITY
# ==============================================================================

.PHONY: security-check
security-check: ## Run security checks
	@echo "Running security checks..."
	@if command -v bandit >/dev/null 2>&1; then \
		bandit -r $(SRC_DIR) -ll; \
	else \
		echo "bandit not installed. Run: pip install bandit"; \
	fi
	@if command -v safety >/dev/null 2>&1; then \
		safety check; \
	else \
		echo "safety not installed. Run: pip install safety"; \
	fi

.PHONY: audit
audit: deps-check security-check ## Run full security audit
	@echo "Security audit complete"

# ==============================================================================
# HELP
# ==============================================================================

.PHONY: help
help: ## Show this help message
	@echo "TelemetryFlow Python MCP Server - Python Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Environment Variables:"
	@echo "  ANTHROPIC_API_KEY              - Claude API key (required for running)"
	@echo "  TELEMETRYFLOW_MCP_DEBUG        - Enable debug mode"
	@echo "  TELEMETRYFLOW_MCP_LOG_LEVEL    - Log level (debug, info, warning, error)"
