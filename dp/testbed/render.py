import argparse
import json
from typing import Optional, Dict

from .sqlite import sqlite_connect

from dp.data.student import Student
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

        student = Student.load(input_data)

        if not branch_result:
            print(render_result(student, baseline_result))
            return

        print('Baseline')
        print('========')
        print()
        print(render_result(student, baseline_result))
        print()
        print()
        label = f'Branch: {args.branch}'
        print(label)
        print('=' * len(label))
        print()
        print(render_result(student, branch_result))


def render_result(student: Student, result: Dict) -> str:
    transcript = {c.clbid: c for c in student.courses}

    return "\n".join(print_result(result, transcript=transcript, show_paths=False))
