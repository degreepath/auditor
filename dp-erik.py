import argparse
import json
import os
import sys
import pathlib
import time

import yaml
import dotenv
import psycopg2
import psycopg2.extras
import sentry_sdk

from degreepath import load_course, AreaOfStudy, Constants, AreaPointer
from degreepath.ms import pretty_ms

dotenv.load_dotenv(verbose=True)
if os.environ.get('SENTRY_DSN', None):
    sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'))
else:
    print('SENTRY_DSN not set; skipping', file=sys.stderr)

psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_file", required=True)
    parser.add_argument("--student", dest="student_file", required=True)
    args = parser.parse_args()
    main(student_file=args.student_file, area_file=args.area_file)


def main(area_file, student_file):
    conn = psycopg2.connect(
        host=os.environ.get("PG_HOST"),
        database=os.environ.get("PG_DATABASE"),
        user=os.environ.get("PG_USER"),
        password=os.environ.get("PG_PASSWORD"),
    )

    result_id = None

    try:
        with open(student_file, "r", encoding="utf-8") as infile:
            student = json.load(infile)
    except FileNotFoundError:
        print('could not find file "{student_file}"')
        sentry_sdk.capture_exception()
        return

    with sentry_sdk.configure_scope() as scope:
        scope.user = {"id": student["stnum"]}

    try:
        area_code = pathlib.Path(area_file).stem
        area_catalog = pathlib.Path(area_file).parent.stem

        area_pointers = tuple([AreaPointer.from_dict(**a) for a in student['areas']])

        try:
            with open(area_file, "r", encoding="utf-8") as infile:
                area = yaml.load(stream=infile, Loader=yaml.SafeLoader)
        except FileNotFoundError:
            sentry_sdk.capture_exception()

            with conn.cursor() as curs:
                curs.execute("""
                    INSERT INTO result (student_id, error, in_progress, area_code, catalog)
                    VALUES (%(student_id)s, %(error)s, false, %(code)s, %(catalog)s)
                """, {
                    "student_id": student["stnum"],
                    "error": {"error": f"could not find the area specification file for {area_code} {area_catalog} at {area_file}"},
                    "code": area_code,
                    "catalog": area_catalog,
                })
                conn.commit()

            return

        result_id = make_result_id(conn=conn, stnum=student["stnum"], area_code=area_code, catalog=area_catalog)

        if result_id is None:
            sentry_sdk.capture_message("skipped evaluation")
            return

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag('result_id', result_id)

        result_info = audit(student=student, spec=area, conn=conn, result_id=result_id, area_pointers=area_pointers)
        record(**result_info, conn=conn, result_id=result_id)

    except Exception as ex:
        sentry_sdk.capture_exception()

        print(ex, file=sys.stderr)

        if result_id:
            with conn.cursor() as curs:
                curs.execute("UPDATE result SET in_progress = false WHERE id = %(result_id)s", {"result_id": result_id})
                conn.commit()
    finally:
        conn.close()


def audit(*, student, spec, conn, result_id, area_pointers):
    constants = Constants(matriculation_year=student['matriculation'])
    area = AreaOfStudy.load(specification=spec, c=constants)
    area.validate()

    attributes_to_attach = area.attributes.get("courses", {})
    transcript = []
    for record in student["courses"]:
        c = load_course(record)

        attrs_by_course = set(attributes_to_attach.get(c.course(), []))
        attrs_by_shorthand = set(attributes_to_attach.get(c.course_shorthand(), []))
        attrs_by_term = set(attributes_to_attach.get(c.course_with_term(), []))

        c = c.attach_attrs(attributes=attrs_by_course | attrs_by_shorthand | attrs_by_term)
        transcript.append(c)

    transcript = tuple(transcript)

    #####

    best_sol = None
    total_count = 0
    times = []
    start = time.perf_counter()
    iter_start = time.perf_counter()

    for sol in area.solutions(transcript=transcript, areas=area_pointers):
        total_count += 1

        if total_count % 1000 == 0:
            update_progress(result_id=result_id, count=total_count, start=start, conn=conn)

        result = sol.audit(transcript=transcript, areas=area_pointers)

        if best_sol is None:
            best_sol = result

        if result.rank() > best_sol.rank():
            best_sol = result

        iter_end = time.perf_counter()
        times.append(iter_end - iter_start)

        if result.ok():
            best_sol = result
            break

        iter_start = time.perf_counter()

    end = time.perf_counter()
    elapsed = pretty_ms((end - start) * 1000)

    return {'result': result, 'times': times, 'elapsed': elapsed}


def record(*, result, times, conn, result_id, elapsed):
    result = result.to_dict()

    avg_iter_s = sum(times) / max(len(times), 1)
    avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

    claims = result["claims"]

    rank = result["rank"]
    ok = result["ok"]

    claims = []

    with conn.cursor() as curs:
        curs.execute("""
            UPDATE result
            SET iterations = %(total_count)s
              , duration = interval %(elapsed)s
              , per_iteration = interval %(avg_iter_time)s
              , rank = %(rank)s
              , result = %(result)s
              , claimed_courses = %(claims)s::jsonb
              , ok = %(ok)s
              , ts = now()
              , in_progress = false
            WHERE id = %(result_id)s
        """, {
            "result_id": result_id,
            "total_count": len(times),
            "elapsed": elapsed,
            "avg_iter_time": avg_iter_time.strip("~"),
            "result": json.dumps(result),
            "rank": rank,
            "claims": json.dumps(claims),
            "ok": False if ok is None else ok,
        })
        conn.commit()


def update_progress(*, conn, start_time, total_count, result_id):
    with conn.cursor() as curs:
        curs.execute("""
            UPDATE result
            SET iterations = %(total_count)s
              , duration = cast(now() - %(start)s as interval)
            WHERE id = %(result_id)s
        """, {
            "result_id": result_id,
            "total_count": total_count,
            "start": start_time,
        })

        conn.commit()


def make_result_id(*, stnum, conn, area_code, catalog):
    with conn.cursor() as curs:
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag('area_code', area_code)
            scope.set_tag('catalog', catalog)

        curs.execute("""
            INSERT INTO result (student_id, area_code, catalog, in_progress)
            VALUES (%(student_id)s, %(area_code)s, %(catalog)s, true)
            RETURNING id
        """, {"student_id": stnum, "area_code": area_code, "catalog": catalog})

        conn.commit()

        for record in curs:
            return record[0]


if __name__ == "__main__":
    cli()
