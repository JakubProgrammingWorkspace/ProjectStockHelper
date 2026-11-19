OS:=$(shell uname -s)
USER_ID:=$(shell id -u)
GROUP_ID:=$(shell id -g)

-include .env
export
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

PROJECT_NAME ?= stock_helper

DOCKER=$(shell which docker)

DOCKER_COMPOSE=docker compose -f docker-compose.yml -p $(PROJECT_NAME)

.PHONY: generate-env
generate-env:
	@if [ -f .env ]; then cp -f .env .env.bak && echo "Existing .env backed up to .env.bak"; fi
	yes | cp -f .env.dist .env
ifeq ($(OS),Linux)
	sed -i -e 's/^UID=.*/UID=$(USER_ID)/g' .env
	sed -i -e 's/^GID=.*/GID=$(GROUP_ID)/g' .env
else
	sed -i '' 's/^UID=.*/UID=$(USER_ID)/g' .env
	sed -i '' 's/^GID=.*/GID=$(GROUP_ID)/g' .env
endif

.PHONY: initialize
initialize: generate-env build

#############################
# Build commands
#############################

.PHONY: build
build:
	$(DOCKER_COMPOSE) build

.PHONY: up
up:
	$(DOCKER_COMPOSE) up -d --remove-orphans --build

.PHONY: down
down:
	$(DOCKER_COMPOSE) down --remove-orphans

.PHONY: sh
sh:
	$(DOCKER) exec -it $(PROJECT_NAME)_web /bin/sh

.PHONY: sh-react
sh-react:
	$(DOCKER) exec -it $(PROJECT_NAME)_react /bin/sh

# if with parameters then use like: make uv -- -D
ifeq (uv,$(firstword $(MAKECMDGOALS)))
  UV_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(UV_ARGS):;@:)
endif

.PHONY: uv
uv:
	$(DOCKER) exec $(PROJECT_NAME)_web uv $(UV_ARGS)


ifeq (npm,$(firstword $(MAKECMDGOALS)))
  NPM_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(NPM_ARGS):;@:)
endif

.PHONY: npm
npm:
	$(DOCKER) exec $(PROJECT_NAME)_react npm $(NPM_ARGS)

.PHONY: build-frontend
build-frontend:
	$(DOCKER) exec $(PROJECT_NAME)_react npm run build

.PHONY: copy-frontend
copy-frontend: build-frontend
	rm -f config/templates/index.html
	rm -rf static/*
	cp -f frontend/build/index.html config/templates/index.html
	cp -rf frontend/build/. static/
	rm -f static/index.html

#############################
# Lint commands
#############################

.PHONY: lint
lint:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run ruff check .

.PHONY: lint-fix
lint-fix:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run ruff check . --fix

.PHONY: lint-intensified-check
lint-intensified-check:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run ruff check --select D,N apps/

.PHONY: check-dupes
check-dupes:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run pylint --rcfile=pyproject.toml apps/

.PHONY: check-unused
check-unused:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run vulture apps/ config/ manage.py --min-confidence 80

.PHONY: format
format:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run ruff format .

#############################
# Test commands
#############################

.PHONY: test-unit
test-unit:
	$(DOCKER) exec -e DJANGO_SETTINGS_MODULE=config.settings.test $(PROJECT_NAME)_web uv run pytest -m "not django_db"

.PHONY: test-integration
test-integration:
	$(DOCKER) exec -e DJANGO_SETTINGS_MODULE=config.settings.test $(PROJECT_NAME)_web uv run pytest -m django_db

.PHONY: test-backend
test-backend:
	$(DOCKER) exec -e DJANGO_SETTINGS_MODULE=config.settings.test $(PROJECT_NAME)_web uv run pytest

.PHONY: run-tests
run-tests: test-backend

.PHONY: test-frontend
test-frontend:
	$(DOCKER) exec $(PROJECT_NAME)_react npm run test

.PHONY: test-frontend-watch
test-frontend-watch:
	$(DOCKER) exec $(PROJECT_NAME)_react npm run test:watch

.PHONY: test-e2e
test-e2e:
	$(DOCKER_COMPOSE) up --abort-on-container-exit --exit-code-from test-e2e test-e2e

.PHONY: test
test: test-backend test-frontend

#############################
# Django commands
#############################

.PHONY: create-migrations
create-migrations:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run manage.py makemigrations

.PHONY: create-migrations-dry-run
create-migrations-dry-run:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run manage.py makemigrations --check --dry-run

.PHONY: execute-migrations
execute-migrations:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run manage.py migrate

.PHONY: fetch-tickers
fetch-tickers:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run manage.py fetch_tickers sec_tickers
	$(DOCKER) exec $(PROJECT_NAME)_web uv run manage.py fetch_tickers process_tickers

.PHONY: fetch-sec-financial
fetch-sec-financial:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run manage.py fetch_sec_financial_data

.PHONY: fetch-prices
fetch-prices:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run manage.py fetch_historical_prices --source yfinance

.PHONY: fetch-demo-prices
fetch-demo-prices:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run manage.py fetch_demo_prices

.PHONY: fetch-bulk-historical-prices
fetch-bulk-historical-prices:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run manage.py fetch_bulk_historical_prices

.PHONY: fetch-all-bulk-historical-prices
fetch-all-bulk-historical-prices:
	$(DOCKER) exec $(PROJECT_NAME)_web uv run manage.py fetch_bulk_historical_prices --all_range


#############################
# Database commands
#############################

.PHONY: dump-db
dump-db:
	$(DOCKER) exec -e PGPASSWORD=$(DATABASE_PASSWORD) $(PROJECT_NAME)_postgres pg_dump -U $(DATABASE_USER) $(DATABASE_NAME) > full_backup.sql

.PHONY: dump-table
dump-table:
	$(DOCKER) exec -e PGPASSWORD=$(DATABASE_PASSWORD) $(PROJECT_NAME)_postgres pg_dump -U $(DATABASE_USER) -t $(filter-out $@,$(MAKECMDGOALS)) $(DATABASE_NAME) > table_backup_$(filter-out $@,$(MAKECMDGOALS)).sql

.PHONY: restore-db
restore-db:
	cat full_backup.sql | $(DOCKER) exec -e PGPASSWORD=$(DATABASE_PASSWORD) -i $(PROJECT_NAME)_postgres psql -U $(DATABASE_USER) -d $(DATABASE_NAME)

.PHONY: restore-table
restore-table:
	cat table_backup_$(filter-out $@,$(MAKECMDGOALS)).sql | $(DOCKER) exec -e PGPASSWORD=$(DATABASE_PASSWORD) -i $(PROJECT_NAME)_postgres psql -U $(DATABASE_USER) -d $(DATABASE_NAME)

.PHONY: sh-db
sh-db:
	$(DOCKER) exec -e PGPASSWORD=$(DATABASE_PASSWORD) -it $(PROJECT_NAME)_postgres psql -U $(DATABASE_USER) -d $(DATABASE_NAME)

