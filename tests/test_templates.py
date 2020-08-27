from dp.data.student import parse_template_course_rule, parse_identified_course, parse_named_course, TemplateCourse


def test_parse_identifier_course():
    assert parse_template_course_rule('AMCON 101', transcript=[]) == TemplateCourse(subject='AMCON', num='101')


def test_parse_named_course__simple():
    assert parse_template_course_rule('name=Level III Seminar', transcript=[]) == TemplateCourse(name='Level III Seminar')
    assert parse_template_course_rule('name=Level III Seminar #2', transcript=[]) == TemplateCourse(name='Level III Seminar #2')


def test_parse_named_course__institution():
    assert parse_template_course_rule('name=Level III Seminar [STOLAF]', transcript=[]) == TemplateCourse(name='Level III Seminar', institution='STOLAF')
    assert parse_template_course_rule('name=Level III Seminar #2 [STOLAF]', transcript=[]) == TemplateCourse(name='Level III Seminar #2', institution='STOLAF')
