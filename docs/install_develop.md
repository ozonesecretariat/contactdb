# Installing for development

**WARNING! DO NOT USE THIS DEPLOYMENT IN A PRODUCTION ENVIRONMENT!**

This document describes installation steps required to install locally for development.

## Preparing environment

- Install node (>=22)
- Install uv (>=0.7.3)
- Install and start postgresql (>=15)
- Install and start redis (>=7)
- Create a postgresql database and user:
  ```shell
  sudo -u postgres createuser -Pds contactdb && sudo -u postgres createdb contactdb
  ```
- Clone this repository

## Installing app for development

- Configure local settings, starting from the dev example; ensure that the DB connection details are correctly set
  ```shell
  cp .env.develop.example .env
  ```
- Install dependencies
  ```shell
  uv sync
  npm install
  ```
- Activate virtualenv (or run all commands with `uv run`)
  ```shell
  source .venv/bin/activate
  ```
- Run migrations
  ```shell
  ./manage.py migrate
  ```
- Add some testing data to the DB:
  ```shell
  ./manage.py seed_db
  ```

## Running the application

- Start the backend with hot-reload
  ```shell
  ./manage.py runserver
  ```
- Start frontend with hot-reload
  ```shell
  npm run dev
  ```
- _(optional)_ Start worker. _**NOTE** Worker does not have hot-reload, changes to the code will require a restart_
  ```shell
  ./manage.py rqworker
  ```
- Check that the app is running correctly at http://localhost:8080 and login with credentials created with seed_db:
  - admin@example.com / admin

## Updating the application

- Update the code with the latest version
- Update third-party packages required at runtime.
  ```shell
  uv sync
  npm install
  ```
- Run migrations:
  ```shell
  ./manage.py migrate
  ```

## Docker

- Copy the env file
  ```shell
  cp .env.develop.docker.example .env
  ```
- Copy the compose override file to create an override
  ```shell
  cp compose.override.local-build.yml compose.override.yml
  ```
- Build and start the containers
  ```shell
  docker compose build
  docker compose up -d
  ```
- Add testing data
  ```shell
  docker compose exec app ./manage.py seed_db
  ```
- Check that the app is running correctly at http://localhost:8080 and login with credentials created with seed_db:
  - admin@example.com / admin

## Where to go from here?

See the [tests guide](./tests.md) to run the test suites locally. Afterward check
the [development guide](./development_guide.md) to help you get started.
