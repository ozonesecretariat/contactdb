# Development guide

## Style guide

- All files should be automatically formatted with [prettier](https://prettier.io/).
  Can be integrated into your IDE or manually run with:
  ```bash
  npm run lint:prettier
  ```
- All js files should be checked with [eslint](https://eslint.org/).
  Can be integrated into your IDE or manually run with:
  ```bash
  npm run lint:eslint
  ```
- The Python code uses [ruff](https://docs.astral.sh/ruff/) for automatic linting and
  formating. Can be integrated into your IDE or manually run with:

  ```bash
  ruff format
  ruff check --fix
  ```

- Run `pre-commit install` to set up the git hook scripts

A workflow is integrated into GitHub action to check that any code push has been first processed with the project
settings. See [code style workflow](../.github/workflows/lint.yml)

## Starting points

- API documentation can be explored with [redocs](http://localhost:8000/api/schema/redoc/)
  or [swagger](http://localhost:8000/api/schema/swagger-ui/#/) while running locally
- API calls can be made from the frontend using the axios `api` instance from [boot/axios.ts](../src/boot/axios.ts)
- Backend:
  - [django](https://docs.djangoproject.com//)
  - [django-task](https://github.com/morlandi/django-task)
- Frontend:
  - [vue](https://vuejs.org/)
  - [vue-router](https://router.vuejs.org/)
  - [vueuse](https://vueuse.org/)
  - [pinia](https://pinia.vuejs.org/)
  - [quasar](https://quasar.dev/)
- Testing:
  - [pytest](https://docs.pytest.org/)
  - [cypress](https://docs.cypress.io/)

## Adding a new backend dependency

To add a new dependency:

- To add a new main dependency, run:
  ```shell
  uv add foo
  ```
- To add a new dev dependency, run:
  ```shell
  uv add --dev foo
  ```

## Testing data

Testing data can be added to the database using the seed_db management command.

```shell
./manage.py seed_db
```

This will add various users with the different access permissions that can be used with
the following credentials:

- admin@example.com / admin
- test-edit@example.com / test
- test-emails@example.com / test
- test-kronos@example.com / test
- test-no-access@example.com / test
- test-view@example.com / test
- test-non-staff@example.com / test
- test-non-staff-view@example.com / test
- test-non-staff-no-access@example.com / test
