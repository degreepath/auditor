import argparse
import json

from .sqlite import sqlite_connect

from dp.data.student import Student
from .render import render_result
from .areas import load_areas
from .audit import audit


def run_one(args: argparse.Namespace) -> None:
    stnum = args.stnum
    catalog = args.catalog
    code = args.code

    with sqlite_connect(args.db, readonly=True) as conn:
        results = conn.execute('''
            SELECT d.input_data
            FROM server_data d
            WHERE (d.stnum) = (:stnum)
        ''', {'stnum': stnum})

        record = results.fetchone()
        input_data: dict = json.loads(record['input_data'])

    areas = load_areas(args, [{'catalog': catalog, 'code': code}])
    result_msg = audit((stnum, catalog, code), data=input_data, db=args.db, area_spec=areas[f"{catalog}/{code}"])
    assert result_msg

    student = Student.load(input_data)

    print(render_result(student, json.loads(result_msg['result'])))
