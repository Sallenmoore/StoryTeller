
TARGETS=initprod initdev deploy run dev test tests cleantest inittests refresh logs clean
BUILD_CMD=docker compose build --no-cache
UP_CMD=docker compose up --build -d
DOWN_CMD=docker compose down --remove-orphans
LOGS_CMD=docker compose logs -f
BACKUPDB_CMD=cp -R ../../prod/world-prod/api/dbbackups/ ../../backups/
BACKUPIMAGES_CMD=cp -R ../../prod/world-prod/static/images ../../backups/
APPCONTAINERS=$$(sudo docker ps --filter "name=${APP_NAME}" -q)

# **Use .ONESHELL**: By default, each line in a makefile is run in a separate shell. This can cause problems if you're trying to do something like change the current directory. You can use the `.ONESHELL:` directive to run all the commands in a target in the same shell.

.PHONY: $(TARGETS)

# # Check if the config file exists - XXX: don't know which .env file to use yet
# ifeq (,$(wildcard .env))
# $(error The file $(CONFIG_FILE) does not exist)
# endif

include .env
export
###### PROD #######

deploy: refresh run

run: initprod clean
	$(UP_CMD)
	docker compose stop db-express
	$(LOGS_CMD)

rundb: initprod clean
	$(UP_CMD)
	$(LOGS_CMD)

initprod:
	./scripts/prod_db_copy.sh
	$(BACKUPDB_CMD)
	$(BACKUPIMAGES_CMD)
	cp -rf envs/prod/.env ./
	cp -rf envs/prod/docker-compose.yml ./
	cp -rf envs/prod/gunicorn.conf.py ./vendor

###### DEV #######

cleandev: refresh dev

dev: initdev
	$(UP_CMD)
	sleep 5
	./scripts/prod_db_copy.sh
	$(LOGS_CMD)

initdev:
	cp -rf envs/dev/.env ./
	cp -rf envs/dev/docker-compose.yml ./
	cp -rf envs/dev/gunicorn.conf.py ./vendor

###### TESTING #######

cleantests: refresh tests

tests: inittests
	$(UP_CMD)
	docker exec -it $(APP_NAME) python -m pytest --pdb

RUNTEST?=test_ai_generation
test: inittests
	$(UP_CMD)
	docker exec -it $(APP_NAME) python -m pytest -k $(RUNTEST) #--pdb

inittests:
	cp -rf envs/testing/.env ./
	cp -rf envs/testing/docker-compose.yml ./
	cp -rf envs/testing/gunicorn.conf.py ./vendor

###### UTILITY #######

clean:
	sudo docker ps -a
	-$(DOWN_CMD)
	-sudo docker kill $(APPCONTAINERS)

refresh: clean
	$(BUILD_CMD)
	$(UP_CMD)

logs:
	$(LOGS_CMD)

prune:
	docker system prune -a