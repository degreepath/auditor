import glob
import json
import os
import time
import datetime

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
    parser.add_argument("--area", dest="area_files", nargs="+", required=True)
    parser.add_argument("--student", dest="student_files", nargs="+", required=True)
    args = parser.parse_args()

    areas = []
    for globset in args.area_files:
        for f in glob.iglob(globset):
            with open(f, "r", encoding="utf-8") as infile:
                a = yaml.load(stream=infile, Loader=yaml.SafeLoader)
            areas.append(a)

    students = []
    for file in args.student_files:
        with open(file, "r", encoding="utf-8") as infile:
            data = json.load(infile)
        students.append(data)

    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        database=os.getenv("PG_DATABASE"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
    )

    try:
        for student in students:
            transcript = []
            for row in student["courses"]:
                instance = CourseInstance.from_dict(**row)
                if instance:
                    transcript.append(instance)

            for area in areas:
                result_id = insert_student_record(conn=conn, student=student, area=area)

                audit(
                    area_def=area,
                    transcript=transcript,
                    student=student,
                    result_id=result_id,
                    conn=conn,
                )
    finally:
        conn.close()


def insert_student_record(*, student, area, conn):
    with conn.cursor() as curs:
        curs.execute(
            """
            INSERT INTO student (
                id
              , student_name, student_advisor, input_courses
              , degrees, majors, concentrations
              , matriculation_year, catalog_year, anticipated_graduation
            )
            VALUES (
                %(student_id)s
              , %(student_name)s, %(student_advisor)s, %(courses)s
              , %(degrees)s, %(majors)s, %(concentrations)s
              , %(matriculation_year)s, %(catalog_year)s, %(anticipated_graduation)s
            )
            ON CONFLICT (id)
            DO UPDATE SET student_name = %(student_name)s
                        , student_advisor = %(student_advisor)s
                        , degrees = %(degrees)s
                        , majors = %(majors)s
                        , concentrations = %(concentrations)s
                        , matriculation_year = %(matriculation_year)s
                        , catalog_year = %(catalog_year)s
                        , anticipated_graduation = %(anticipated_graduation)s
                        , input_courses = %(courses)s
            WHERE student.id = %(student_id)s
            """,
            {
                "student_id": str(student["stnum"]),
                "student_name": student["name"],
                "student_advisor": student["advisor"],
                "degrees": student["degrees"],
                "majors": student["majors"],
                "concentrations": student["concentrations"],
                "matriculation_year": student["matriculation"],
                "catalog_year": student["matriculation"],
                "anticipated_graduation": f"{student['graduation']}-05-31",
                "courses": json.dumps(student["courses"]),
            },
        )

        curs.execute(
            """
            INSERT INTO result (student_id, area_id)
            VALUES (
                %(student_id)s,
                (
                    SELECT id
                    FROM area
                    WHERE name = %(area_name)s
                        AND catalog_year = %(area_catalog)s
                        AND type = %(area_type)s
                        AND degree = %(area_degree)s
                )
            )
            RETURNING id
            """,
            {
                "student_id": student["stnum"],
                "area_name": area["name"],
                "area_catalog": int(area["catalog"][0:4]),
                "area_type": area["type"],
                "area_degree": area["degree"],
            },
        )

        conn.commit()

        result_id = curs.fetchone()[0]

        return result_id


def record_audit_result(*, conn, result_id, result, count, elapsed, iterations):
    avg_iter_s = sum(iterations) / max(len(iterations), 1)
    avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

    claims = result["claims"]
    del result["claims"]

    rank = result["rank"]
    ok = result["ok"]

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
                "total_count": count,
                "elapsed": elapsed,
                "avg_iter_time": avg_iter_time.strip("~"),
                "result": json.dumps(result),
                "rank": rank,
                "claims": json.dumps(claims),
                "ok": ok,
            },
        )
        conn.commit()


def audit(*, area_def, transcript, student, result_id=None, conn=None):
    area = AreaOfStudy.load(area_def)
    area.validate()

    this_transcript = []
    attributes_to_attach = area.attributes.get("courses", {})
    for c in transcript:
        attrs_by_course = attributes_to_attach.get(c.course(), [])
        attrs_by_shorthand = attributes_to_attach.get(c.course_shorthand(), [])

        c = c.attach_attrs(attributes=attrs_by_course or attrs_by_shorthand)
        this_transcript.append(c)

    best_sol = None
    total_count = 0
    times = []
    start = time.perf_counter()
    start_time = datetime.datetime.now()
    iter_start = time.perf_counter()

    for sol in area.solutions(transcript=this_transcript):
        total_count += 1

        if total_count % 1000 == 0:
            with conn.cursor() as curs:
                curs.execute(
                    """
                    UPDATE result
                    SET iterations = %(total_count)s
                      , duration = cast(now() - %(start)s as interval)
                    WHERE id = %(result_id)s
                    """,
                    {
                        "result_id": result_id,
                        "total_count": total_count,
                        "start": start_time,
                    },
                )
                conn.commit()

        result = sol.audit(transcript=this_transcript)

        if best_sol is None:
            best_sol = result

        if result.rank() > best_sol.rank():
            best_sol = result

        if result.ok():
            iter_end = time.perf_counter()
            times.append(iter_end - iter_start)
            break

        iter_end = time.perf_counter()
        times.append(iter_end - iter_start)

        iter_start = time.perf_counter()

    end = time.perf_counter()
    elapsed = pretty_ms((end - start) * 1000)

    record_audit_result(
        conn=conn,
        result_id=result_id,
        result=best_sol.to_dict(),
        count=total_count,
        elapsed=elapsed,
        iterations=times,
    )


if __name__ == "__main__":
    main()
