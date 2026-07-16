.PHONY: install lint format test run-api run-ui migrate compose-up compose-down

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .

format:
	ruff format .

test:
	pytest

migrate:
	alembic upgrade head

run-api:
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

run-ui:
	streamlit run streamlit_app/main.py

compose-up:
	docker compose up --build

compose-down:
	docker compose down
