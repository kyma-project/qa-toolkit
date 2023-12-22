# Commit Test Suites Coverage

This report lists all the repository commits for a designated timespan with a breakdown to unit and E2E test suites for 
each.

## Usage
```sh
gauge-sprint-commits.py --repo-url https://github.com/kyma-project/lifecycle-manager.git --days 14 --e2e tests/e2e --integration tests/integration --exclude api/ --exclude docs/```

### Parameters
 Parameter  | Description
----------- | -----------
repo-url    | the URL to the repository to be gauged
days        | the days backwards to fetch commits for
e2e         | the path to the E2E test suite. This path is used to separate unit test from the E2E tests
integration | the path to the Integration test suite. This path is used to separate unit test from the integration tests
exclude     | the paths to exclude fro the report
