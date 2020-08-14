from dp.conditional_expression import PredicateExpressionFunction
from dp.conditional_expression import PredicateExpression, PredicateExpressionNot
from dp.conditional_expression import PredicateExpressionCompoundAnd, PredicateExpressionCompoundOr
from dp.conditional_expression import load_predicate_expression, evaluate_predicate_function
from dp.context import RequirementContext
from dp.data.music import MusicProficiencies
from dp.data.area_pointer import AreaPointer
from dp.data.course import course_from_str
import pytest


def test_pred_expr_has_area_code():
    ctx = RequirementContext(areas=(AreaPointer.with_code('711'),))
    assert load_predicate_expression({'has-declared-area-code': '711'}, ctx=ctx).result is True
    assert load_predicate_expression({'has-declared-area-code': '000'}, ctx=ctx).result is False


def test_pred_expr_passed_proficiency_exam():
    ctx = RequirementContext(music_proficiencies=MusicProficiencies(keyboard_3=True))
    assert load_predicate_expression({'passed-proficiency-exam': 'Keyboard Level III'}, ctx=ctx).result is True


def test_pred_expr_has_course():
    ctx = RequirementContext().with_transcript([course_from_str('AMCON 101')])
    assert load_predicate_expression({'has-course': 'AMCON 101'}, ctx=ctx).result is True


def test_pred_expr_has_completed_course():
    ctx = RequirementContext().with_transcript([
        course_from_str('AMCON 101', in_progress=True),
        course_from_str('AMCON 102', in_progress=False),
    ])
    assert load_predicate_expression({'has-completed-course': 'AMCON 101'}, ctx=ctx).result is False
    assert load_predicate_expression({'has-completed-course': 'AMCON 102'}, ctx=ctx).result is True


def test_pred_expr_has_ip_course():
    ctx = RequirementContext().with_transcript([
        course_from_str('AMCON 101', in_progress=True),
        course_from_str('AMCON 102', in_progress=False),
    ])
    assert load_predicate_expression({'has-ip-course': 'AMCON 101'}, ctx=ctx).result is True
    assert load_predicate_expression({'has-ip-course': 'AMCON 102'}, ctx=ctx).result is False


def test_pred_and_expr():
    ctx = RequirementContext(
        areas=(AreaPointer.with_code('711'),),
        music_proficiencies=MusicProficiencies(keyboard_3=True, keyboard_4=False),
    )

    both_true = {
        '$and': [
            {'has-declared-area-code': '711'},
            {'passed-proficiency-exam': 'Keyboard Level III'},
        ]
    }
    actual = load_predicate_expression(both_true, ctx=ctx)
    assert actual.result is True
    assert isinstance(actual, PredicateExpressionCompoundAnd)

    area_but_not_exam = {
        '$and': [
            {'has-declared-area-code': '711'},
            {'passed-proficiency-exam': 'Keyboard Level IV'},
        ]
    }
    assert load_predicate_expression(area_but_not_exam, ctx=ctx).result is False


def test_pred_or_expr():
    ctx = RequirementContext(
        areas=(AreaPointer.with_code('711'),),
        music_proficiencies=MusicProficiencies(keyboard_3=True, keyboard_4=False),
    )

    both_true = {
        '$or': [
            {'has-declared-area-code': '711'},
            {'passed-proficiency-exam': 'Keyboard Level III'},
        ]
    }
    assert load_predicate_expression(both_true, ctx=ctx).result is True

    exam_but_not_area = {
        '$or': [
            {'has-declared-area-code': '000'},
            {'passed-proficiency-exam': 'Keyboard Level III'},
        ]
    }
    assert load_predicate_expression(exam_but_not_area, ctx=ctx).result is True

    area_but_not_exam = {
        '$or': [
            {'has-declared-area-code': '711'},
            {'passed-proficiency-exam': 'Keyboard Level IV'},
        ]
    }
    assert load_predicate_expression(area_but_not_exam, ctx=ctx).result is True

    both_false = {
        '$or': [
            {'has-declared-area-code': '000'},
            {'passed-proficiency-exam': 'Keyboard Level IV'},
        ]
    }
    assert load_predicate_expression(both_false, ctx=ctx).result is False


def test_load_predicate_expression():
    ctx = RequirementContext(areas=(AreaPointer.with_code('711'),))

    with pytest.raises(TypeError, match=r"unknown predicate expression \{'unknown-key': '711'\}"):
        assert load_predicate_expression({'unknown-key': '711'}, ctx=ctx)
