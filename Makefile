up:
	docker-compose up -d --build

down:
	docker compose down && docker network prune --force

run:
	docker compose up -d
