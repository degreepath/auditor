from typing import Union, List, TypeVar, Mapping, Any, Tuple
from dataclasses import dataclass
import decimal
import enum

T = TypeVar('T')
U = TypeVar('U')


class Operator(enum.Enum):
    Eq = "="
    Neq = "!="
    Gte = ">="
    Gt = ">"
    Lt = "<"
    Lte = "<="
    Any = "ANY"
    Range = "RANGE"


@dataclass
class Student:
    ...


@dataclass
class All:
    items: List


@dataclass
class AnyClause:
    items: List


@dataclass
class Leaf:
    key: T
    op: Operator
    value: Union[U, List[U]]


Clause = Union[
    All,
    AnyClause,
    Leaf,
]


class CourseClauseAssertionKey(enum.Enum):
    CountCourses = 'count/courses'
    CountDistinct_courses = 'count/distinct_courses'
    CountTermsFromMostCommonCourse = 'count/terms-from-most-common-course'
    CountTermsFromMostCommonCourseByName = 'count/terms-from-most-common-course-by-name'
    CountSubjects = 'count/subjects'
    CountTerms = 'count/terms'
    CountYears = 'count/years'

    SumCredits = 'sum/credits'
    SumCreditsFromSingleSubject = 'sum/credits-from-single-subject'

    AverageGrades = 'average/grades'
    AverageCredits = 'average/credits'

    CountMathPerspectives = 'count/x/math-perspectives'
    CountReligionTraditions = 'count/x/religion-traditions'


class CourseClauseFilterKey(enum.Enum):
    Course = "course"
    Subject = "subject"
    Number = "number"


def load_clause__course_filter(key_s: str, operator: Operator, value: Any) -> Clause:
    key = CourseClauseFilterKey(key_s)

    if key in (CourseClauseFilterKey.Number,):
        if isinstance(value, str):
            value = int(value)
        elif isinstance(value, list):
            value = tuple(int(v) for v in value)

    return Leaf(key=key, op=operator, value=value)


def load_clause__course_assertion(key_s: str, operator: Operator, value: Any) -> Clause:
    key = CourseClauseAssertionKey(key_s)

    return Leaf(key=key, op=operator, value=value)


LeafClauseData = Union[
    str,
    Mapping[str, List[str]],
    Mapping[str, List[int]],
    Mapping[str, List[decimal.Decimal]],
]

ClauseData = Union[
    LeafClauseData,
    List[LeafClauseData],
]


def load_clause(mode: str, data: ClauseData, called: bool = False) -> Clause:
    value: Union[str, Tuple]

    if isinstance(data, str):
        key, op, value = data.split(maxsplit=2)
        operator = Operator(op)
        arguments = []

    elif isinstance(data, dict):
        assert len(data.keys()) == 1

        key = list(data.keys())[0]
        arguments = data[key]

        if key in ("and", "$and", "all"):
            ret1 = All(items=[load_clause(mode, item, called=True) for item in arguments])
            if not called: print(ret1)
            return ret1
        elif key in ("or", "$or", "any"):
            ret2 = AnyClause(items=[load_clause(mode, item, called=True) for item in arguments])
            if not called: print(ret2)
            return ret2

        key, op, value = key.split(maxsplit=2)
        operator = Operator(op)

        if value == "ANY":
            operator = Operator.Any
            value = tuple(arguments)
        elif value == "RANGE":
            operator = Operator.Range
            value = tuple(arguments)

        if operator in (Operator.Any, Operator.Range):
            assert len(value) > 0

    if mode == 'course/filter':
        ret = load_clause__course_filter(key, operator, value)
        if not called: print(ret)
        return ret

    elif mode == 'course/assert':
        ret = load_clause__course_assertion(key, operator, value)
        if not called: print(ret)
        return ret

    assert False


def test() -> None:
    load_clause("course/filter", "course = ENGL 101")

    load_clause("course/filter", {"course = ANY": ["ENGL", "MUSIC", "DANCE"]})

    load_clause("course/assert", "count/courses >= 1")

    load_clause("course/filter", {
        "all": [
            "course = ENGL 101",
        ],
    })

    load_clause("course/filter", {
        "all": [
            "course = ENGL 101",
            {"any": [
                {"subject = ANY": ["ENGL", "MUSIC", "DANCE"]},
                {"subject = RANGE": [270, 279]},
            ]},
        ],
    })


if __name__ == '__main__':
    test()
