import argparse
import json
from typing import Optional, Dict

from .sqlite import sqlite_connect

from dp.data.course import load_course
from dp.stringify import print_result


def render(args: argparse.Namespace) -> None:
    stnum = args.stnum
    catalog = args.catalog
    code = args.code
    branch = args.branch

    input_data: Optional[Dict]
    baseline_result: Optional[Dict]
    branch_result: Optional[Dict] = None

    with sqlite_connect(args.db, readonly=True) as conn:
        if branch == 'server':
            results = conn.execute('''
                SELECT d.input_data, d.result as output
                FROM server_data d
                WHERE d.stnum = :stnum
                    AND d.catalog = :catalog
                    AND d.code = :code
            ''', {'catalog': catalog, 'code': code, 'stnum': stnum})

            record = results.fetchone()
            assert record, {'catalog': catalog, 'code': code, 'stnum': stnum}

            input_data = json.loads(record['input_data'])
            baseline_result = json.loads(record['output'])

        elif branch == 'baseline':
            results = conn.execute('''
                SELECT d.input_data, b1.result as output
                FROM server_data d
                LEFT JOIN baseline b1 ON (b1.stnum, b1.catalog, b1.code) = (d.stnum, d.catalog, d.code)
                WHERE d.stnum = :stnum
                    AND d.catalog = :catalog
                    AND d.code = :code
            ''', {'catalog': catalog, 'code': code, 'stnum': stnum})

            record = results.fetchone()
            assert record, {'catalog': catalog, 'code': code, 'stnum': stnum}

            input_data = json.loads(record['input_data'])
            baseline_result = json.loads(record['output'])

        else:
            results = conn.execute('''
                SELECT d.input_data, b1.result as baseline, b2.result as branch
                FROM server_data d
                LEFT JOIN baseline b1 ON (b1.stnum, b1.catalog, b1.code) = (d.stnum, d.catalog, d.code)
                LEFT JOIN branch b2 ON (b2.stnum, b2.catalog, b2.code) = (d.stnum, d.catalog, d.code)
                WHERE d.stnum = :stnum
                    AND d.catalog = :catalog
                    AND d.code = :code
                    AND b2.branch = :branch
            ''', {'catalog': catalog, 'code': code, 'stnum': stnum, 'branch': branch})

            record = results.fetchone()
            assert record, {'catalog': catalog, 'code': code, 'stnum': stnum, 'branch': branch}

            input_data = json.loads(record['input_data'])
            baseline_result = json.loads(record['baseline'])
            branch_result = json.loads(record['branch'])

        assert input_data
        assert baseline_result

        if not branch_result:
            print(render_result(input_data, baseline_result))
            return

        print('Baseline')
        print('========\n')
        print(render_result(input_data, baseline_result))
        print()
        print()
        print(f'Branch: {args.branch}')
        print('========\n')
        print(render_result(input_data, branch_result))


def render_result(student_data: Dict, result: Dict) -> str:
    courses = [load_course(row, overrides=[]) for row in student_data["courses"]]
    transcript = {c.clbid: c for c in courses}

    return "\n".join(print_result(result, transcript=transcript, show_paths=False))
