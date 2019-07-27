from degreepath.area import AreaOfStudy
from degreepath.clause import SingleClause, AndClause, Operator, load_clause, apply_operator
from degreepath.operator import Operator, apply_operator
from degreepath.context import RequirementContext
from degreepath.data import CourseInstance
from degreepath.constants import Constants
from degreepath.rule.course import CourseRule
import yaml
import pytest
import io
import logging

c = Constants(matriculation_year=2000)

next_assertion = '\n\n... next assertion ...\n\n'


def test_load_mc(caplog):
    caplog.set_level(logging.DEBUG, logger='degreepath.context')

    transcript = tuple([
        CourseInstance.from_s("XYZ 101", attributes=['elective', 'alternate']),
    ])

    test_data = io.StringIO("""
        result:
            from: {student: courses}
            where: {attributes: {$eq: 'elective'}}
            assert: {count(courses): {$gte: 1}}

        attributes:
            multicountable:
                - - {attributes: {$eq: elective}}
                  - {attributes: {$eq: alternate}}
    """)

    area = AreaOfStudy.load(specification=yaml.load(stream=test_data, Loader=yaml.SafeLoader), c=c)

    multicountable = area.multicountable

    expected = [
        [
            SingleClause(key='attributes', expected='elective', expected_verbatim='elective', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='alternate', expected_verbatim='alternate', operator=Operator.EqualTo),
        ]
    ]

    assert multicountable == expected


@pytest.mark.x
def test_mc(caplog):
    caplog.set_level(logging.DEBUG, logger='degreepath.context')

    course = CourseInstance.from_s("XYZ 101", attributes=['elective', 'alternate'])
    transcript = tuple([course])
    ctx = RequirementContext(transcript=transcript, areas=tuple(), multicountable=[
        [
            SingleClause(key='attributes', expected='elective', expected_verbatim='elective', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='alternate', expected_verbatim='alternate', operator=Operator.EqualTo),
        ],
    ])

    by_elective = SingleClause(key='attributes', expected=('elective',), expected_verbatim=('elective',), operator=Operator.In)
    by_alternate = SingleClause(key='attributes', expected=('alternate',), expected_verbatim=('alternate',), operator=Operator.In)

    claim_a = ctx.make_claim(course=course, path=[], clause=by_elective, allow_claimed=False)
    assert claim_a.failed() == False

    logging.info(next_assertion)

    claim_b = ctx.make_claim(course=course, path=[], clause=by_alternate, allow_claimed=False)
    assert claim_b.failed() == False

    logging.info(next_assertion)

    claim_c = ctx.make_claim(course=course, path=[], clause=by_elective, allow_claimed=False)
    assert claim_c.failed() == True

    logging.info(next_assertion)

    claim_d = ctx.make_claim(course=course, path=[], clause=by_alternate, allow_claimed=False)
    assert claim_d.failed() == True


def test_mc_course_attrs(caplog):
    caplog.set_level(logging.DEBUG, logger='degreepath.context')

    """
    multicountable:
      - - {course: {$eq: ECON 385}}
        - {attributes: {$eq: econ_level_3}}
    """

    course = CourseInstance.from_s("ECON 385", attributes=['econ_level_3'])
    transcript = tuple([course])
    ctx = RequirementContext(transcript=transcript, areas=tuple(), multicountable=[
        [
            SingleClause(key='course', expected='ECON 385', expected_verbatim='ECON 385', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='econ_level_3', expected_verbatim='econ_level_3', operator=Operator.EqualTo),
        ],
    ])

    by_course = SingleClause(key='course', expected='ECON 385', expected_verbatim='ECON 385', operator=Operator.EqualTo)
    by_attr = SingleClause(key='attributes', expected='econ_level_3', expected_verbatim='econ_level_3', operator=Operator.EqualTo)

    claim_a = ctx.make_claim(course=course, path=[], clause=by_course, allow_claimed=False)
    assert claim_a.failed() == False

    logging.info(next_assertion)

    claim_b = ctx.make_claim(course=course, path=[], clause=by_attr, allow_claimed=False)
    assert claim_b.failed() == False

    logging.info(next_assertion)

    claim_c = ctx.make_claim(course=course, path=[], clause=by_course, allow_claimed=False)
    assert claim_c.failed() == True

    logging.info(next_assertion)

    claim_d = ctx.make_claim(course=course, path=[], clause=by_attr, allow_claimed=False)
    assert claim_c.failed() == True


