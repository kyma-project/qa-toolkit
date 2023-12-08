# Commit Test Suites Coverage

This report lists all the repository commits for a designated timespan with a breakdown to unit and E2E test suites for 
each.

## Usage
```sh
gauge-sprint-commits.py --repo https://github.com/kyma-project/lifecycle-manager.git --days 14 --e2e-path tests/
```

### Parameters
 Parameter | Description
---------- | -----------
repo       | the URL to the repository to be gauged
days       | the days backwards to fetch commits for
e2e-path   | the path to the E2E test suite. This path is used to separate unit test from the E2E tests
