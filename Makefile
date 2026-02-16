CONTAINER=api
ALEMBIC = docker compose exec $(CONTAINER) alembic -c app/db/alembic.ini

revision:
	$(ALEMBIC) revision --autogenerate -m "$(m)"

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
