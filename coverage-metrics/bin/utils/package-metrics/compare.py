#!/usr/bin/env python3

from argparse import ArgumentParser
import json
from prettytable import PrettyTable

COLOURS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "blue": "\033[94m",
    "empty": "\x1b[0m",
}


def normalise(args):
    if not args.base_path or len(args.base_path) == 0:
        raise "the --base parameter must not be empty"

    if not args.target_path or len(args.target_path) == 0:
        raise "the --target parameter must not be empty"


# Highlights the text with a specified colour.
def highlight(text, colour):
    return f'{colour}{text}{COLOURS["empty"]}'


# Highlights the keywords in the input.
def highlight_delta(string, delta, is_new=False):
    if is_new:
        return highlight(string, COLOURS['blue'])

    if delta > 0:
        return highlight(string, COLOURS['red'])

    if delta < 0:
        return highlight(string, COLOURS['green'])

    return string


if "__main__" == __name__:
    parser = ArgumentParser()
    parser.add_argument("-b", "--base", dest="base_path", help="A path to the json file with a base metrics")
    parser.add_argument("-t", "--target", dest="target_path", help="A path to the json file with a target metrics")

    args = parser.parse_args()
    normalise(args)

    # Read the file contents
    with open(args.base_path, "r") as base_file:
        base = json.load(base_file)
    with open(args.target_path, "r") as target_file:
        target = json.load(target_file)

    base = dict(sorted(base.items()))
    target = dict(sorted(target.items()))

    table = PrettyTable(("Package", "Efferent", "Afferent", "External"))

    for pkg, pkg_metrics in target.items():
        is_new = pkg not in base

        delta_efferent = pkg_metrics["efferent"] - base.get(pkg, {}).get("efferent", 0)
        delta_afferent = pkg_metrics["afferent"] - base.get(pkg, {}).get("afferent", 0)
        delta_external = pkg_metrics["external"] - base.get(pkg, {}).get("external", 0)

        efferent_label = " %+d" % delta_efferent if delta_efferent != 0 else ""
        afferent_label = " %+d" % delta_afferent if delta_afferent != 0 else ""
        external_label = " %+d" % delta_external if delta_external != 0 else ""

        table.add_row(
            (pkg,
             "%d%s" % (pkg_metrics["efferent"], highlight_delta(efferent_label, delta_efferent, is_new=is_new)),
             "%d%s" % (pkg_metrics["afferent"], highlight_delta(afferent_label, delta_afferent, is_new=is_new)),
             "%d%s" % (pkg_metrics["external"], highlight_delta(external_label, delta_external, is_new=is_new)),
             ))

    table.align["Package"] = "l"
    table.align["Efferent"] = "r"
    table.align["Afferent"] = "r"
    table.align["External"] = "r"
    print(table)