def test_mc_multiple_attr_sets(caplog):
    caplog.set_level(logging.DEBUG, logger='degreepath.context')

    """
    multicountable:
      - - {attributes: {$eq: engl_elective}}
        - {attributes: {$eq: engl_period_post1800}}
        - {attributes: {$eq: engl_period_pre1800}}

      - - {attributes: {$eq: engl_topic_crosscultural}}
        - {attributes: {$eq: engl_period_post1800}}
        - {attributes: {$eq: engl_period_pre1800}}

      - - {attributes: {$eq: engl_topic_crossdisciplinary}}
        - {attributes: {$eq: engl_period_post1800}}
        - {attributes: {$eq: engl_period_pre1800}}

      - - {attributes: {$eq: engl_topic_genre}}
        - {attributes: {$eq: engl_period_post1800}}
        - {attributes: {$eq: engl_period_pre1800}}

      - - {attributes: {$eq: engl_topic_literary_history}}
        - {attributes: {$eq: engl_period_post1800}}
        - {attributes: {$eq: engl_period_pre1800}}
    """

    course = CourseInstance.from_s("ENGL 205", attributes=['engl_elective', 'engl_period_post1800', 'engl_period_pre1800', 'engl_topic_crosscultural'])
    transcript = tuple([course])
    ctx = RequirementContext(transcript=transcript, areas=tuple(), multicountable=[
        [
            SingleClause(key='attributes', expected='engl_elective', expected_verbatim='engl_elective', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='engl_period_post1800', expected_verbatim='engl_period_post1800', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='engl_period_pre1800', expected_verbatim='engl_period_pre1800', operator=Operator.EqualTo),
        ],
        [
            SingleClause(key='attributes', expected='engl_topic_crosscultural', expected_verbatim='engl_topic_crosscultural', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='engl_period_post1800', expected_verbatim='engl_period_post1800', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='engl_period_pre1800', expected_verbatim='engl_period_pre1800', operator=Operator.EqualTo),
        ],
        [
            SingleClause(key='attributes', expected='engl_topic_crossdisciplinary', expected_verbatim='engl_topic_crossdisciplinary', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='engl_period_post1800', expected_verbatim='engl_period_post1800', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='engl_period_pre1800', expected_verbatim='engl_period_pre1800', operator=Operator.EqualTo),
        ],
        [
            SingleClause(key='attributes', expected='engl_topic_genre', expected_verbatim='engl_topic_genre', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='engl_period_post1800', expected_verbatim='engl_period_post1800', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='engl_period_pre1800', expected_verbatim='engl_period_pre1800', operator=Operator.EqualTo),
        ],
        [
            SingleClause(key='attributes', expected='engl_topic_literary_history', expected_verbatim='engl_topic_literary_history', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='engl_period_post1800', expected_verbatim='engl_period_post1800', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='engl_period_pre1800', expected_verbatim='engl_period_pre1800', operator=Operator.EqualTo),
        ],
    ])

    by_elective = SingleClause(key='attributes', expected='engl_elective', expected_verbatim='engl_elective', operator=Operator.EqualTo)
    by_post1800 = SingleClause(key='attributes', expected='engl_period_post1800', expected_verbatim='engl_period_post1800', operator=Operator.EqualTo)
    by_pre1800 = SingleClause(key='attributes', expected='engl_period_pre1800', expected_verbatim='engl_period_pre1800', operator=Operator.EqualTo)
    by_xcultural = SingleClause(key='attributes', expected='engl_topic_crosscultural', expected_verbatim='engl_topic_crosscultural', operator=Operator.EqualTo)

    # We expect the three claims in the first ruleset to succeed, and any future claims against those keys – or any others – to fail.

    logger = logging.getLogger('degreepath.context')

    claim_a = ctx.make_claim(course=course, path=['a'], clause=by_elective, allow_claimed=False)
    assert claim_a.failed() == False, 'Should pass because no claim exists on this course yet'

    logger.info(next_assertion)

    claim_b = ctx.make_claim(course=course, path=['c'], clause=by_xcultural, allow_claimed=False)
    assert claim_b.failed() == True, 'Should fail due to no clauseset having both [elective] and [xcultural]'

    logger.info(next_assertion)

    claim_c = ctx.make_claim(course=course, path=['a'], clause=by_post1800, allow_claimed=False)
    assert claim_c.failed() == False, 'Should pass because there is a [elective, post1800, pre1800] set'

    logger.info(next_assertion)

    claim_d = ctx.make_claim(course=course, path=['a'], clause=by_pre1800, allow_claimed=False)
    assert claim_d.failed() == False, 'Should pass because there is a [elective, post1800, pre1800] set'

    logger.info(next_assertion)

    claim_e = ctx.make_claim(course=course, path=['b'], clause=by_elective, allow_claimed=False)
    assert claim_e.failed() == False, "Should fail because we've already claimed this course"

    logger.info(next_assertion)

    claim_f = ctx.make_claim(course=course, path=['b'], clause=by_elective, allow_claimed=True)
    assert claim_f.failed() == False, "Should pass because we said already_claimed was OK"


"""
multicountable:
  - - {attributes: {$eq: history_era_premodern}}
    - {attributes: {$eq: history_l2_seminar}}
    - {attributes: {$eq: history_level_3}}
    - {attributes: {$eq: history_region_europe}}
    - {attributes: {$eq: history_region_nonwesternworld}}
    - {attributes: {$eq: history_region_us}}
"""


"""
multicountable:
  - - {attributes: {$eq: math_perspective_a}}
    - {attributes: {$eq: math_level_3}}
    - {attributes: {$eq: math_transitions}}

  - - {attributes: {$eq: math_perspective_c}}
    - {attributes: {$eq: math_level_3}}
    - {attributes: {$eq: math_transitions}}

  - - {attributes: {$eq: math_perspective_d}}
    - {attributes: {$eq: math_level_3}}
    - {attributes: {$eq: math_transitions}}

  - - {attributes: {$eq: math_perspective_m}}
    - {attributes: {$eq: math_level_3}}
    - {attributes: {$eq: math_transitions}}
"""


"""
multicountable:
  - - {course: {$eq: SPAN 313}}
    - {attribute: {$eq: spanish_elective}}
  - - {course: {$eq: SPAN 313}}
    - {attribute: {$eq: spanish_focus_spain}}

  - - {course: {$eq: SPAN 314}}
    - {attribute: {$eq: spanish_elective}}
  - - {course: {$eq: SPAN 314}}
    - {attribute: {$eq: spanish_focus_latinamerica}}
"""


"""
multicountable:
  - - {attribute: {$eq: wmgst_theory}}
    - {attribute: {$eq: wmgst_elective}}

  - - {attribute: {$eq: wmgst_diverse}}
    - {attribute: {$eq: wmgst_elective}}

  - - {attribute: {$eq: wmgst_historical}}
    - {attribute: {$eq: wmgst_elective}}

  - - {course: {$eq: WMGST 121}}
    - {attribute: {$eq: wmgst_lived}}
"""
