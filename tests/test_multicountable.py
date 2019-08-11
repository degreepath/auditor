from degreepath.area import AreaOfStudy
from degreepath.clause import SingleClause
from degreepath.operator import Operator
from degreepath.context import RequirementContext
from degreepath.data import course_from_str
from degreepath.constants import Constants
from degreepath.rule.course import CourseRule
import yaml
import io
import logging

c = Constants(matriculation_year=2000)

next_assertion = '\n\n... next assertion ...\n\n'


def test_load_mc(caplog):
    caplog.set_level(logging.DEBUG, logger='degreepath.context')

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


def test_mc(caplog):
    caplog.set_level(logging.DEBUG, logger='degreepath.context')

    course = course_from_str("XYZ 101", attributes=['elective', 'alternate'])
    multicountable = [
        [
            SingleClause(key='attributes', expected='elective', expected_verbatim='elective', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='alternate', expected_verbatim='alternate', operator=Operator.EqualTo),
        ],
    ]
    ctx = RequirementContext(areas=tuple(), multicountable=multicountable).with_transcript(tuple([course]))

    by_elective = SingleClause(key='attributes', expected=('elective',), expected_verbatim=('elective',), operator=Operator.In)
    by_alternate = SingleClause(key='attributes', expected=('alternate',), expected_verbatim=('alternate',), operator=Operator.In)

    claim_a = ctx.make_claim(course=course, path=[], clause=by_elective, allow_claimed=False)
    assert claim_a.failed() is False

    logging.info(next_assertion)

    claim_b = ctx.make_claim(course=course, path=[], clause=by_alternate, allow_claimed=False)
    assert claim_b.failed() is False

    logging.info(next_assertion)

    claim_c = ctx.make_claim(course=course, path=[], clause=by_elective, allow_claimed=False)
    assert claim_c.failed() is True

    logging.info(next_assertion)

    claim_d = ctx.make_claim(course=course, path=[], clause=by_alternate, allow_claimed=False)
    assert claim_d.failed() is True


def test_mc_course_attrs(caplog):
    caplog.set_level(logging.DEBUG, logger='degreepath.context')

    """
    multicountable:
      - - {course: {$eq: ECON 385}}
        - {attributes: {$eq: econ_level_3}}
    """

    course = course_from_str("ECON 385", attributes=['econ_level_3'])
    multicountable = [
        [
            SingleClause(key='course', expected='ECON 385', expected_verbatim='ECON 385', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='econ_level_3', expected_verbatim='econ_level_3', operator=Operator.EqualTo),
        ],
    ]
    ctx = RequirementContext(areas=tuple(), multicountable=multicountable).with_transcript(tuple([course]))

    by_course = SingleClause(key='course', expected='ECON 385', expected_verbatim='ECON 385', operator=Operator.EqualTo)
    by_attr = SingleClause(key='attributes', expected='econ_level_3', expected_verbatim='econ_level_3', operator=Operator.EqualTo)

    claim_a = ctx.make_claim(course=course, path=[], clause=by_course, allow_claimed=False)
    assert claim_a.failed() is False

    logging.info(next_assertion)

    claim_b = ctx.make_claim(course=course, path=[], clause=by_attr, allow_claimed=False)
    assert claim_b.failed() is False

    logging.info(next_assertion)

    claim_c = ctx.make_claim(course=course, path=[], clause=by_course, allow_claimed=False)
    assert claim_c.failed() is True

    logging.info(next_assertion)

    claim_d = ctx.make_claim(course=course, path=[], clause=by_attr, allow_claimed=False)
    assert claim_d.failed() is True


