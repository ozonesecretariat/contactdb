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
