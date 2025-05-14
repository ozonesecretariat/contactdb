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
- The Python code uses the [black style guide](https://black.readthedocs.io/en/stable/) for extra automatic linting. Can
  be integrated into your IDE or manually run with:
  ```bash
  black .
  ```

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

- Add it to either [base.txt](../requirements/base.txt) if the dependency needs to be run in production
  or [dev.txt](../requirements/dev.txt) if the dependency is only needed for developing.
- Create a new virtualenv and activate it
  ```bash
  virtualenv .venv && source .venv/bin/activate
  ```
- Install all dependencies
  ```bash
  pip install -r requirements/dev.txt -r requirements/prod.txt -c requirements/constraints.txt
  ```
- Resolve any dependency problems, if any
- Freeze the new constraints
  ```bash
  pip freeze > requirements/constraints.txt
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
