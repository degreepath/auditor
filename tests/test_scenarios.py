from dp import AreaOfStudy, Constants, AreaPointer
from dp.audit import audit, Arguments
from dp.data.course import course_from_str
from dp.data.student import Student
from dp.data.area_enums import AreaStatus, AreaType
from typing import Dict, Any


def test_audit__double_history_and_studio():
    student: Dict[str, Any] = {
        'areas': [
            AreaPointer(
                code='140',
                status=AreaStatus.Declared,
                kind=AreaType.Major,
                name='Studio Art',
                degree='B.A.',
                dept='ART',
                gpa=None,
                terms_since_declaration=None,
            ),
            AreaPointer(
                code='135',
                status=AreaStatus.Declared,
                kind=AreaType.Major,
                name='Art History',
                degree='B.A.',
                dept='ART',
                gpa=None,
                terms_since_declaration=None,
            ),
        ],
        'courses': [
            course_from_str('DEPT 123'),
        ],
    }

    c = Constants(matriculation_year=2000)

    area = AreaOfStudy.load(c=c, student=Student.load(dict(areas=student['areas'], courses=student['courses'])), specification={
        'name': 'Art History Test',
        'type': 'major',
        'code': '140',
        'degree': 'B.A.',

        'result': {
            'all': [{'course': 'DEPT 123'}],
        }
    })

    messages = list(audit(area=area, student=Student.load(dict(areas=student['areas'], courses=student['courses']))))
    result = messages[-1].result

    assert result.result.items[-1].result.items[-1].result.assertions[0].expected == 18


def test_audit__single_studio_art():
    student: Dict[str, Any] = {
        'areas': [
            AreaPointer(
                code='140',
                status=AreaStatus.Declared,
                kind=AreaType.Major,
                name='Studio Art',
                degree='B.A.',
                dept='ART',
                gpa=None,
                terms_since_declaration=None,
            ),
        ],
        'courses': [
            course_from_str('DEPT 123'),
        ],
    }

    c = Constants(matriculation_year=2000)

    area = AreaOfStudy.load(c=c, student=Student.load(dict(areas=student['areas'], courses=student['courses'])), specification={
        'name': 'Art History Test',
        'type': 'major',
        'code': '140',
        'degree': 'B.A.',

        'result': {
            'all': [{'course': 'DEPT 123'}],
        }
    })

    messages = list(audit(area=area, student=Student.load(dict(areas=student['areas'], courses=student['courses']))))
    result = messages[-1].result

    assert result.result.items[-1].result.items[-1].result.assertions[0].expected == 21


def test_audit__single_art_history():
    student: Dict[str, Any] = {
        'areas': [
            AreaPointer(
                code='135',
                status=AreaStatus.Declared,
                kind=AreaType.Major,
                name='Art History',
                degree='B.A.',
                dept='ART',
                gpa=None,
                terms_since_declaration=None,
            ),
        ],
        'courses': [
            course_from_str('DEPT 123'),
        ],
    }

    c = Constants(matriculation_year=2000)

    area = AreaOfStudy.load(c=c, student=Student.load(dict(areas=student['areas'], courses=student['courses'])), specification={
        'name': 'Art History Test',
        'type': 'major',
        'code': '135',
        'degree': 'B.A.',

        'result': {
            'all': [{'course': 'DEPT 123'}],
        }
    })

    messages = list(audit(area=area, student=Student.load(dict(areas=student['areas'], courses=student['courses']))))
    result = messages[-1].result

    assert result.result.items[-1].result.items[-1].result.assertions[0].expected == 21


def test_audit__double_art_history_and_other():
    student: Dict[str, Any] = {
        'areas': [
            AreaPointer(
                code='135',
                status=AreaStatus.Declared,
                kind=AreaType.Major,
                name='Art History',
                degree='B.A.',
                dept='ART',
                gpa=None,
                terms_since_declaration=None,
            ),
            AreaPointer(
                code='001',
                status=AreaStatus.Declared,
                kind=AreaType.Major,
                name='Other',
                degree='B.A.',
                dept='DEPT',
                gpa=None,
                terms_since_declaration=None,
            ),
        ],
        'courses': [
            course_from_str('DEPT 123'),
        ],
    }

    c = Constants(matriculation_year=2000)

    area = AreaOfStudy.load(c=c, student=Student.load(dict(areas=student['areas'], courses=student['courses'])), specification={
        'name': 'Art History',
        'type': 'major',
        'code': '135',
        'degree': 'B.A.',

        'result': {
            'all': [{'course': 'DEPT 123'}],
        }
    })

    messages = list(audit(area=area, student=Student.load(dict(areas=student['areas'], courses=student['courses']))))
    result = messages[-1].result

    assert result.result.items[-1].result.items[-1].result.assertions[0].expected == 21


def test_audit__triple_arts_and_other():
    student: Dict[str, Any] = {
        'areas': [
            AreaPointer(
                code='135',
                status=AreaStatus.Declared,
                kind=AreaType.Major,
                name='Art History',
                degree='B.A.',
                dept='ART',
                gpa=None,
                terms_since_declaration=None,
            ),
            AreaPointer(
                code='140',
                status=AreaStatus.Declared,
                kind=AreaType.Major,
                name='Studio Art',
                degree='B.A.',
                dept='ART',
                gpa=None,
                terms_since_declaration=None,
            ),
            AreaPointer(
                code='001',
                status=AreaStatus.Declared,
                kind=AreaType.Major,
                name='Other',
                degree='B.A.',
                dept='DEPT',
                gpa=None,
                terms_since_declaration=None,
            ),
        ],
        'courses': [
            course_from_str('DEPT 123'),
        ],
    }

    c = Constants(matriculation_year=2000)

    area = AreaOfStudy.load(c=c, student=Student.load(dict(areas=student['areas'], courses=student['courses'])), specification={
        'name': 'Art History Test',
        'type': 'major',
        'code': '001',
        'degree': 'B.A.',

        'result': {
            'all': [{'course': 'DEPT 123'}],
        }
    })

    messages = list(audit(area=area, student=Student.load(dict(areas=student['areas'], courses=student['courses']))))
    result = messages[-1].result

    assert result.result.items[-1].result.items[-1].result.assertions[0].expected == 21

    area = AreaOfStudy.load(c=c, student=Student.load(dict(areas=student['areas'], courses=student['courses'])), specification={
        'name': 'Art History',
        'type': 'major',
        'code': '135',
        'degree': 'B.A.',

        'result': {
            'all': [{'course': 'DEPT 123'}],
        }
    })

    messages = list(audit(area=area, student=Student.load(dict(areas=student['areas'], courses=student['courses']))))
    result = messages[-1].result

    assert result.result.items[-1].result.items[-1].result.assertions[0].expected == 18

    area = AreaOfStudy.load(c=c, student=Student.load(dict(areas=student['areas'], courses=student['courses'])), specification={
        'name': 'Studio Art',
        'type': 'major',
        'code': '140',
        'degree': 'B.A.',

        'result': {
            'all': [{'course': 'DEPT 123'}],
        }
    })

    messages = list(audit(area=area, student=Student.load(dict(areas=student['areas'], courses=student['courses']))))
    result = messages[-1].result

    assert result.result.items[-1].result.items[-1].result.assertions[0].expected == 18
