#!/usr/bin/env python3

from argparse import ArgumentParser
from git import Repo
import json
import os
import re

DIRS_TO_SKIP = (".", "config", "tests")  # The list of directories to skip metric calculation
GO_TEST_SUFFIX = "_test.go"
GO_SUFFIX = ".go"

# The regular expression to match an import section content inside a go file (https://regex101.com/r/JW2UD0/1).
go_imports_regexp = re.compile(r"import \((.*?)\)|import (\".*?\")", flags=re.MULTILINE | re.DOTALL)


def trim_prefix(text, prefix):
    return text[len(prefix):] if text.startswith(prefix) else text


# Extracts the list of dependencies from the go file content.
def extract_deps(file_contents):
    imports_match = go_imports_regexp.search(file_contents)
    if not imports_match:
        return []

    # Normalise the imports section, weed out empty lines and comments.
    raw_imports = imports_match.group(1) if imports_match.group(1) else imports_match.group(2)
    imports = [i.strip() for i in raw_imports.split("\n")]
    imports = [i for i in imports if len(i) > 0 and not i.startswith("//")]

    dependencies = []
    for i in imports:
        # Extract the imported package name only (without any aliases and quote characters).
        dependencies.append(re.match(r'.*\"(.*)\".*', i)[1])

    return list(set(dependencies))


# Returns the dict of all go packages discovered under the given path.
def fetch_deps(path, skipped_dirs):
    packages = {}

    for root, dirs, files in os.walk(path):
        package_name = trim_prefix(root, path)

        # Skip all unwanted directories.
        if any(True for to_skip in skipped_dirs if package_name.startswith(to_skip)):
            continue

        # Fetch the list of go files in the directory excluding test ones.
        go_files = [f for f in files if not f.endswith(GO_TEST_SUFFIX) and f.endswith(GO_SUFFIX)]
        if len(go_files) == 0:
            continue

        dependencies = []
        for f in go_files:
            file = open(os.path.join(root, f), "r")
            dependencies += extract_deps(file.read())

        packages[package_name] = list(set(dependencies))

    return packages


# Groups the dependencies into efferent, afferent and external categories.
def group_deps(imported_packages, module_name):
    packages = {}
    for package in imported_packages:
        package_name = module_name + package
        package_imports = imported_packages[package]
        packages[package] = {
            # The list of all imported packages prefixed with a module_name.
            "efferent": len([i for i in package_imports if i.startswith(module_name)]),
            # The list of all packages that import a package_name.
            "afferent": len([1 for p in imported_packages if package_name in imported_packages[p]]),
            # The list of all external packages (the ones that contain a "." as a domain-name and "/"
            # as a path separator to distinguish them for the standard packages).
            "external": len(set([i for i in package_imports if
                                 not i.startswith(module_name) and '/' in i and "." in i.split("/")[0]])),
        }

    return packages


# Validates and normalises the CLI arguments.
def normalise(args):
    if not args.go_module or len(args.go_module) == 0:
        raise "the --module parameter must not be empty"

    if not args.go_module.endswith("/"):
        args.go_module += "/"

    if not args.repo_path or len(args.repo_path) == 0:
        raise "the --path parameter must not be empty"
    if not args.repo_path.endswith("/"):
        args.repo_path += "/"

    if not args.out or len(args.out) == 0:
        raise "the --out parameter must not be empty"

    if args.skip:
        skip = args.skip.split(",")
        skip = [s.trim() for s in skip]
        skip = [s for s in skip if len(s) > 0]
        args.skip = list(DIRS_TO_SKIP) + skip
    else:
        args.skip = list(DIRS_TO_SKIP)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--path", dest="repo_path", help="A path to the Go project's source code")
    parser.add_argument("-o", "--out", dest="out", help="A path to the resulting JSON file")
    parser.add_argument("-s", "--skip", dest="skip",
                        help="A comma-separated list of directories to be skipped for the analysis")
    parser.add_argument("-m", "--module", dest="go_module",
                        help="Fully qualified go module name (e.g.: github.com/kyma-project/lifecycle-manager)")

    args = parser.parse_args()
    normalise(args)

    repo = Repo(args.repo_path)
    dependencies = fetch_deps(args.repo_path, args.skip)
    grouped_dependencies = group_deps(dependencies, args.go_module)

    out_file = open(args.out, "w")
    json.dump(grouped_dependencies, out_file, indent=4)
    out_file.close()
