.PHONY: check test lint version

check: lint test

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -t .

lint:
	python3 -m compileall -q src tests
	python3 scripts/check_no_prints.py src

version:
	python3 scripts/gen_version.py > src/inventory/_version.py
