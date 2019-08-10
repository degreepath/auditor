from typing import Dict, Sequence, List
from .constants import Constants

from .base import Rule
from .rule.count import CountRule
from .rule.course import CourseRule
from .rule.query import QueryRule
from .rule.requirement import RequirementRule


def load_rule(
    *,
    data: Dict,
    c: Constants,
    path: List[str] = [],
    children: Dict[str, Dict] = {},
    emphases: Sequence[Dict[str, Dict]] = tuple(),
) -> Rule:
    # This only runs at the top level of an area, because we don't ass
    # emphases down below that. This is how we attach the requirements
    # for an emphasis into the main run.
    if emphases:
        assert CountRule.can_load(data)
        return CountRule.load(data, c=c, children=children, emphases=emphases, path=path)

    if CourseRule.can_load(data):
        return CourseRule.load(data, c=c, path=path)

    elif QueryRule.can_load(data):
        return QueryRule.load(data, c=c, path=path)

    elif CountRule.can_load(data):
        return CountRule.load(data, c=c, children=children, path=path)

    elif RequirementRule.can_load(data):
        reqname = data["requirement"]
        return RequirementRule.load(children[reqname], name=reqname, c=c, path=path)

    raise ValueError(f"expected Course, Query, Count, or Reference; found none of those (in {data}, {type(data)})")
