.PHONY: install run test discover-fields fixtures clean

install:
	uv sync --extra dev

run:
	uv run uvicorn src.agent_tax.main:app --host 0.0.0.0 --port $${PORT:-8000} --reload

test:
	uv run pytest

discover-fields:
	uv run python -m agent_tax.scripts.discover_fields

fixtures:
	uv run python scripts/generate_sample_w2.py

clean:
	rm -rf .venv __pycache__ .pytest_cache **/__pycache__
