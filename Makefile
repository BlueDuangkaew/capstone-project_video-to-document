PYTHON := venv/bin/python

.PHONY: help install test serve format

help:
	@echo "Usage: make <target>"
	@echo "  install    Create virtualenv & install deps"
	@echo "  test       Run pytest"
	@echo "  serve      Run the FastAPI app (local)"

install:
	python3 -m venv venv
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

serve:
	$(PYTHON) -m src.main --reload