def test_mc_course_attrs_courserule(caplog):
    caplog.set_level(logging.DEBUG, logger='degreepath.context')

    """
    multicountable:
      - - {course: {$eq: ECON 385}}
        - {attributes: {$eq: econ_level_3}}
    """

    course = course_from_str("ECON 385", attributes=['econ_level_3'])
    multicountable = [
        [
            SingleClause(key='course', expected='ECON 385', expected_verbatim='ECON 385', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='econ_level_3', expected_verbatim='econ_level_3', operator=Operator.EqualTo),
        ],
    ]
    ctx = RequirementContext(areas=tuple(), multicountable=multicountable).with_transcript(tuple([course]))

    by_course_rule = CourseRule(course='ECON 385', hidden=False, grade=None, allow_claimed=False, path=tuple())
    by_course_clause = CourseRule(course='ECON 385', hidden=False, grade=None, allow_claimed=False, path=tuple())
    by_attr = SingleClause(key='attributes', expected='econ_level_3', expected_verbatim='econ_level_3', operator=Operator.EqualTo)

    claim_a = ctx.make_claim(course=course, path=[], clause=by_course_rule, allow_claimed=False)
    assert claim_a.failed() is False

    logging.info(next_assertion)

    claim_b = ctx.make_claim(course=course, path=[], clause=by_attr, allow_claimed=False)
    assert claim_b.failed() is False

    logging.info(next_assertion)

    claim_c = ctx.make_claim(course=course, path=[], clause=by_course_rule, allow_claimed=False)
    assert claim_c.failed() is True

    logging.info(next_assertion)

    claim_c2 = ctx.make_claim(course=course, path=[], clause=by_course_clause, allow_claimed=False)
    assert claim_c2.failed() is True

    logging.info(next_assertion)

    claim_d = ctx.make_claim(course=course, path=[], clause=by_attr, allow_claimed=False)
    assert claim_d.failed() is True


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

    course = course_from_str("ENGL 205", attributes=['engl_elective', 'engl_period_post1800', 'engl_period_pre1800', 'engl_topic_crosscultural'])
    multicountable = [
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
    ]
    ctx = RequirementContext(areas=tuple(), multicountable=multicountable).with_transcript(tuple([course]))

    by_elective = SingleClause(key='attributes', expected='engl_elective', expected_verbatim='engl_elective', operator=Operator.EqualTo)
    by_post1800 = SingleClause(key='attributes', expected='engl_period_post1800', expected_verbatim='engl_period_post1800', operator=Operator.EqualTo)
    by_pre1800 = SingleClause(key='attributes', expected='engl_period_pre1800', expected_verbatim='engl_period_pre1800', operator=Operator.EqualTo)
    by_xcultural = SingleClause(key='attributes', expected='engl_topic_crosscultural', expected_verbatim='engl_topic_crosscultural', operator=Operator.EqualTo)

    # We expect the three claims in the first ruleset to succeed, and any future claims against those keys – or any others – to fail.

    logger = logging.getLogger('degreepath.context')

    claim_a = ctx.make_claim(course=course, path=['a'], clause=by_elective, allow_claimed=False)
    assert claim_a.failed() is False, 'Should pass because no claim exists on this course yet'

    logger.info(next_assertion)

    claim_b = ctx.make_claim(course=course, path=['c'], clause=by_xcultural, allow_claimed=False)
    assert claim_b.failed() is True, 'Should fail due to no clauseset having both [elective] and [xcultural]'

    logger.info(next_assertion)

    claim_c = ctx.make_claim(course=course, path=['a'], clause=by_post1800, allow_claimed=False)
    assert claim_c.failed() is False, 'Should pass because there is a [elective, post1800, pre1800] set'

    logger.info(next_assertion)

    claim_d = ctx.make_claim(course=course, path=['a'], clause=by_pre1800, allow_claimed=False)
    assert claim_d.failed() is False, 'Should pass because there is a [elective, post1800, pre1800] set'

    logger.info(next_assertion)

    claim_e = ctx.make_claim(course=course, path=['b'], clause=by_elective, allow_claimed=False)
    assert claim_e.failed() is True, "Should fail because we've already claimed this course"

    logger.info(next_assertion)

    claim_f = ctx.make_claim(course=course, path=['b'], clause=by_elective, allow_claimed=True)
    assert claim_f.failed() is False, "Should pass because we said already_claimed was OK"


