# Development guide

## Style guide

The backend code uses the [black style guide](https://black.readthedocs.io/en/stable/) for automatic linting. Can
be integrated into your IDE or manually run with:

```bash
black --extend-exclude=migrations .
```

A workflow is integrated into GitHub action to check that any code push has been first processed with the project
settings. See [code style workflow](https://github.com/ozonesecretariat/contactdb/actions/workflows/lint.yml)

## Starting points

- [django](https://docs.djangoproject.com//)
- [django-task](https://github.com/morlandi/django-task)
- [pytest](https://docs.pytest.org/)

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
