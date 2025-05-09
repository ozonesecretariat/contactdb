# Running tests

## Running backend tests

- To run the full suite, make sure you have everything [installed for dev](./install_develop.md) and run
  ```shell
  pytest
  ```
- To run with coverage
  ```shell
  pytest --cov
  ```
- To run a specific test suite
  ```shell
  pytest accounts/tests/test_users.py
  ```
- To run a specific single test

  ```shell
  pytest accounts/tests/test_users.py::TestUsers::test_create_user
  ```

## Running E2E tests

Prepare env:

- Clone repository locally
- Make sure that the app is running. Either using [install for dev](./install_develop.md) or
  [install with docker](./install_docker.md).
- Seed the database with data for the E2E tests. Only needs to be done once, but if you change anything in the DB you
  _may need to run it again_.
  ```shell
  ./manage.py seed_db
  # OR if running in docker
  docker compose exec app ./manage.py seed_db
  ```
- Install dev frontend dependencies:
  ```shell
  npm install
  ```

Interactive running options:

- Open interactive Cypress test runner and manually run specs from there
  ```shell
  npm run test:open
  ```

Headless running options:

- Run the FULL suite headless
  ```shell
  npm run test
  ```
- Run single spec headless
  ```shell
  npm run test -- -s cypress/e2e/1.login/1.login.cy.js
  ```
