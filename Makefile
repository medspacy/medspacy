help:
	@echo "setup - sets up the repository"
	@echo "lint - check style with flake8"
	@echo "format - run black formatter"
	@echo "pre-commit - run linting and formatting"

setup:
	@echo -e "\n Installing dependencies in editable mode"
	@pip install -e .
	@echo -e "\n Installing pre-commit"
	@pre-commit install

pre-commit: format lint

lint:
	autoflake8 -r --exclude __init__.py medspacy tests

lint-check:
	autoflake8 -r -c --exclude __init__.py medspacy tests

format: 
	black medspacy tests

format-check:
	black --check medspacy tests
