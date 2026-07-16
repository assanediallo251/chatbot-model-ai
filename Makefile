.PHONY: install lint format test run-api run-ui migrate compose-up compose-down

install:
	python3 -m pip install -e ".[dev]"

lint:
	python3 -m ruff check .

format:
	python3 -m ruff format .

test:
	python3 -m pytest

migrate:
	python3 -m alembic upgrade head

run-api:
	python3 -m uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8000

run-ui:
	python3 -m streamlit run streamlit_app/main.py

compose-up:
	docker compose up --build

compose-down:
	docker compose down
