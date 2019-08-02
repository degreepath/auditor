from degreepath.area import AreaOfStudy
from degreepath.data import course_from_str
from degreepath.constants import Constants
import pytest
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
          from: {student: courses}
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

    solutions = list(area.solutions(transcript=transcript, areas=[]))
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


def x_test_limits_asian(caplog):
    """
    result:
      from: {student: courses}
      limit:
        - at_most: 2
          where: {level: {$eq: 100}}
        - at_most: 4
          where: {attributes: {$eq: asian_region_china}}
        - at_most: 4
          where: {attributes: {$eq: asian_region_japan}}
      assert: {count(courses): {$gte: 6}}
    """
