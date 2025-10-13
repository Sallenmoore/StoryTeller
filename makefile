
TARGETS=deploy run initprod cleandev dev initdev cleantests tests test inittests clean refresh logs prune
BUILD_CMD=docker compose build --no-cache
UP_CMD=docker compose up --build -d
DOWN_CMD=docker compose down --remove-orphans
LOGS_CMD=docker compose logs -f
APPCONTAINERS=$$(sudo docker ps --filter "name=${APP_NAME}" -q)

# **Use .ONESHELL**: By default, each line in a makefile is run in a separate shell. This can cause problems if you're trying to do something like change the current directory. You can use the `.ONESHELL:` directive to run all the commands in a target in the same shell.

.PHONY: $(TARGETS)

include .env
export
###### PROD #######

deploy: refresh run

run: initprod clean
	$(UP_CMD)
	$(LOGS_CMD)

initprod:
	cp -rf envs/prod/.env ./
	cp -rf envs/prod/compose.yml ./
	cp -rf envs/prod/gunicorn.conf.py ./vendor

###### Frontend DEV #######

cleandev: refresh dev

dev: initdev
	$(UP_CMD)
	$(LOGS_CMD)

initdev:
	cp -rf envs/dev/.env ./
	cp -rf envs/dev/compose.yml ./
	cp -rf envs/dev/gunicorn.conf.py ./vendor

###### Backend DEV #######

cleandev: refresh dev

dev: initdev
	$(UP_CMD)
	$(LOGS_CMD)

initdev:
	cp -rf envs/backend/.env ./
	cp -rf envs/backend/compose.yml ./
	cp -rf envs/backend/gunicorn.conf.py ./vendor

###### TESTING #######

cleantests: refresh tests

tests: inittests
	docker exec -it $(APP_NAME) python -m pytest

RUNTEST?=test_campaign
test: inittests
	docker exec -it $(APP_NAME) python -m pytest -k $(RUNTEST)

inittests:
	cp -rf envs/testing/.env ./
	cp -rf envs/testing/compose.yml ./
	cp -rf envs/testing/gunicorn.conf.py ./vendor
	$(UP_CMD)

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