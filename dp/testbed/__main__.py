# input() will use readline if imported
import readline  # noqa: F401

import argparse
import sqlite3
import decimal
import logging
import math
import os
from typing import Any

from dp.dotenv import load as load_dotenv

from .extract import extract_one
from .fetch import fetch, summarize
from .baseline import baseline
from .branch import branch
from .compare import compare
from .render import render
from .query import query
from .run import run_one
from .invoke import print_invocation
from .db import init_local_db

logger = logging.getLogger(__name__)


def adapt_decimal(d: decimal.Decimal) -> str:
    return str(d)


def convert_decimal(s: Any) -> decimal.Decimal:
    return decimal.Decimal(s)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda args: parser.print_usage())

    parser.add_argument('--db', action='store', default='testbed_db.db')
    parser.add_argument('-w', '--workers', action='store', type=int, help='how many workers to use to run parallel audits', default=max(math.floor((os.cpu_count() or 0) / 2), 1))

    subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands')

    parser_fetch = subparsers.add_parser('summarize', help='show stats for recent audit runs on the server')
    parser_fetch.set_defaults(func=summarize)

    parser_fetch = subparsers.add_parser('fetch', help='downloads audit results from a server')
    parser_fetch.add_argument('--latest', action='store_true', default=False, help='always fetch the latest run of audits')
    parser_fetch.add_argument('--run', action='store', type=int, help='fetch the Nth run of audits')
    parser_fetch.add_argument('--clear', action='store_true', default=False, help='clear the cached results table')
    parser_fetch.set_defaults(func=fetch)

    parser_baseline = subparsers.add_parser('baseline', help='runs a baseline audit benchmark')
    parser_baseline.add_argument('--min', dest='minimum_duration', default='30s', nargs='?', help='the minimum duration of audits to benchmark against')
    # parser_baseline.add_argument('--clear', action='store_true', default=False, help='clear the cached results table')
    parser_baseline.set_defaults(func=baseline)

    parser_branch = subparsers.add_parser('branch', help='runs an audit benchmark')
    parser_branch.add_argument('--min', dest='minimum_duration', default='30s', nargs='?', help='the minimum duration of audits to benchmark against')
    parser_branch.add_argument('--code', dest='filter', default=None, nargs='?', help='an area code to filter to')
    # parser_branch.add_argument('--clear', action='store_true', default=False, help='clear the cached results table')
    parser_branch.add_argument('branch', help='the git branch to compare against')
    parser_branch.set_defaults(func=branch)

    parser_compare = subparsers.add_parser('compare', help='compare an audit run against the baseline')
    parser_compare.add_argument('run', help='the run to compare against the base run')
    parser_compare.add_argument('base', default='baseline', nargs='?', help='the base run to compare against')
    parser_compare.add_argument('--mode', default='data', choices=['data', 'speed', 'all', 'ok', 'gpa'], help='the base run to compare against')
    parser_compare.set_defaults(func=compare)

    parser_print = subparsers.add_parser('print', help='show the baseline and branched audit results')
    parser_print.add_argument('branch', help='')
    parser_print.add_argument('stnum', help='')
    parser_print.add_argument('catalog')
    parser_print.add_argument('code')
    parser_print.add_argument('base', default='baseline', nargs='?', help='the base run to compare against')
    parser_print.add_argument('--diff', action='store_true', default=False)
    parser_print.set_defaults(func=render)

    parser_query = subparsers.add_parser('query', help='query the database')
    parser_query.add_argument('--stnum', default=None)
    parser_query.add_argument('--catalog', default=None)
    parser_query.add_argument('--code', default=None)
    parser_query.set_defaults(func=query)

    parser_run = subparsers.add_parser('run', help='run an audit against the current code')
    parser_run.add_argument('stnum', help='')
    parser_run.add_argument('catalog')
    parser_run.add_argument('code')
    parser_run.set_defaults(func=run_one)

    parser_run = subparsers.add_parser('invoke', help='')
    parser_run.add_argument('stnum', help='')
    parser_run.add_argument('catalog')
    parser_run.add_argument('code')
    parser_run.set_defaults(func=print_invocation)

    parser_extract = subparsers.add_parser('extract', help='extract input data for a student')
    parser_extract.add_argument('stnum', help='')
    parser_extract.add_argument('catalog')
    parser_extract.add_argument('code')
    parser_extract.set_defaults(func=extract_one)

    args = parser.parse_args()
    init_local_db(args)
    args.func(args)


if __name__ == "__main__":
    load_dotenv()

    # Register the adapter
    sqlite3.register_adapter(decimal.Decimal, adapt_decimal)

    # Register the converter
    sqlite3.register_converter("decimal", convert_decimal)

    try:
        main()
    except KeyboardInterrupt:
        pass
