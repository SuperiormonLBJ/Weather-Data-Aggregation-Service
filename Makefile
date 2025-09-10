.PHONY: help install test test-unit test-integration test-coverage test-html clean lint format

help: ## Show this help message
	@echo "Weather Service - Available Commands:"
	@echo "====================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

test: ## Run all tests
	python -m pytest tests/ -v

test-unit: ## Run unit tests only
	python -m pytest tests/unit/ -v

test-integration: ## Run integration tests only
	python -m pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

test-html: ## Open coverage HTML report
	open htmlcov/index.html

test-watch: ## Run tests in watch mode
	python -m pytest tests/ -v --tb=short -f

test-parallel: ## Run tests in parallel
	python -m pytest tests/ -n auto

lint: ## Run linting
	flake8 app/ tests/
	black --check app/ tests/
	isort --check-only app/ tests/

format: ## Format code
	black app/ tests/
	isort app/ tests/

clean: ## Clean up generated files
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run: ## Run the application
	python -m uvicorn app.core.main:app --reload --host 0.0.0.0 --port 8000

run-tests: ## Run the custom test runner
	python run_tests.py
