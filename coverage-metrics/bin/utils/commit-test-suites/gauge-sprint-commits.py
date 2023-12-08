#!/usr/bin/env python3

import os
import re
import tempfile

from argparse import ArgumentParser
from git import Repo
from prettytable import PrettyTable


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
    def is_e2e_test(name, e2e_path):
        return e2e_path != "" and File.is_test(name) and name.startswith(e2e_path)

    @staticmethod
    def is_unit_test(name, e2e_path):
        return File.is_test(name) and (e2e_path == "" or not name.startswith(e2e_path))


PATH_REPO = tempfile.mkdtemp()
BRANCH_MAIN = "main"

# The pattern for the conventional commit message.
# https://www.conventionalcommits.org/en/v1.0.0/
CONVENTIONAL_COMMIT_RE = re.compile(r"^([\w]{3,}){1}(\([\w\-.,\s]+\))?(!)?: ([\w ])+([\s\S]*)$")


# A predicate for commits that are reportable.
# Reportable commits are: features, fixes, tests and refactorings.
def filter_relevant_commit(commit_message):
    if not CONVENTIONAL_COMMIT_RE.match(commit_message):
        return True

    is_feat = commit_message.startswith("feat")
    is_test = commit_message.startswith("test")
    is_fix = commit_message.startswith("fix")
    is_refactor = commit_message.startswith("refactor")

    return is_feat or is_test or is_fix or is_refactor


# Calculates metrics for commits within a specified timespan.
def gauge(commits, e2e_path):
    # Strip all commit messages.
    for c in commits: c.message = c.message.split("\n")[0]
    filtered_commits = [c for c in commits if filter_relevant_commit(c.message)]

    gauged_commits = []
    for c in filtered_commits:
        changed_files = list(c.stats.files.keys())
        gauged_commits.append({
            "message": c.message,
            "changed_e2e_files": len([f for f in changed_files if File.is_e2e_test(f, e2e_path)]),
            "changed_test_files": len([f for f in changed_files if File.is_unit_test(f, e2e_path)]),
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

    if not args.e2e_path:
        args.e2e_path = ""

    return args


def print_commits_report(gauged_commits, e2e_path):
    table = PrettyTable(("Message", "E2E tests", "Unit tests"))
    for c in gauged_commits:
        no_test_suites = c["changed_e2e_files"] == 0 and c["changed_test_files"] == 0
        colour = Colour.RED if no_test_suites else Colour.RESET
        table.add_row((
            c["message"],
            Colour.highlight(c["changed_e2e_files"], colour),
            Colour.highlight(c["changed_test_files"], colour),
        ))

    table.align["Message"] = "l"
    table.align["E2E tests"] = "r"
    table.align["Unit tests"] = "r"
    print(table)


def print_aggregation_report(commits):
    table = PrettyTable(("", "Total", "Features", "Fixes", "Tests"))

    features = [c for c in commits if c["message"].startswith("feat")]
    fixes = [c for c in commits if c["message"].startswith("fix")]
    tests = [c for c in commits if c["message"].startswith("test")]
    table.add_row((
        "PRs", len(commits),
        pad(len(features), len(features) / len(commits) if len(commits) else 0),
        pad(len(fixes), len(fixes) / len(commits) if len(commits) else 0),
        pad(len(tests), len(tests) / len(commits) if len(commits) else 0),
    ))

    ut = [c for c in commits if c["changed_test_files"] > 0]
    ut_features = [c for c in features if c["changed_test_files"] > 0]
    ut_fixes = [c for c in fixes if c["changed_test_files"] > 0]
    ut_tests = [c for c in tests if c["changed_test_files"] > 0]
    table.add_row((
        "Unit tests", len(ut),
        pad(len(ut_features), len(ut_features) / len(features) if len(features) else 0),
        pad(len(ut_fixes), len(ut_fixes) / len(fixes) if len(fixes) else 0),
        pad(len(ut_tests), len(ut_tests) / len(tests) if len(tests) else 0),
    ))

    e2e = [c for c in commits if c["changed_e2e_files"] > 0]
    e2e_features = [c for c in features if c["changed_e2e_files"] > 0]
    e2e_fixes = [c for c in fixes if c["changed_e2e_files"] > 0]
    e2e_tests = [c for c in tests if c["changed_e2e_files"] > 0]
    table.add_row((
        "E2E tests", len(e2e),
        pad(len(e2e_features), len(e2e_features) / len(features) if len(features) else 0),
        pad(len(e2e_fixes), len(e2e_fixes) / len(fixes) if len(fixes) else 0),
        pad(len(e2e_tests), len(e2e_tests) / len(tests) if len(tests) else 0),
    ))

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
    parser.add_argument("-r", "--repo", dest="repo_url", help="A URL for the GitHub repository")
    parser.add_argument("-d", "--days", dest="days", help="A number of days for the report")
    parser.add_argument("-t", "--e2e-path", dest="e2e_path", help="A path to the directory with the E2E test suite")

    args = parser.parse_args()
    normalise(args)

    try:
        repo = Repo.clone_from(args.repo_url, PATH_REPO, branch=BRANCH_MAIN)
    except:
        print('Cannot clone the repository at URL: "%s"' % args.repo_url)
        exit(os.EX_IOERR)

    gauged_commits = gauge(list(repo.iter_commits('--all', since='%d.days.ago' % args.days)), args.e2e_path)

    print_commits_report(gauged_commits, args.e2e_path)
    print_aggregation_report(gauged_commits)
