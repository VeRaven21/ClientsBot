up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build 

rebuild:
	docker-compose down
	docker-compose build 
	docker-compose up -d

migrate:
	docker-compose exec bot uv run alembic -c /app/database/alembic.ini upgrade head

migration:
	docker-compose exec bot uv run alembic -c /app/database/alembic.ini revision --autogenerate -m "$(name)"