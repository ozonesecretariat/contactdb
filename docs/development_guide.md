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

- [django](https://docs.djangoproject.com//)
- [django-task](https://github.com/morlandi/django-task)
- [pytest](https://docs.pytest.org/)
- [vue](https://vuejs.org/)
- [vue-router](https://router.vuejs.org/)
- [vueuse](https://vueuse.org/)
- [pinia](https://pinia.vuejs.org/)
- [quasar](https://quasar.dev/)
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
