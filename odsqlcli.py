#!/usr/bin/env python
import argparse
import os
import sys

from prompt_toolkit import prompt, PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

from typing import Iterator, Dict

from parser import split_query_or_command

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

def fetch_catalog_datasets(result) -> Iterator[Dict]:
    for record in result.json()["datasets"]:
        yield {
            k: record["dataset"][k]
            for k in ("dataset_id", "dataset_uid", "has_records", "data_visible")
        }


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

    if not rows:
        yield "<empty>\n"
        return

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

    yield "-" * total_width + "\n"

    yield "({} row{})".format(len(rows), "s" if len(rows) > 0 else "") + "\n"


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


class OptionRegistry:
    options = {
        "debug": 0
    }

    def set_command(self, option_name, value):
        if option_name not in self.options:
            print("Unknown option {}".format(option_name))
            return

        self.options[option_name] = value

    def get(self, option_name):
        return self.options.get(option_name)

    def show_command(self, option_name):
        if option_name == "all":
            # list all
            for option, value in self.options.items():
                print("{} = {}".format(option, value))
        else:
            if option_name not in self.options:
                print("Unknown option {}".format(option_name))
                return
            print(self.options[option_name])


cli_parser = argparse.ArgumentParser(description="ODSQL Command line interface", add_help=False)
cli_parser.add_argument("-h", "--host", help="The HTTP host to connect to", required=True)
cli_parser.add_argument("-u", "--user", help="HTTP Basic auth username")
cli_parser.add_argument("-p", "--password", help="HTTP Basic auth password")
cli_parser.add_argument("--help", action="help", help="Show this message and exit")

RECORDS_ENDPOINT = "records"
AGGREGATIONS_ENDPOINT = "aggregates"
DATASETS_ENDPOINT = "catalog/datasets"
DATASET_AGGREGATIONS_ENDPOINT = "catalog/aggregates"

HISTORY_FILE = os.path.expanduser("~/.odsql_history")

def main():
    args = cli_parser.parse_args()
    options = OptionRegistry()
    
    if not args.password:
        args.password = prompt(
            'Password for user {}:'.format(args.user),
            is_password=True
        )

    session = PromptSession(
        lexer=PygmentsLexer(SqlLexer),
        completer=sql_completer,
        style=style,
        history=FileHistory(HISTORY_FILE)
    )

    print("Welcome. Type ODSQL queries ending with ';'")
    while True:
        try:
            query = ""
            first_line = True
            while True:
                fragment = session.prompt('> ' if first_line else ": ")
                first_line = False
                if fragment.strip().endswith(";"):
                    query += fragment
                    break
                query += fragment + "\n"
            query = query.strip("; \t\n")
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.

        q = split_query_or_command(query, options.get("debug"))

        if q.set_command is not None:
            option_name, value = q.set_command
            options.set_command(option_name, value)
            continue
        if q.show_command is not None:
            options.show_command(q.show_command)
            continue

        if q.from_ == "catalog":
            endpoint = DATASETS_ENDPOINT
        else:
            endpoint = RECORDS_ENDPOINT

        params = {
            "select": q.select
        }
        if q.where:
            params["where"] = q.where
        if q.limit is not None:
            params["rows"] = q.limit
        if q.offset is not None:
            params["start"] = q.offset
        if q.group_by:
            params["group_by"] = q.group_by
        if q.order_by:
            if endpoint in (RECORDS_ENDPOINT, DATASETS_ENDPOINT):
                params["sort"] = q.order_by
            else:
                params["order_by"] = q.order_by

        # Decide when to switch to aggregates
        if q.has_aggregate:
            if q.from_ == "catalog":
                endpoint = DATASET_AGGREGATIONS_ENDPOINT
            elif endpoint == RECORDS_ENDPOINT:
                endpoint = AGGREGATIONS_ENDPOINT

        kw_auth = {}
        if args.user:
            kw_auth["auth"] = (args.user, args.password)

        if endpoint.startswith("catalog"):
            url = args.host + "/api/v2/{}".format(endpoint)
        else:
            url = args.host + "/api/v2/catalog/datasets/{}/{}".format(q.from_, endpoint)

        if options.get("debug"):
            print("url:", url)
            print("params:", params)

        r = requests.get(
            url,
            params=params,
            **kw_auth
        )

        if r.status_code != 200:
            print(r.text)
            continue

        if endpoint == RECORDS_ENDPOINT:
            rows = fetch_records(r)
        elif endpoint == AGGREGATIONS_ENDPOINT:
            rows = fetch_aggregations(r)
        elif endpoint == DATASETS_ENDPOINT:
            rows = fetch_catalog_datasets(r)
        elif endpoint == DATASET_AGGREGATIONS_ENDPOINT:
            rows = fetch_aggregations(r)

        output_with_elision(
            display_results_in_table(rows),
            os.get_terminal_size().columns
        )

    print('GoodBye!')

if __name__ == '__main__':
    main()
