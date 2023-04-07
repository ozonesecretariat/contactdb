# Local Docker build

In some case it might be useful to build images and test the full stack locally. This
can be done by following these steps:

- Make sure docker and docker-compose-plugin is installed
- Copy override example and adjust as necessary:
  ```shell
  cp docker-compose.override.local-build.yml docker-compose.override.yml  
  ```
- Copy env example and adjust as necessary. Most values will be set to working 
  defaults
  ```shell
  cp .env.example .env
  ```
- Build and start services
  ```shell
  docker compose build --pull
  docker compose up -d
  ```
  
