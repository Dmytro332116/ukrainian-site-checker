.PHONY: help build up down restart logs shell db-shell redis-shell migrate test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "   Frontend: http://localhost:8080"
	@echo "   Backend:  http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

down: ## Stop all services
	docker-compose down

restart: down up ## Restart all services

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs
	docker-compose logs -f backend

logs-celery: ## View Celery worker logs
	docker-compose logs -f celery-worker

shell: ## Open shell in backend container
	docker-compose exec backend /bin/bash

db-shell: ## Open PostgreSQL shell
	docker-compose exec db psql -U postgres -d site_checker

redis-shell: ## Open Redis CLI
	docker-compose exec redis redis-cli

migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head

migration: ## Create new migration (use: make migration m="description")
	docker-compose exec backend alembic revision --autogenerate -m "$(m)"

test: ## Run tests
	docker-compose exec backend pytest

test-coverage: ## Run tests with coverage
	docker-compose exec backend pytest --cov=app --cov-report=html

clean: ## Clean up containers, volumes, and images
	docker-compose down -v
	docker system prune -f

setup: build up migrate ## Initial setup: build, start, and migrate
	@echo "✅ Setup complete!"
	@echo "   Open http://localhost:8080 to get started"

dev: ## Start services in development mode with logs
	docker-compose up

status: ## Show status of all services
	docker-compose ps

