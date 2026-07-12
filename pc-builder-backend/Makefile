.PHONY: install run test lint format migrate revision docker-up docker-down openapi

install:
	python -m pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

test:
	pytest -q --cov=app --cov-report=term-missing

lint:
	ruff check .

format:
	ruff format .
	ruff check . --fix

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(m)"

docker-up:
	docker compose up --build

docker-down:
	docker compose down

openapi:
	python scripts/export_openapi.py