def test_mc_massive_attr_set(caplog):
    caplog.set_level(logging.DEBUG, logger='degreepath.context')

    """
    multicountable:
      - - {attributes: {$eq: history_era_premodern}}
        - {attributes: {$eq: history_l2_seminar}}
        - {attributes: {$eq: history_level_3}}
        - {attributes: {$eq: history_region_europe}}
        - {attributes: {$eq: history_region_nonwesternworld}}
        - {attributes: {$eq: history_region_us}}
    """

    course = course_from_str("HIST 204", attributes=['history_era_premodern'])
    multicountable = [
        [
            SingleClause(key='attributes', expected='history_era_premodern', expected_verbatim='history_era_premodern', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='history_l2_seminar', expected_verbatim='history_l2_seminar', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='history_level_3', expected_verbatim='history_level_3', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='history_region_europe', expected_verbatim='history_region_europe', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='history_region_nonwesternworld', expected_verbatim='history_region_nonwesternworld', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='history_region_us', expected_verbatim='history_region_us', operator=Operator.EqualTo),
        ],
    ]
    ctx = RequirementContext(areas=tuple(), multicountable=multicountable).with_transcript(tuple([course]))

    by_premodern = SingleClause(key='attributes', expected='history_era_premodern', expected_verbatim='history_era_premodern', operator=Operator.EqualTo)
    by_l2_seminar = SingleClause(key='attributes', expected='history_l2_seminar', expected_verbatim='history_l2_seminar', operator=Operator.EqualTo)
    by_l3 = SingleClause(key='attributes', expected='history_level_3', expected_verbatim='history_level_3', operator=Operator.EqualTo)
    by_europe = SingleClause(key='attributes', expected='history_region_europe', expected_verbatim='history_region_europe', operator=Operator.EqualTo)
    by_world = SingleClause(key='attributes', expected='history_region_nonwesternworld', expected_verbatim='history_region_nonwesternworld', operator=Operator.EqualTo)
    by_usa = SingleClause(key='attributes', expected='history_region_us', expected_verbatim='history_region_us', operator=Operator.EqualTo)

    # We expect to be able to make one claim for each of the six attribute values, once each

    logger = logging.getLogger('degreepath.context')

    claim_a = ctx.make_claim(course=course, path=['a'], clause=by_premodern, allow_claimed=False)
    assert claim_a.failed() is False, 'Should pass because no claim exists on this course yet'

    logger.info(next_assertion)

    claim_b = ctx.make_claim(course=course, path=['b'], clause=by_l2_seminar, allow_claimed=False)
    assert claim_b.failed() is False, 'Should pass due to the allowance of six values'

    logger.info(next_assertion)

    claim_c = ctx.make_claim(course=course, path=['c'], clause=by_l3, allow_claimed=False)
    assert claim_c.failed() is False, 'Should pass due to the allowance of six values'

    logger.info(next_assertion)

    claim_d = ctx.make_claim(course=course, path=['d'], clause=by_europe, allow_claimed=False)
    assert claim_d.failed() is False, 'Should pass due to the allowance of six values'

    logger.info(next_assertion)

    claim_e = ctx.make_claim(course=course, path=['e'], clause=by_world, allow_claimed=False)
    assert claim_e.failed() is False, 'Should pass due to the allowance of six values'

    logger.info(next_assertion)

    claim_f = ctx.make_claim(course=course, path=['f'], clause=by_usa, allow_claimed=False)
    assert claim_f.failed() is False, 'Should pass due to the allowance of six values'

    logger.info(next_assertion)

    # Now, we expect all of _these_ to fail, because the first six have already claimed them

    claim_g = ctx.make_claim(course=course, path=['g'], clause=by_premodern, allow_claimed=False)
    assert claim_g.failed() is True, 'Should fail because we have already claimed by this value'

    logger.info(next_assertion)

    claim_h = ctx.make_claim(course=course, path=['h'], clause=by_l2_seminar, allow_claimed=False)
    assert claim_h.failed() is True, 'Should fail because we have already claimed by this value'

    logger.info(next_assertion)

    claim_i = ctx.make_claim(course=course, path=['i'], clause=by_l3, allow_claimed=False)
    assert claim_i.failed() is True, 'Should fail because we have already claimed by this value'

    logger.info(next_assertion)

    claim_j = ctx.make_claim(course=course, path=['j'], clause=by_europe, allow_claimed=False)
    assert claim_j.failed() is True, 'Should fail because we have already claimed by this value'

    logger.info(next_assertion)

    claim_k = ctx.make_claim(course=course, path=['k'], clause=by_world, allow_claimed=False)
    assert claim_k.failed() is True, 'Should fail because we have already claimed by this value'

    logger.info(next_assertion)

    claim_l = ctx.make_claim(course=course, path=['l'], clause=by_usa, allow_claimed=False)
    assert claim_l.failed() is True, 'Should fail because we have already claimed by this value'


