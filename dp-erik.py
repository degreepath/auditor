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

from degreepath import (
    CourseInstance,
    AreaOfStudy,
    CourseStatus,
    Operator,
    str_clause,
    str_assertion,
    pretty_ms,
)


psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)
dotenv.load_dotenv(verbose=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_file", required=True)
    parser.add_argument("--student", dest="student_file", required=True)
    args = parser.parse_args()

    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        database=os.getenv("PG_DATABASE"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
    )

    try:
        with open(args.student_file, "r", encoding="utf-8") as infile:
            student = json.load(infile)
    except FileNotFoundError:
        print('could not find file "{}"'.format(args.student_file))
        return

    try:
        try:
            with open(args.area_file, "r", encoding="utf-8") as infile:
                area = yaml.load(stream=infile, Loader=yaml.SafeLoader)
        except FileNotFoundError:
            with conn.cursor() as curs:
                curs.execute("""
                    INSERT INTO result (student_id, error)
                    VALUES (%(student_id)s, %(error)s)
                    RETURNING id
                """, {
                    "student_id": student["stnum"],
                    "error": {"error": "could not find the area specification file"},
                })
                conn.commit()
            return

        result_id = make_result_id(conn=conn, student=student, area=area)

        if result_id is None:
            return

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
    finally:
        conn.close()


def make_result_id(student, area, conn):
    with conn.cursor() as curs:
        area_degree = area.get('degree', None)
        if area_degree == 'Bachelor of Arts':
            area_degree = 'B.A.'
        elif area_degree == 'Bachelor of Arts':
            area_degree = 'B.M.'

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
            "area_name": area["name"],
            "area_catalog": int(area["catalog"][0:4]),
            "area_type": area["type"],
            "area_degree": area_degree,
        })

        area_id = None
        for record in curs:
            area_id = record[0]

        if area_id is None:
            curs.execute("""
                INSERT INTO result (student_id, error)
                VALUES (%(student_id)s, %(error)s)
            """, {
                "student_id": student["stnum"],
                "error": {"error": "could not find the area in the database"},
            })
            conn.commit()
            return None

        curs.execute("""
            INSERT INTO result (student_id, area_id)
            VALUES (%(student_id)s, %(area_id)s)
            RETURNING id
        """, {"student_id": student["stnum"], "area_id": area_id})

        conn.commit()

        for record in curs:
            return record[0]


if __name__ == "__main__":
    main()
