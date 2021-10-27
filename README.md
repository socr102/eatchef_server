# EATCHEFS BACKEND

[Install Docker](https://docs.docker.com/install/)
[Install Docker Compose](https://docs.docker.com/compose/install/)

---

# Local installation

### DOCKER ONLY

#### 1. INSTALLATION

(after git clone)

```
cp main/settings/local.py.example main/settings/local.py
cp main/settings/local-docker.py.example main/settings/local-docker.py
```

To create admin:
```
docker-compose run --rm main bash
python manage.py createsuperuser
```

---

#### 2. RUN SERVER

(after git pull)

```
# if there are unapplied migrations
docker-compose run main bash -c "python manage.py migrate"

docker-compose up -d
```

---

#### 3. IF THERE ARE PROBLEMS

3.1 if some package is not installed after pull
```
docker-compose exec --it eatchef-main bash
pipenv install
```

3.2 if changes in code are made and new migrations should be created (this is for backend-developers)
```
docker-compose run --rm main bash -c "python manage.py makemigrations"
```

3.3 to rebuild containers from scratch
```
docker system prune -a
```
(then Installation)

---

### DJANGO USING VIRTUALENV, DOCKER FOR OTHER COMPONENTS

#### 1. INSTALLATION

[Install python >= 3.9](https://www.python.org/downloads/release/python-395/)

(after git clone)

```
# for Ubuntu
# necessary only if pipenv is already installed and there are problems
sudo apt-get remove python3-pipenv
```

```
pip3 install pipenv --user
pip3 install virtualenv --user
pipenv install  # install modules from Pipfile
```

```
pipenv --py  # check that python from virtualenv is used
```

---

#### 2. RUN SERVER

```
docker-compose up -d postgres rabbit redis
```

```
# WINDOWS
set DJANGO_SETTINGS_MODULE=main.settings.local
# UNIX
export DJANGO_SETTINGS_MODULE=main.settings.local

pipenv shell
python manage.py migrate
python manage.py runserver 0.0.0.0:4096
```

In order to run workers locally, you need to run the command

```
# WINDOWS
set DJANGO_SETTINGS_MODULE=main.settings.local
celery -A main worker -l debug

# UNIX
export DJANGO_SETTINGS_MODULE=main.settings.local
celery -A main worker -l debug
```

To run the crontab locally, you need to run the command

```
# WINDOWS
set DJANGO_SETTINGS_MODULE=main.settings.local
celery -A main beat -l debug

# UNIX
export DJANGO_SETTINGS_MODULE=main.settings.local
celery -A main beat -l debug
```

#### 3. IF THERE ARE PROBLEMS

3.1 if package is not installed
```
pipenv install
```

---

### ADDITIONAL COMMANDS

1) To check code coverage by tests, coverage is used.

```
coverage run && coverage report
coverage run && coverage html
```

2) To load example recipes for testing purposes from stored json file

```
python manage.py add_recipes --user-id=1
```

---

# Stage installation

```
cd /services/eatchef_server/ci/stage
python3 scripts.py deploy  # containers will be built and started
```

Please note that including monitoring.yml during deploy of the produciton
server exposes server and container data to be monitored by external system
(ports 9100 and 8080 should be opened in the firewall for this).

---

# Production installation

```
cd /services/eatchef_server/ci/production
python3 scripts.py deploy  # containers will be built and started
```