def test_mc_math_sets(caplog):
    caplog.set_level(logging.DEBUG, logger='degreepath.context')

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

    course = course_from_str("MATH 399", attributes=['math_perspective_a', 'math_perspective_c', 'math_level_3'])
    multicountable = [
        [
            SingleClause(key='attributes', expected='math_perspective_a', expected_verbatim='math_perspective_a', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='math_level_3', expected_verbatim='math_level_3', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='math_transitions', expected_verbatim='math_transitions', operator=Operator.EqualTo),
        ],
        [
            SingleClause(key='attributes', expected='math_perspective_c', expected_verbatim='math_perspective_c', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='math_level_3', expected_verbatim='math_level_3', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='math_transitions', expected_verbatim='math_transitions', operator=Operator.EqualTo),
        ],
        [
            SingleClause(key='attributes', expected='math_perspective_d', expected_verbatim='math_perspective_d', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='math_level_3', expected_verbatim='math_level_3', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='math_transitions', expected_verbatim='math_transitions', operator=Operator.EqualTo),
        ],
        [
            SingleClause(key='attributes', expected='math_perspective_m', expected_verbatim='math_perspective_m', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='math_level_3', expected_verbatim='math_level_3', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='math_transitions', expected_verbatim='math_transitions', operator=Operator.EqualTo),
        ],
    ]
    ctx = RequirementContext(areas=tuple(), multicountable=multicountable).with_transcript(tuple([course]))

    by_a = SingleClause(key='attributes', expected='math_perspective_a', expected_verbatim='math_perspective_a', operator=Operator.EqualTo)
    by_l3 = SingleClause(key='attributes', expected='math_level_3', expected_verbatim='math_level_3', operator=Operator.EqualTo)
    by_c = SingleClause(key='attributes', expected='math_perspective_c', expected_verbatim='math_perspective_c', operator=Operator.EqualTo)

    # We expect 'math_perspective_a' and 'math_level_3' to succeed, but
    # 'math_perspective_c' to fail because it's mutually exclusive with
    # 'math_perspective_a'

    logger = logging.getLogger('degreepath.context')

    claim_a = ctx.make_claim(course=course, path=['a'], clause=by_a, allow_claimed=False)
    assert claim_a.failed() is False, 'Should pass because no claim exists on this course yet'

    logger.info(next_assertion)

    claim_b = ctx.make_claim(course=course, path=['a'], clause=by_l3, allow_claimed=False)
    assert claim_b.failed() is False, 'Should pass because there is an [a, level3] set'

    logger.info(next_assertion)

    claim_c = ctx.make_claim(course=course, path=['a'], clause=by_c, allow_claimed=False)
    assert claim_c.failed() is True, 'Should fail because there is no [persp_a, persp_c] set'


