#!/usr/bin/env python3

import os
import re
import subprocess

from argparse import ArgumentParser
from prettytable import PrettyTable
import yaml

ATTR_PACKAGES = "packages"
CONFIG = "config.yaml"


class Colour:
    RED = "\033[91m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    # Resets the colour to the default one
    RESET = "\x1b[0m"
    # Dims the current colour
    DIM = '\033[2m'

    @staticmethod
    # Highlights the text with a specified colour.
    def highlight(text, colour):
        return f'{colour}{text}{Colour.RESET}'


# Validates the test coverage config file.
def validate_coverage_config(config):
    if ATTR_PACKAGES not in coverage_cfg:
        raise AttributeError('The coverage config file is malformed. The "%s" attribute is missing.' % ATTR_PACKAGES)

    if len(config[ATTR_PACKAGES]) == 0:
        return config

    for pkg, pkg_coverage in config[ATTR_PACKAGES].items():
        if not type(pkg_coverage) in (int, float):
            raise AttributeError('A non-numeric coverage setting for package: "%s".' % pkg)

    return config


# Ensures that every package under evaluation exist in the target repository.
def ensure_packages_exist(packages, repo_path):
    for pkg in packages:
        pkg_path = os.path.join(repo_path, pkg)
        if not os.path.exists(pkg_path):
            raise FileNotFoundError('Cannot find a package "%s" under "%s".' % (pkg, repo_path))


def fetch_raw_coverage(packages, path):
    if len(packages) == 0:
        return ""

    # Normalise the package path to be relative to the project.
    packages = ["./%s" % p for p in packages]
    try:
        raw_coverage = subprocess.check_output(['go', 'test', '-cover', *packages], cwd=os.path.realpath(path))
        return raw_coverage.decode("UTF-8")
    except Exception as e:
        return str(e.output).replace('\\n', '\n').replace('\\t', '\t')


def parse_coverage(raw_coverage):
    failed_test_suites = re.findall(r"^FAIL\s*" + re.escape(args.module) + r"/([\w/]*)",
                                    raw_coverage,
                                    flags=re.MULTILINE)
    if len(failed_test_suites) > 0:
        raise AssertionError("Unit tests failed for packages: %s" % ", ".join(failed_test_suites))

    res = {}
    # Extracts all coverage percentages from the unit test report.
    # https://regex101.com/r/xPIx8n/1
    coverages = re.findall(
        r"^ok\s*" + re.escape(args.module) + r"/([\w/]*)\s*(?:\(cached\)|\d*\.\d*s)?\s*coverage: (\d*\.\d*)%",
        raw_coverage,
        flags=re.MULTILINE)
    for package, package_coverage in coverages:
        res[package] = float(package_coverage)

    return res


def print_report(cfg, coverage):
    table = PrettyTable(("Package", "Desired coverage", "Actual coverage"))
    is_undertested = False
    for package, desired_coverage in cfg[ATTR_PACKAGES].items():
        if package not in coverage:
            raise AttributeError('A package "%s" is not in the list of tested packages.' % package)
        actual_coverage = coverage[package]
        is_covered = actual_coverage >= desired_coverage
        if not is_covered:
            is_undertested = True
        colour = Colour.GREEN if is_covered else Colour.RED
        table.add_row((
            package,
            Colour.highlight(desired_coverage, colour),
            Colour.highlight(actual_coverage, colour),
        ))

    table.align["Package"] = "l"
    table.align["Desired coverage"] = "r"
    table.align["Actual coverage"] = "r"
    print(table)

    return is_undertested


# Validates and normalises the CLI arguments.
def normalise(args):
    if not args.repo_path:
        raise "the --repo parameter must be point to the Go project source code"

    if not args.module:
        raise "the --module parameter contain a fully qualified module name"

    if not args.config:
        args.config = CONFIG

    return args


if "__main__" == __name__:
    parser = ArgumentParser()
    parser.add_argument("-r", "--repo", dest="repo_path", help="A path to the Go project source code")
    parser.add_argument("-m", "--module", dest="module", help="A Go module name")
    parser.add_argument("-c", "--config", dest="config", help="A coverage file config")

    args = parser.parse_args()
    normalise(args)

    try:
        with open(os.path.join(args.repo_path, args.config), 'r') as config_file:
            coverage_cfg = yaml.safe_load(config_file)

        validate_coverage_config(coverage_cfg)

        # Validate the coverage prerequisites.
        packages_with_coverage = list(coverage_cfg[ATTR_PACKAGES].keys())
        ensure_packages_exist(packages_with_coverage, args.repo_path)

        # Calculate the coverage.
        raw_coverage = fetch_raw_coverage(packages_with_coverage, args.repo_path)
        print(raw_coverage)
        base_coverage = parse_coverage(raw_coverage)

        is_undertested = print_report(coverage_cfg, base_coverage)
        if is_undertested:
            exit(os.EX_DATAERR)

    except (AttributeError, AssertionError, FileNotFoundError) as e:
        print(e)
        exit(os.EX_IOERR)
