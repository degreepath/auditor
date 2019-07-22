from degreepath import *
import pytest
import io
import yaml
import ppretty

c = Constants(matriculation_year=2000)


def test_from():
    test_data = io.StringIO("""
        result:
            from: {student: courses, repeats: first}
            where: {gereqs: {$eq: SPM}}
            assert: {count(courses): {$gte: 1}}
    """)

    area = AreaOfStudy.load(specification=yaml.load(stream=test_data, Loader=yaml.SafeLoader), c=c)
    area.validate()

    transcript = [
        CourseInstance.from_s("CSCI 111", gereqs=['SPM'], term=20091),
        CourseInstance.from_s("CSCI 111", gereqs=['SPM'], term=20081),
        CourseInstance.from_s("ASIAN 110"),
    ]

    s = next(area.solutions(transcript=transcript))
    a = s.audit(transcript=transcript)

    assert len(a.successful_claims) == 1

    assert a.successful_claims[0].claim.clbid == transcript[1].clbid


def test_from_distinct():
    test_data = io.StringIO("""
        result:
            from: {student: courses}
            where: {gereqs: {$eq: SPM}}
            assert: {count(distinct_courses): {$gte: 1}}
    """)

    area = AreaOfStudy.load(specification=yaml.load(stream=test_data, Loader=yaml.SafeLoader), c=c)
    area.validate()

    transcript = [
        CourseInstance.from_s("CSCI 111", gereqs=['SPM'], term=20091),
        CourseInstance.from_s("CSCI 111", gereqs=['SPM'], term=20081),
        CourseInstance.from_s("CSCI 111", gereqs=['SPM'], term=20071),
        CourseInstance.from_s("ASIAN 110"),
    ]

    s = next(area.solutions(transcript=transcript))
    a = s.audit(transcript=transcript)

    assert len(a.successful_claims) == 1

    assert a.successful_claims[0].claim.clbid == transcript[0].clbid
