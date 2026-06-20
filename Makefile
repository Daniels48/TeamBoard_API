CONTAINER=api
ALEMBIC = docker compose exec $(CONTAINER) alembic -c app/infrastructure/db/alembic.ini

revision:
	$(ALEMBIC) revision --autogenerate -m "$(m)"

seed:
	docker compose exec $(CONTAINER) python -m scripts.seed

upgrade:
	$(ALEMBIC) upgrade head

downgrade:
	$(ALEMBIC) downgrade -1

logs:
	docker compose logs -f

up:
	docker compose up -d --build

down:
	docker compose down
