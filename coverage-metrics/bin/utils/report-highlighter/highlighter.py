#!/usr/bin/env python3

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


# KeywordsReader reads the list of keywords from the remote Wiki page.
class KeywordsReader:
    def __init__(self, file_url):
        with urlopen(file_url) as response:
            body = str(response.read().decode('utf-8'))
            self._lines = body.split('\n')

        self._terms_index = 0
        self._terms_table_index = 0

    # Returns the list of terms from the parsed Wiki page.
    def read(self):
        self._find_terms_section()
        self._find_table()
        return self._read_table_terms()

    # Skips all the lines in the source until the ## Terms section.
    def _find_terms_section(self):
        for i, l in enumerate(self._lines):
            if l.startswith("## Terms"):
                self._terms_index = i
                break

    # Skips all the lines until the table node is found.
    def _find_table(self):
        for i in range(self._terms_index + 1, len(self._lines)):
            if self._lines[i].startswith("| Term "):
                self._terms_table_index = i
                break

    # Returns the terms from the first column of the table.
    def _read_table_terms(self):
        keys = []
        for i in range(self._terms_table_index + 2, len(self._lines)):
            table_line = self._lines[i]
            if not table_line.startswith("| "):
                break

            keys.append(table_line[1:table_line.find("|", 1)].strip())

        return keys


# Highlights the keywords in the input.
def highlight_keywords(text, kwds):
    for keyword in kwds:
        text = text.replace(keyword, highlight(keyword, COLOURS['cyan']))

    return text


# Highlights the text with a specified colour.
def highlight(text, colour):
    return f'{colour}{text}{COLOURS["empty"]}'


report = sys.stdin.read()
if len(sys.argv) == 2:
    TERMS_URL = sys.argv[1]
highlighted_report = highlight_keywords(report, KeywordsReader(TERMS_URL).read())
print(highlighted_report)