def test_mc_spanish_sets(caplog):
    caplog.set_level(logging.DEBUG, logger='degreepath.context')

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

    course = course_from_str("SPAN 313", attributes=['spanish_elective', 'spanish_focus_spain'])
    multicountable = [
        [
            SingleClause(key='course', expected='SPAN 313', expected_verbatim='SPAN 313', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='spanish_elective', expected_verbatim='spanish_elective', operator=Operator.EqualTo),
        ],
        [
            SingleClause(key='course', expected='SPAN 313', expected_verbatim='SPAN 313', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='spanish_focus_spain', expected_verbatim='spanish_focus_spain', operator=Operator.EqualTo),
        ],
    ]
    ctx = RequirementContext(areas=tuple(), multicountable=multicountable).with_transcript(tuple([course]))

    by_course = CourseRule(course='SPAN 313', hidden=False, grade=None, allow_claimed=False, path=tuple())
    by_elective = SingleClause(key='attributes', expected='spanish_elective', expected_verbatim='spanish_elective', operator=Operator.EqualTo)
    by_focus = SingleClause(key='attributes', expected='spanish_focus_spain', expected_verbatim='spanish_focus_spain', operator=Operator.EqualTo)

    # We expect SPAN 313 + spanish_elective to work, but then adding _focus_spain should fail

    logger = logging.getLogger('degreepath.context')

    claim_a = ctx.make_claim(course=course, path=['a'], clause=by_course, allow_claimed=False)
    assert claim_a.failed() is False, 'Should pass because no claim exists on this course yet'

    logger.info(next_assertion)

    claim_b = ctx.make_claim(course=course, path=['c'], clause=by_elective, allow_claimed=False)
    assert claim_b.failed() is False, 'Should pass because we allow the pairing'

    logger.info(next_assertion)

    claim_c = ctx.make_claim(course=course, path=['a'], clause=by_focus, allow_claimed=False)
    assert claim_c.failed() is True, 'Should fail because we have already locked in to 313+elective, not 313+focus'


def test_mc_dance_sets(caplog):
    caplog.set_level(logging.DEBUG, logger='degreepath.context')

    """
    multicountable:
      - - {attributes: {$eq: dance_movement}}
        - {attributes: {$eq: dance_genre_ballet}}

      - - {attributes: {$eq: dance_movement}}
        - {attributes: {$eq: dance_genre_international}}

      - - {attributes: {$eq: dance_movement}}
        - {attributes: {$eq: dance_genre_modern}}

      - - {attributes: {$eq: dance_movement}}
        - {attributes: {$eq: dance_genre_other}}
    """

    course = course_from_str("DANCE 313", attributes=['dance_movement', 'dance_genre_modern'])
    multicountable = [
        [
            SingleClause(key='attributes', expected='dance_movement', expected_verbatim='dance_movement', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='dance_genre_ballet', expected_verbatim='dance_genre_ballet', operator=Operator.EqualTo),
        ],
        [
            SingleClause(key='attributes', expected='dance_movement', expected_verbatim='dance_movement', operator=Operator.EqualTo),
            SingleClause(key='attributes', expected='dance_genre_modern', expected_verbatim='dance_genre_modern', operator=Operator.EqualTo),
        ],
    ]
    ctx = RequirementContext(areas=tuple(), multicountable=multicountable).with_transcript(tuple([course]))

    by_movement = SingleClause(key='attributes', expected='dance_movement', expected_verbatim='dance_movement', operator=Operator.EqualTo)
    by_modern = SingleClause(key='attributes', expected='dance_genre_modern', expected_verbatim='dance_genre_modern', operator=Operator.EqualTo)

    logger = logging.getLogger('degreepath.context')

    claim_a = ctx.make_claim(course=course, path=['a'], clause=by_movement, allow_claimed=False)
    assert claim_a.failed() is False, 'Should pass because no claim exists on this course yet'

    logger.info(next_assertion)

    claim_b = ctx.make_claim(course=course, path=['c'], clause=by_modern, allow_claimed=False)
    assert claim_b.failed() is False, 'Should pass because we allow the pairing'
