.PHONY: setup test run seed lint clean

setup:            ## create the virtualenv and install dependencies
	python3 -m venv .venv
	.venv/bin/pip install --quiet --upgrade pip
	.venv/bin/pip install --quiet -r requirements.txt
	@echo "Done. Now run: make test"

test:             ## run the whole test suite (this is the one command that matters)
	.venv/bin/python -m pytest

run:              ## start the API on http://127.0.0.1:8000 (docs at /docs)
	.venv/bin/uvicorn app.main:app --reload

seed:             ## rebuild data/libraries.csv from the generator
	.venv/bin/python scripts/generate_data.py

clean:
	rm -rf .venv .pytest_cache app/__pycache__ tests/__pycache__ **/__pycache__ app.db
