help:
	@echo "lint - check style with flake8"
	@echo "format - run black formatter"
	@echo "test - run tests"

format: 
	black medspacy tests

lint:
	autoflake8 -r --exclude __init__.py medspacy tests