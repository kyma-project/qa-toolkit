#!/usr/bin/env python3

import os
import re
import tempfile

from argparse import ArgumentParser
from git import Repo
from prettytable import PrettyTable

PREFIX_FEAT = "feat"
PREFIX_FIX = "fix"
PREFIX_REFACTOR = "refactor"
PREFIX_TEST = "test"


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


class File:
    @staticmethod
    def is_test(name):
        return name.endswith("_test.go")

    @staticmethod
    def is_test_in_path(name, test_path):
        return File.is_test(name) and test_path is not None and name.startswith(test_path)


class Commit:
    def __init__(self, message, files):
        self.message = message
        self.files = files

    def filter_files(self, predicate):
        return predicate(self.files)


PATH_REPO = tempfile.mkdtemp()
BRANCH_MAIN = "main"

# The pattern for the conventional commit message.
# https://www.conventionalcommits.org/en/v1.0.0/
CONVENTIONAL_COMMIT_RE = re.compile(r"^([\w]{3,}){1}(\([\w\-.,\s]+\))?(!)?: ([\w ])+([\s\S]*)$")


# A predicate for commits that are reportable.
def filter_relevant_commit(commit_message):
    if not CONVENTIONAL_COMMIT_RE.match(commit_message):
        return True

    is_feature = commit_message.startswith(PREFIX_FEAT)
    is_fix = commit_message.startswith(PREFIX_FIX)
    is_refactor = commit_message.startswith(PREFIX_REFACTOR)
    is_test = commit_message.startswith(PREFIX_TEST)

    return is_feature or is_test or is_fix or is_refactor


# Breaks down the test modified files into distinct test suites (unit, e2e and integration) for commits collection.
def gauge(commits, paths):
    # Normalise the commit messages.
    for c in commits:
        c.message = c.message.split("\n")[0]
    filtered_commits = filter(lambda commit: filter_relevant_commit(commit.message), commits)

    gauged_commits = []
    for c in filtered_commits:
        changed_files = [f for f in c.stats.files.keys() if not f.startswith(paths["exclude"])]
        changed_unit_tests = [f for f in changed_files if File.is_test(f) and
                              not File.is_test_in_path(f, paths["e2e"]) and
                              not File.is_test_in_path(f, paths["integration"])
                              ]
        changed_integration_tests = [f for f in changed_files if File.is_test_in_path(f, paths["integration"])]
        changed_e2e_tests = [f for f in changed_files if File.is_test_in_path(f, paths["e2e"])]

        gauged_commits.append({
            "message": c.message,
            "unit_tests": len(changed_unit_tests),
            "integration_tests": len(changed_integration_tests),
            "e2e_tests": len(changed_e2e_tests),
        })

    return gauged_commits


def pad(number, percent):
    percent_str = ("(%d%%)" % round(percent * 100)).rjust(6)
    return "%d %s" % (number, Colour.highlight(percent_str, Colour.DIM))


# Validates and normalises the CLI arguments.
def normalise(args):
    try:
        args.days = int(args.days)
    except TypeError:
        raise "the --days parameter must be an integer value"

    if args.days < 1:
        raise "the --days parameter must be an integer value greater that 0"

    if args.exclude_path:
        args.exclude_path = tuple(args.exclude_path)
    else:
        args.exclude_path = ()

    return args


def print_commits_report(gauged_commits, integration=False, e2e=False):
    def pluck(data, penultimate=False, last=False):
        entries = len(data)
        if not last:
            data.pop(entries - 1)
        if not penultimate:
            data.pop(entries - 2)
        return data

    table = PrettyTable(pluck(["Message", "Unit", "Integration", "E2E"], integration, e2e))
    for c in gauged_commits:
        no_test_suites = c["e2e_tests"] == 0 and c["unit_tests"] == 0 and c["integration_tests"] == 0
        colour = Colour.RED if no_test_suites else Colour.RESET
        table.add_row(pluck([
            c["message"],
            Colour.highlight(c["unit_tests"], colour),
            Colour.highlight(c["integration_tests"], colour),
            Colour.highlight(c["e2e_tests"], colour)
        ], integration, e2e))

    table.align["Message"] = "l"
    table.align["Unit"] = "r"
    if integration:
        table.align["Integration"] = "r"
    if e2e:
        table.align["E2E"] = "r"
    print(table)


def print_aggregation_report(commits, integration, e2e):
    def suite_stats(index, commits, features, fixes, tests):
        suite = [c for c in commits if c[index] > 0]
        suite_features = [c for c in features if c[index] > 0]
        suite_fixes = [c for c in fixes if c[index] > 0]
        suite_tests = [c for c in tests if c[index] > 0]

        return [
            len(suite),
            pad(len(suite_features), len(suite_features) / len(features) if len(features) else 0),
            pad(len(suite_fixes), len(suite_fixes) / len(fixes) if len(fixes) else 0),
            pad(len(suite_tests), len(suite_tests) / len(tests) if len(tests) else 0),
        ]

    table = PrettyTable(("", "Total", "Features", "Fixes", "Tests"))

    features = [c for c in commits if c["message"].startswith(PREFIX_FEAT)]
    fixes = [c for c in commits if c["message"].startswith(PREFIX_FIX)]
    tests = [c for c in commits if c["message"].startswith(PREFIX_TEST)]
    table.add_row((
        "PRs", len(commits),
        pad(len(features), len(features) / len(commits) if len(commits) else 0),
        pad(len(fixes), len(fixes) / len(commits) if len(commits) else 0),
        pad(len(tests), len(tests) / len(commits) if len(commits) else 0),
    ))

    table.add_row(["Unit"] + suite_stats("unit_tests", commits, features, fixes, tests))

    if integration:
        table.add_row(["Integration"] + suite_stats("integration_tests", commits, features, fixes, tests))

    if e2e:
        table.add_row(["E2E"] + suite_stats("e2e_tests", commits, features, fixes, tests))

    table.align[""] = "l"
    table.align["Total"] = "r"
    table.align["Features %"] = "r"
    table.align["Fixes %"] = "r"
    table.align["Features"] = "r"
    table.align["Fixes"] = "r"
    table.align["Tests"] = "r"
    print(table)


if "__main__" == __name__:
    parser = ArgumentParser()
    parser.add_argument("--repo-url", dest="repo_url", help="A URL for the GitHub repository")
    parser.add_argument("--days", dest="days", help="A number of days for the report")
    parser.add_argument("--e2e", dest="e2e_path", help="A path to the directory with the E2E test suite")
    parser.add_argument("--integration", dest="integration_path",
                        help="A path to the directory with the integration test suite")
    parser.add_argument("--exclude", dest="exclude_path", action='append',
                        help="Paths to be excluded from the analysis")
    args = parser.parse_args()
    normalise(args)

    try:
        repo = Repo.clone_from(args.repo_url, PATH_REPO, branch=BRANCH_MAIN)
    except:
        print('Cannot clone the repository at URL: "%s"' % args.repo_url)
        exit(os.EX_IOERR)

    gauged_commits = gauge(
        list(repo.iter_commits('--all', since='%d.days.ago' % args.days)),
        {
            "exclude": args.exclude_path,
            "integration": args.integration_path,
            "e2e": args.e2e_path,
        })

    print_commits_report(gauged_commits, integration=args.integration_path, e2e=args.e2e_path)
    print_aggregation_report(gauged_commits, integration=args.integration_path, e2e=args.e2e_path)
