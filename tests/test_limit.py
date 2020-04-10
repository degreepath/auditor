from dp.area import AreaOfStudy
from dp.data.student import Student
from dp.data.course import course_from_str
from dp.constants import Constants
import io
import yaml

c = Constants(matriculation_year=2000)


def test_limit__at_most_1_course():
    test_data = io.StringIO("""
        limit:
          - at_most: 1
            where: {number: {$eq: 201}}

        result:
          from: courses
          where: {number: {$eq: 201}}
          assert: {count(courses): {$gte: 1}}
    """)

    area = AreaOfStudy.load(specification=yaml.load(stream=test_data, Loader=yaml.SafeLoader), c=c)

    course_1 = course_from_str("BIO 201")
    course_2 = course_from_str("ABC 201")
    transcript = [course_1, course_2]

    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[]))
    course_sets = set(frozenset(s.solution.output) for s in solutions)

    assert course_sets == set([
        frozenset((course_2,)),
        frozenset((course_1,)),
        frozenset(()),
    ])


def test_limit__at_most_1_credit():
    test_data = io.StringIO("""
        limit:
          - at_most: 1 credit
            where: {number: {$eq: 201}}

        result:
          from: courses
          assert: {count(courses): {$gte: 1}}
    """)

    area = AreaOfStudy.load(specification=yaml.load(stream=test_data, Loader=yaml.SafeLoader), c=c)

    course_1 = course_from_str("ABC 201", credits='0.5')
    course_2 = course_from_str("BCD 201", credits='0.5')
    course_3 = course_from_str("CDE 201", credits='0.5')
    transcript = [course_1, course_2, course_3]

    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[]))
    course_sets = set(frozenset(s.solution.output) for s in solutions)

    for i, s in enumerate(course_sets):
        print(i)
        for _c in s:
            print(_c.course())

    assert course_sets == set([
        frozenset((course_1, course_2)),
        frozenset((course_1, course_3)),
        frozenset((course_2, course_3)),
        frozenset((course_1,)),
        frozenset((course_2,)),
        frozenset((course_3,)),
        frozenset(()),
    ])
