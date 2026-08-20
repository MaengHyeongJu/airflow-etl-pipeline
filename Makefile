.PHONY: init up down logs psql trigger backfill test

init:
	cp -n .env.example .env || true
	@echo "Edit .env (AIRFLOW_UID, FERNET_KEY, JWT secret) before running 'make up'"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

psql:
	docker compose exec postgres psql -U $${POSTGRES_USER:-postgres} -d datamart

trigger:
	docker compose exec airflow-scheduler airflow dags trigger etl_pipeline

backfill:
	docker compose exec airflow-scheduler airflow dags backfill etl_pipeline -s $(START) -e $(END)

test:
	cd generator && python3 -m pytest -q
