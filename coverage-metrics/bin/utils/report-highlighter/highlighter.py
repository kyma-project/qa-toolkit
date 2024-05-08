#!/usr/bin/env python3

import re
import sys
from urllib.request import urlopen

# Disable the certificate verification for the GitHub wiki page.
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

COLOURS = {
    "red": "\x1b[6;30;41m",
    "green": "\x1b[6;30;42m",
    "yellow": "\x1b[6;30;43m",
    "blue": "\x1b[6;30;44m",
    "magenta": "\x1b[6;30;45m",
    "cyan": "\x1b[6;30;36m",
    "light cyan": "\x1b[6;30;96m",
    "empty": "\x1b[0m",
}

# The URL to the Markdown file with a list of keywords.
TERMS_URL = ""
TABLE_HEADER = "Term"


def read_keywords(url):
    with urlopen(url) as response:
        terms_response = str(response.read().decode('utf-8'))

    terms = []
    for match in re.compile(r'\|(.*?)\|.*?\|').finditer(terms_response):
        columns = match.group(1).split('|')
        term = columns[0].strip()
        is_table_header = len(term.replace("-", "")) == 0 or term == TABLE_HEADER
        if not is_table_header:
            terms.append(term)

    return terms


# Highlights the keywords in the input.
def highlight_keywords(text, kwds):
    for keyword in kwds:
        text = text.replace(keyword, highlight(keyword, COLOURS['cyan']))

    return text


# Highlights the text with a specified colour.
def highlight(text, colour):
    return f'{colour}{text}{COLOURS["empty"]}'


# Inserts empty lines between scenarios.
def separate_scenarios(report):
    lines = report.split("\n")
    for i, line in enumerate(lines):
        if not line.strip().startswith("When"):
            continue

        if i != 0 and lines[i - 1].strip().startswith("Given"):
            continue

        lines[i] = "\n" + line

    return "\n".join(lines)


report = sys.stdin.read()
report = separate_scenarios(report)
if len(sys.argv) == 2:
    TERMS_URL = sys.argv[1]
highlighted_report = highlight_keywords(report, read_keywords(TERMS_URL))
print(highlighted_report)
