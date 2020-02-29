from .course_from_str import course_from_str
from dp.data.student import Student
from dp.area import AreaOfStudy
from dp.constants import Constants
import pytest  # type: ignore
import io
import yaml
import logging

c = Constants(matriculation_year=2000)


def test_global_limits(caplog):
    caplog.set_level(logging.DEBUG)

    test_data = io.StringIO("""
        limit:
          - at_most: 1
            where: {level: {$eq: 200}}
          - at_most: 1
            where: {level: {$eq: 300}}

        result:
          from: courses
          where: {subject: {$eq: BIO}}
          assert: {count(courses): {$gte: 1}}
    """)

    area = AreaOfStudy.load(specification=yaml.load(stream=test_data, Loader=yaml.SafeLoader), c=c)

    bio_101 = course_from_str("BIO 101")
    bio_201 = course_from_str("BIO 201")
    bio_202 = course_from_str("BIO 202")
    bio_301 = course_from_str("BIO 301")
    bio_302 = course_from_str("BIO 302")
    transcript = [bio_101, bio_201, bio_202, bio_301, bio_302]

    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[]))
    course_sets = set([frozenset(s.solution.output) for s in solutions])

    assert course_sets == set([
        frozenset((bio_101, bio_201)),
        frozenset((bio_101, bio_201, bio_301)),
        frozenset((bio_101, bio_201, bio_302)),
        frozenset((bio_101, bio_202)),
        frozenset((bio_101, bio_202, bio_301)),
        frozenset((bio_101, bio_202, bio_301)),
        frozenset((bio_101, bio_202, bio_302)),
        frozenset((bio_101, bio_301)),
        frozenset((bio_101, bio_302)),
        frozenset((bio_101,)),
        frozenset((bio_201, bio_301)),
        frozenset((bio_201, bio_302)),
        frozenset((bio_201,)),
        frozenset((bio_202, bio_301)),
        frozenset((bio_202, bio_302)),
        frozenset((bio_202,)),
        frozenset((bio_301,)),
        frozenset((bio_302,)),
    ])


def test_limits_esth(caplog):
    spec = """
    result:
      from: courses
      limit:
        - at_most: 1
          where:
            $or:
              - course: {$in: ['STAT 110', 'STAT 212', 'STAT 214']}
              - ap: {$eq: AP Statistics}
      assert: {count(courses): {$gte: 2}}
    """

    area = AreaOfStudy.load(specification=yaml.load(stream=spec, Loader=yaml.SafeLoader), c=c)

    psych_241 = course_from_str("PSYCH 241", clbid="0")
    stat_212 = course_from_str("STAT 212", clbid="1")
    ap_stat = course_from_str("STAT 0", name="AP Statistics", course_type="AP", clbid="2")
    transcript = [psych_241, stat_212, ap_stat]

    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[]))
    course_sets = [list(s.solution.output) for s in solutions]

    assert course_sets == [
        [psych_241],
        [psych_241, stat_212],
        [psych_241, ap_stat],
    ]
