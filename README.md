[![REUSE status](https://api.reuse.software/badge/github.com/kyma-project/qa-toolkit)](https://api.reuse.software/info/github.com/kyma-project/qa-toolkit)

# QA Toolkit

## Overview

This repository contains multiple scripts that are used across different GitHub Actions in order to improve overall quality of the delivered solutions, this include:
- Tests coverage by commit
- Quality gate utils for unit tests
- Tools for highlightning the Acceptance Criteria in the BDD report

## Usage

Any of the scripts may be imported and used in GH Actions.
Examples include:
- [KLM Acceptance Report](https://github.com/kyma-project/lifecycle-manager/blob/main/.github/workflows/report-acceptance-criteria.yml)
- [Package Metrics](https://github.com/kyma-project/lifecycle-manager/blob/main/.github/workflows/report-package-metrics.yml)
- [Unit Tests coverage verification in KLM](https://github.com/kyma-project/lifecycle-manager/blob/main/.github/workflows/verify-unit-test-coverage.yml)

## Contributing
<!--- mandatory section - do not change this! --->

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Code of Conduct
<!--- mandatory section - do not change this! --->

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Licensing
<!--- mandatory section - do not change this! --->

See the [LICENSE file](./LICENSE).
