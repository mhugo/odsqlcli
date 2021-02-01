#!/usr/bin/env python
import argparse
import os
import sys
import time

from prompt_toolkit import prompt, PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

from typing import Iterator, Dict, Optional, Tuple

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


def fetch_records(result: Dict) -> Iterator[Dict]:
    for record in result["records"]:
        yield record["record"]["fields"]


def fetch_aggregations(result: Dict) -> Iterator[Dict]:
    for record in result["aggregations"]:
        yield record


def fetch_catalog_datasets(result: Dict) -> Iterator[Dict]:
    for record in result["datasets"]:
        yield record["dataset"]
        #yield {
        #    k: record["dataset"][k]
        #    for k in ("dataset_id", "dataset_uid", "has_records", "data_visible")
        #}


def display_results_in_table(records: Iterator[Dict], total_count : Optional[int] = None) -> Iterator[str]:
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

    yield "({} row{}{})".format(
        len(rows),
        "s" if len(rows) > 1 else "",
        " on a total of {}".format(total_count) if total_count else "") + "\n"


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

def simple_output(stream: Iterator[str]) -> None:
    for line in stream:
        if line.endswith("\n"):
            print(line[0:-1])
        else:
            print(line, end="")


class OptionRegistry:
    options = {
        # option_name: [Description, value]
        "debug": ["Be verbose", int, 0],
        "force_records": ["Force the records endpoint when both aggregates and records are possible", int, 0],
        "truncate_lines": ["Truncate long lines that are wider than the screen width", int, 1],
        "display_timing": ["Display timing", int, 0],
        "timezone": ["Current timezone", str, "Europe/Paris"]
    }

    def set_command(self, option_name, value):
        if option_name not in self.options:
            print("Unknown option {}".format(option_name))
            return

        type = self.options[option_name][1]
        try:
            self.options[option_name][2] = type(value)
        except ValueError:
            print("Wrong type for option, expected: {}".format(type.__name__))

    def get(self, option_name):
        return self.options.get(option_name)[2]

    def show_command(self, option_name):
        if option_name == "all":
            # list all
            for option, desc_value in self.options.items():
                print("{} - ({}:{}) = {}".format(option, desc_value[1].__name__, desc_value[0], desc_value[2]))
        else:
            if option_name not in self.options:
                print("Unknown option {}".format(option_name))
                return
            print(self.get(option_name))


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


class APIRequester(object):

    def __init__(self, host: str, basic_auth: Optional[Tuple[str, str]] = None):
        self.__host = host
        self.__basic_auth = {"auth": basic_auth} if basic_auth else {}

    def get(self, endpoint: str, get_parameters: Optional[Dict[str, str]] = None) -> requests.models.Response:
        return requests.get(
            self.__host + endpoint,
            params=get_parameters,
            **self.__basic_auth
        )

    def fetch_dataset_schema(self, dataset_name: str) -> Iterator[Dict]:
        # FIXME where clause ?
        r = self.get("/api/v2/catalog/datasets")
        if r.status_code != 200:
            print(r.text)
            raise StopIteration
        results = r.json()
        for dataset in results["datasets"]:
            ds = dataset["dataset"]
            if ds["dataset_id"] != dataset_name:
                continue
            for field in ds["fields"]:
                yield field


def main():
    args = cli_parser.parse_args()
    options = OptionRegistry()

    if not args.password:
        args.password = prompt(
            'Password for user {}:'.format(args.user),
            is_password=True
        )

    basic_auth = None
    if args.user:
        basic_auth = (args.user, args.password)

    requester = APIRequester(args.host, basic_auth=basic_auth)

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
        if q.schema_command is not None:
            output_with_elision(
                display_results_in_table(requester.fetch_dataset_schema(q.schema_command)),
                os.get_terminal_size().columns
            )
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
        if q.group_by or (q.has_aggregate and not options.get("force_records")):
            if q.from_ == "catalog":
                endpoint = DATASET_AGGREGATIONS_ENDPOINT
            elif endpoint == RECORDS_ENDPOINT:
                endpoint = AGGREGATIONS_ENDPOINT

        if endpoint.startswith("catalog"):
            api_endpoint = "/api/v2/{}".format(endpoint)
        else:
            api_endpoint = "/api/v2/catalog/datasets/{}/{}".format(q.from_, endpoint)

        params["timezone"] = options.get("timezone")

        if options.get("debug"):
            print("url:", api_endpoint)
            print("params:", params)

        start_t = time.time()
        r = requester.get(api_endpoint, get_parameters=params)
        request_elapsed = time.time() - start_t

        if r.status_code != 200:
            print(r.text)
            continue

        results = r.json()
        total_count = None
        if endpoint == RECORDS_ENDPOINT:
            rows = fetch_records(results)
            total_count = results["total_count"]
        elif endpoint == AGGREGATIONS_ENDPOINT:
            rows = fetch_aggregations(results)
        elif endpoint == DATASETS_ENDPOINT:
            rows = fetch_catalog_datasets(results)
        elif endpoint == DATASET_AGGREGATIONS_ENDPOINT:
            rows = fetch_aggregations(results)

        if options.get("truncate_lines"):
            output_with_elision(
                display_results_in_table(rows, total_count),
                os.get_terminal_size().columns
            )
        else:
            simple_output(
                display_results_in_table(rows, total_count),
            )

        if options.get("display_timing"):
            print("Request time: {:0.2g}s".format(request_elapsed))

    print('GoodBye!')

if __name__ == '__main__':
    main()
