#!/usr/bin/env python
import argparse
import os
import sys

from prompt_toolkit import prompt, PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

from typing import Iterator, Dict

from parser import split_query

import requests

sql_completer = WordCompleter([
    'select', 'where', 'from', 'desc', 'asc', 'and', 'or', 'interval'
], ignore_case=True)


style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})

def fetch_records(result) -> Iterator[Dict]:
    for record in result.json()["records"]:
        yield record["record"]["fields"]


def fetch_aggregations(result) -> Iterator[Dict]:
    for record in result.json()["aggregations"]:
        yield record


def display_results_in_table(records: Iterator[Dict]) -> Iterator[str]:
    # collect rows in a list
    # and compute width of each column
    rows = []
    fields = []
    field_width = []
    first_row = True
    for record in records:
        if first_row:
            fields = record.keys()
            field_width = [len(f) for f in fields]
            first_row = False

        for i, field in enumerate(fields):
            value_str = str(record[field])
            if len(value_str) > field_width[i]:
                field_width[i] = len(value_str)

        rows.append([str(record[field]) for field in fields])

    # display a table
    total_width = sum([w+3 for w in field_width]) + 1
    yield "-" * total_width + "\n"
    yield "| "
    for i, field in enumerate(fields):
        yield field + " " * (field_width[i] - len(field)) + " | "
    yield "\n"
    yield "-" * total_width + "\n"

    for row in rows:
        yield "| "
        for i, value in enumerate(row):
            yield value + " " * (field_width[i] - len(value)) + " | "
        yield "\n"


def output_with_elision(stream: Iterator[str], max_width: int) -> None:
    line = ""
    for fragment in stream:
        line += fragment
        if fragment.endswith("\n"):
            if len(line) > max_width:
                print(line[0:max_width-4] + "...")
            else:
                print(line[0:-1])
            line = ""

cli_parser = argparse.ArgumentParser(description="ODSQL Command line interface", add_help=False)
cli_parser.add_argument("-h", "--host", help="The HTTP host to connect to", required=True)
cli_parser.add_argument("-u", "--user", help="HTTP Basic auth username")
cli_parser.add_argument("-p", "--password", help="HTTP Basic auth password")
cli_parser.add_argument("--help", action="help", help="Show this message and exit")

def main():
    args = cli_parser.parse_args()
    
    if not args.password:
        args.password = prompt(
            'Password for user {}:'.format(args.user),
            is_password=True
        )

    session = PromptSession(
        lexer=PygmentsLexer(SqlLexer), completer=sql_completer, style=style)

    while True:
        try:
            text = session.prompt('> ')
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.

        q = split_query(text)

        params = {
            "select": q.select
        }
        endpoint = "records"
        if q.where:
            params["where"] = q.where
        if q.limit:
            params["rows"] = q.limit
        if q.offset:
            params["start"] = q.offset
        if q.group_by:
            endpoint = "aggregates"
            params["group_by"] = q.group_by
        if q.order_by:
            if endpoint == "records":
                params["sort"] = q.order_by
            else:
                params["order_by"] = q.order_by

        kw_auth = {}
        if args.user:
            kw_auth["auth"] = (args.user, args.password)

        r = requests.get(
                args.host + "/api/v2/catalog/datasets/{}/{}".format(q.from_, endpoint),
                params=params,
                **kw_auth
        )

        if r.status_code != 200:
            print(r.text)
            continue

        if endpoint == "records":
            rows = fetch_records(r)
        else:
            rows = fetch_aggregations(r)

        output_with_elision(
            display_results_in_table(rows),
            os.get_terminal_size().columns
        )

    print('GoodBye!')

if __name__ == '__main__':
    main()
