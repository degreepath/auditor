from typing import Dict, Sequence, Iterable, Iterator, List, Optional, TYPE_CHECKING
from .constants import Constants

from .base import Rule
from .rule.count import CountRule
from .rule.course import CourseRule
from .rule.query import QueryRule
from .rule.requirement import RequirementRule
from .rule.proficiency import ProficiencyRule
from .rule.conditional import ConditionalRule
from .data.student import TemplateCourse

if TYPE_CHECKING:  # pragma: no cover
    from .context import RequirementContext  # noqa: F401


def load_rule(
    *,
    data: Dict,
    c: Constants,
    path: List[str],
    children: Dict[str, Dict],
    emphases: Sequence[Dict[str, Dict]] = tuple(),
    ctx: 'RequirementContext',
) -> Optional[Rule]:
    # This only runs at the top level of an area, because we don't pass
    # emphases down below that. This is how we attach the requirements
    # for an emphasis into the main run.
    if emphases:
        assert CountRule.can_load(data)

    if ProficiencyRule.can_load(data):
        return ProficiencyRule.load(data, c=c, path=path)

    elif CourseRule.can_load(data):
        return CourseRule.load(data, c=c, path=path)

    elif QueryRule.can_load(data):
        return QueryRule.load(data, c=c, path=path, ctx=ctx)

    elif ConditionalRule.can_load(data):
        return ConditionalRule.load(data, c=c, path=path, ctx=ctx)

    elif CountRule.can_load(data):
        return CountRule.load(data, c=c, children=children, path=path, emphases=emphases, ctx=ctx)

    elif RequirementRule.can_load(data):
        if "name" in data:
            return RequirementRule.load(data, name=data["name"], c=c, path=path, ctx=ctx)
        else:
            req_name = data["requirement"]
            return RequirementRule.load(children[req_name], name=req_name, c=c, path=path, ctx=ctx)

    raise ValueError(f"expected Course, Query, Count, or Reference; found none of those (in {data}, {type(data)})")


def expand_template(items: Iterable[Dict], *, ctx: 'RequirementContext') -> Iterator[Dict]:
    for item in items:
        if 'template' in item:
            yield from expand_template_item(key=item['template'], ctx=ctx)
        else:
            yield item


def expand_template_item(*, key: str, ctx: 'RequirementContext') -> Iterator[Dict]:
    template_courses: Iterable[TemplateCourse] = ctx.templates.get(key, [])

    for template in template_courses:
        yield template.to_course_rule_as_dict()
