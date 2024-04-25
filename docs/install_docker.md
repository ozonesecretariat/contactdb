# Install Docker

Steps for installing the application with Docker for production. _Not suitable for development!_

## Docker Setup

- Clone the repository, or just download the relevant files:
  - [.env.example](../.env.example)
  - [docker-compose.yml](../docker-compose.yml)
  - [docker-compose.override.example.yml](../docker-compose.override.example.yml)
- Make sure docker and docker-compose-plugin is installed
- Copy override example and adjust as necessary:
  ```shell
  cp docker-compose.override.example.yml docker-compose.override.yml
  ```
- Copy env example and adjust as necessary. Most values will be set to working
  defaults
  ```shell
  cp .env.example .env
  ```
- Start services
  ```shell
  docker compose up -d
  ```
- Create a super user
  ```shell
  docker compose exec app ./manage.py createsuperuser
  ```
- Load initial fixtures
  ```shell
  docker compose exec app ./manage.py load_fixtures initial
  ```

## Updating

- Update the git repo/relevant files
- Pull and restart services
  ```shell
  docker compose pull
  docker compose up -d --remove-orphans
  ```
