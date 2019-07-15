import argparse
import datetime
import glob
import json
import os
import time

import yaml
import dotenv
import psycopg2
import psycopg2.extras
import sentry_sdk

from degreepath import (
    CourseInstance,
    AreaOfStudy,
    CourseStatus,
    Operator,
    str_clause,
    str_assertion,
    pretty_ms,
)


dotenv.load_dotenv(verbose=True)
if os.environ.get('SENTRY_DSN', None):
    sentry_sdk.init(dsn='http://b5ea900bd6e8496984ba360f8c5f36a0:976e13ab96f14ed7ac0cbe253ae7feb0@10.4.136.201:9000/6')

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
        print('could not find file "{}"'.format(student_file))
        sentry_sdk.capture_exception()
        return

    with sentry_sdk.configure_scope() as scope:
        scope.user = {"id": student["stnum"]}

    try:
        try:
            with open(area_file, "r", encoding="utf-8") as infile:
                area = yaml.load(stream=infile, Loader=yaml.SafeLoader)
        except FileNotFoundError:
            with conn.cursor() as curs:
                err = "could not find the area specification file at {}".format(area_file)
                curs.execute("""
                    INSERT INTO result (student_id, error)
                    VALUES (%(student_id)s, %(error)s)
                """, {
                    "student_id": student["stnum"],
                    "error": {"error": err},
                })
                conn.commit()
                sentry_sdk.capture_exception(Exception(err))
            return

        result_id = make_result_id(conn=conn, student=student, area=area, path=area_file)

        if result_id is None:
            sentry_sdk.capture_exception(Exception("skipped evaluation"))
            return

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag('result_id', result_id)

        #####

        area = AreaOfStudy.load(area)
        area.validate()

        attributes_to_attach = area.attributes.get("courses", {})
        transcript = []
        for record in student["courses"]:
            c = CourseInstance.from_dict(**record)

            if c is None:
                continue

            attrs_by_course = attributes_to_attach.get(c.course(), [])
            attrs_by_shorthand = attributes_to_attach.get(c.course_shorthand(), [])

            c = c.attach_attrs(attributes=attrs_by_course or attrs_by_shorthand)
            transcript.append(c)

        #####

        best_sol = None
        total_count = 0
        times = []
        start = time.perf_counter()
        start_time = datetime.datetime.now()
        iter_start = time.perf_counter()

        for sol in area.solutions(transcript=transcript):
            total_count += 1

            if total_count % 1000 == 0:
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

            result = sol.audit(transcript=transcript)

            if best_sol is None:
                best_sol = result

            if result.rank() > best_sol.rank():
                best_sol = result

            iter_end = time.perf_counter()
            times.append(iter_end - iter_start)

            if result.ok():
                break

            iter_start = time.perf_counter()

        end = time.perf_counter()
        elapsed = pretty_ms((end - start) * 1000)

        #####

        result = best_sol.to_dict()

        avg_iter_s = sum(times) / max(len(times), 1)
        avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

        claims = result["claims"]
        del result["claims"]

        rank = result["rank"]
        ok = result["ok"]

        claims = []

        with conn.cursor() as curs:
            curs.execute(
                """
                    UPDATE result
                    SET iterations = %(total_count)s
                      , duration = interval %(elapsed)s
                      , per_iteration = interval %(avg_iter_time)s
                      , rank = %(rank)s
                      , result = %(result)s
                      , claimed_courses = %(claims)s::jsonb
                      , ok = %(ok)s
                      , ts = now()
                    WHERE id = %(result_id)s
                """,
                {
                    "result_id": result_id,
                    "total_count": total_count,
                    "elapsed": elapsed,
                    "avg_iter_time": avg_iter_time.strip("~"),
                    "result": json.dumps(result),
                    "rank": rank,
                    "claims": json.dumps(claims),
                    "ok": ok,
                },
            )
            conn.commit()
    except Exception as ex:
        sentry_sdk.capture_exception()

        import traceback

        with conn.cursor() as curs:
            tb = ''.join(traceback.format_exception(
                etype=type(ex),
                value=ex,
                tb=ex.__traceback__,
            ))

            curs.execute("""
                INSERT INTO result (student_id, id, error)
                VALUES (%(student_id)s, %(result_id)s, %(error)s)
                ON CONFLICT (id) DO UPDATE
                SET error = %(error)s
            """, {
                "student_id": student["stnum"],
                "error": {
                    "error": "{}".format(ex),
                    "student": student_file,
                    "area": area_file,
                    "trace": tb,
                },
                "result_id": result_id,
            })
            conn.commit()
    finally:
        conn.close()


def make_result_id(*, student, area, conn, path):
    with conn.cursor() as curs:
        area_degree = area.get('degree', None)
        area_name = area.get('name', None)
        if area_degree == 'Bachelor of Arts':
            area_degree = 'B.A.'
            if area_name == 'Bachelor of Arts':
                area_name = 'B.A.'
        elif area_degree == 'Bachelor of Music':
            area_degree = 'B.M.'
            if area_name == 'Bachelor of Music':
                area_name = 'B.M.'

        curs.execute("""
            SELECT id
            FROM area
            WHERE name = %(area_name)s
              AND catalog_year = %(area_catalog)s
              AND type = %(area_type)s
              AND CASE type WHEN 'degree'
                    THEN true
                    ELSE degree = %(area_degree)s
                  END
        """, {
            "area_name": area_name,
            "area_catalog": int(area["catalog"][0:4]),
            "area_type": area["type"],
            "area_degree": area_degree,
        })

        area_id = None
        for record in curs:
            area_id = record[0]

        if area_id is None:
            err = "could not find the area {} in the database".format(path)
            sentry_sdk.capture_exception(Exception(err))
            curs.execute("""
                INSERT INTO result (student_id, error)
                VALUES (%(student_id)s, %(error)s)
            """, {
                "student_id": student["stnum"],
                "error": {"error": err},
            })
            conn.commit()
            return None

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag('area_id', area_id)

        curs.execute("""
            INSERT INTO result (student_id, area_id)
            VALUES (%(student_id)s, %(area_id)s)
            RETURNING id
        """, {"student_id": student["stnum"], "area_id": area_id})

        conn.commit()

        for record in curs:
            return record[0]


if __name__ == "__main__":
    cli()
