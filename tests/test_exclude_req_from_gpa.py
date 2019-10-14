from degreepath import AreaOfStudy
from degreepath.data import course_from_str
from degreepath.constants import Constants
from decimal import Decimal

c = Constants(matriculation_year=2000)


def trns():
    return [
        course_from_str('CSCI 251', grade_points_gpa=Decimal('3.0')),
        course_from_str('CSCI 275', grade_points_gpa=Decimal('2.0')),
        course_from_str('ART 101', grade_points_gpa=Decimal('1.0')),
    ]


def test_normal_gpa():
    transcript = trns()

    area = AreaOfStudy.load(c=c, transcript=transcript, specification={
        'name': 'test',
        'type': 'concentration',
        'result': {
            'all': [
                {'requirement': 'compsci'},
                {'requirement': 'art'},
            ],
        },
        'requirements': {
            'compsci': {
                'result': {
                    'from': 'courses',
                    'where': {'subject': {'$eq': 'CSCI'}},
                    'assert': {'count(courses)': {'$gte': 2}},
                }
            },
            'art': {
                'result': {
                    'from': 'courses',
                    'where': {'subject': {'$eq': 'ART'}},
                    'assert': {'count(courses)': {'$gte': 1}},
                },
            },
        },
    })

    solution = list(area.solutions(transcript=transcript, areas=[], exceptions=[]))[0]

    result = solution.audit()

    assert set(result.matched()) == set(transcript)

    assert result.gpa() == Decimal('2.0')


def test_excluded_req_gpa():
    transcript = trns()

    area = AreaOfStudy.load(c=c, transcript=transcript, specification={
        'name': 'test',
        'type': 'concentration',
        'result': {
            'all': [
                {'requirement': 'compsci'},
                {'requirement': 'art'},
            ],
        },
        'requirements': {
            'compsci': {
                'result': {
                    'from': 'courses',
                    'where': {'subject': {'$eq': 'CSCI'}},
                    'assert': {'count(courses)': {'$gte': 2}},
                }
            },
            'art': {
                'in_gpa': False,
                'result': {
                    'from': 'courses',
                    'where': {'subject': {'$eq': 'ART'}},
                    'assert': {'count(courses)': {'$gte': 1}},
                },
            },
        },
    })

    solution = list(area.solutions(transcript=transcript, areas=[], exceptions=[]))[0]
    result = solution.audit()

    assert area.result.items[1].in_gpa is False

    assert set(result.matched_for_gpa()) == set([transcript[0], transcript[1]])
    assert transcript[2] not in set(result.matched_for_gpa())

    assert result.gpa() == Decimal('2.5')
