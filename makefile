
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

deploy: initprod refresh prod

prod:
	$(UP_CMD)
	$(LOGS_CMD)

initprod:
	cp -rf envs/prod/.env ./
	cp -rf envs/prod/compose.yml ./
	cp -rf envs/prod/gunicorn.conf.py ./vendor

###### Frontend DEV #######

cleandfrontend: initfrontend refresh frontend

frontend: initfrontend
	$(UP_CMD)
	$(LOGS_CMD)

initfrontend:
	cp -rf envs/frontend/.env ./
	cp -rf envs/frontend/compose.yml ./
	cp -rf envs/frontend/gunicorn.conf.py ./vendor

###### Backend DEV #######

cleanbackend: initbackend refresh backend

backend: initbackend
	$(UP_CMD)
	$(LOGS_CMD)

initbackend:
	cp -rf envs/backend/.env ./
	cp -rf envs/backend/compose.yml ./
	cp -rf envs/backend/gunicorn.conf.py ./vendor

devdeploy:
	-git commit -am "Updated"
	-git push
	-cd /root/prod/StoryTeller/;make clean;git checkout main;git pull;make prod


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

logs:
	$(LOGS_CMD)

prune:
	docker system prune -a