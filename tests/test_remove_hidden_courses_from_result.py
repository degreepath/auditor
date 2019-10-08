from degreepath import AreaOfStudy
from degreepath.data import course_from_str
from degreepath.constants import Constants
from decimal import Decimal
from degreepath.rule.course import CourseRule
from degreepath.result.course import CourseResult

c = Constants(matriculation_year=2000)


def test_hidden_and_taken_so_shown():
    """
    Because the input course matches a hidden option, the matched hidden option
    is retained in the list.
    """
    transcript = [
        course_from_str('CSCI 251', grade_points_gpa=Decimal('3.0')),
    ]

    area = AreaOfStudy.load(c=c, transcript=transcript, specification={
        'name': 'test',
        'type': 'concentration',
        'result': {
            'any': [
                {'course': 'CSCI 251', 'hidden': True},
                {'course': 'CSCI 275', 'hidden': True},
                {'course': 'ART 101', 'hidden': False},
            ],
        },
    })

    solution = list(area.solutions(transcript=transcript, areas=[], exceptions=[]))[0]

    result = solution.audit()

    assert result.matched() == set([transcript[0]])

    assert len(result.result.items) == 2
    assert [r.course for r in result.result.items] == ['CSCI 251', 'ART 101']


def test_hidden_and_taken_so_shown_2():
    """
    Because all of the input courses match the hidden options, the hidden options
    are retained in the list.
    """
    transcript = [
        course_from_str('CSCI 251', grade_points_gpa=Decimal('3.0')),
        course_from_str('CSCI 275', grade_points_gpa=Decimal('2.0')),
        course_from_str('ART 101', grade_points_gpa=Decimal('1.0')),
    ]

    area = AreaOfStudy.load(c=c, transcript=transcript, specification={
        'name': 'test',
        'type': 'concentration',
        'result': {
            'any': [
                {'course': 'CSCI 251', 'hidden': True},
                {'course': 'CSCI 275', 'hidden': True},
                {'course': 'ART 101', 'hidden': False},
            ],
        },
    })

    solution = list(area.solutions(transcript=transcript, areas=[], exceptions=[]))[0]

    result = solution.audit()

    assert result.matched() == set(transcript)

    assert len(result.result.items) == 3
    assert [r.course for r in result.result.items] == ['CSCI 251', 'CSCI 275', 'ART 101']


def test_hidden_and_taken_so_shown_3():
    """
    Because none of the input courses match the hidden options, the hidden options
    are removed from the list.
    """
    transcript = [
        course_from_str('ART 101', grade_points_gpa=Decimal('1.0')),
    ]

    area = AreaOfStudy.load(c=c, transcript=transcript, specification={
        'name': 'test',
        'type': 'concentration',
        'result': {
            'any': [
                {'course': 'CSCI 251', 'hidden': True},
                {'course': 'CSCI 275', 'hidden': True},
                {'course': 'ART 101', 'hidden': False},
            ],
        },
    })

    solution = list(area.solutions(transcript=transcript, areas=[], exceptions=[]))[0]

    result = solution.audit()

    assert result.matched() == set(transcript)

    assert isinstance(result.result, CourseResult)
    assert result.result.course == 'ART 101'


def test_hidden_and_taken_so_shown_4():
    """
    Because there are no input courses that match, the hidden courses
    are removed from the list of options.
    """
    transcript = []

    area = AreaOfStudy.load(c=c, transcript=transcript, specification={
        'name': 'test',
        'type': 'concentration',
        'result': {
            'any': [
                {'course': 'CSCI 251', 'hidden': True},
                {'course': 'CSCI 275', 'hidden': True},
                {'course': 'ART 101', 'hidden': False},
            ],
        },
    })

    solution = list(area.solutions(transcript=transcript, areas=[], exceptions=[]))[0]

    result = solution.audit()

    assert result.matched() == set(transcript)

    assert isinstance(result.result, CourseRule)
    assert result.result.course == 'ART 101'


def test_hidden_and_taken_so_shown_5():
    """
    Because the input course matches a hidden option, the matched hidden option
    is retained in the list.
    """
    transcript = [
        course_from_str('CSCI 251', grade_points_gpa=Decimal('3.0')),
        course_from_str('ART 101', grade_points_gpa=Decimal('3.0')),
    ]

    area = AreaOfStudy.load(c=c, transcript=transcript, specification={
        'name': 'test',
        'type': 'concentration',
        'result': {
            'all': [
                {'course': 'CSCI 251', 'hidden': True},
                {'course': 'CSCI 275', 'hidden': True},
                {'course': 'ART 101', 'hidden': False},
            ],
        },
    })

    solution = list(area.solutions(transcript=transcript, areas=[], exceptions=[]))[0]

    result = solution.audit()

    assert result.matched() == set([transcript[0], transcript[1]])

    assert result.result.count == 2
    assert len(result.result.items) == 2
    assert [r.course for r in result.result.items] == ['CSCI 251', 'ART 101']
