from typing import List, Iterator, Union, Dict, Optional
import os
import json

import attr
import urllib3  # type: ignore

from .constants import Constants
from .area import AreaOfStudy

from .base import Base, BaseRequirementRule, BaseCountRule
from .base.query import QuerySource
from .rule.query import QueryRule
from .clause import Clause, AndClause, OrClause, SingleClause
from .operator import Operator

http = urllib3.PoolManager()


def discover_clause_potential(
    area: AreaOfStudy,
    c: Constants,
    *,
    url: Optional[str] = os.getenv('POTENTIALS_URL', None),
) -> Dict[int, List[str]]:
    if not url:
        return {}

    result = {}
    for clause in find_all_clauses(area):
        positive_buckets = set(extract_positive_buckets(clause))
        negative_buckets = set(extract_negative_buckets(clause))

        dict_clause = clause.to_dict()

        data = {
            'positive_buckets': chr(30).join(sorted(positive_buckets)),
            'negative_buckets': chr(30).join(sorted(negative_buckets)),
            'clause': json.dumps(dict_clause),
            'matriculation': str(c.matriculation_year),
        }

        response = http.request('POST', url, fields=data, headers={'Accept': 'application/json'})
        parsed = json.loads(response.data.decode('utf-8'))

        if 'hash' in parsed and parsed['error'] is False:
            result[parsed['hash']] = parsed['clbids']
        else:
            raise ValueError(parsed)

    return result


def find_all_clauses(rule: Union[Base, Clause]) -> Iterator[Clause]:
    if isinstance(rule, (AreaOfStudy, BaseRequirementRule)):
        if rule.result:
            yield from find_all_clauses(rule.result)
    elif isinstance(rule, BaseCountRule):
        for child in rule.items:
            yield from find_all_clauses(child)
    elif isinstance(rule, QueryRule):
        if rule.source is QuerySource.Courses:
            if rule.where and rule.load_potentials:
                yield from find_all_clauses(rule.where)
    elif isinstance(rule, (AndClause, OrClause, SingleClause)):
        yield from strip_pointless_clauses(rule)


def strip_pointless_clauses(clause: Clause) -> Iterator[Clause]:
    if isinstance(clause, (AndClause, OrClause)):
        children = []
        for c in clause.children:
            for good_clause in strip_pointless_clauses(c):
                children.append(good_clause)
        yield attr.evolve(clause, children=tuple(children))

    elif isinstance(clause, SingleClause):
        if clause.key in ('credits', 'grade_option', 's/u', 'is_stolaf'):
            return

        yield clause


def extract_positive_buckets(clause: Clause) -> Iterator[str]:
    if isinstance(clause, (AndClause, OrClause)):
        for child in clause.children:
            yield from extract_positive_buckets(child)

    elif isinstance(clause, SingleClause):
        if clause.key == 'attributes':
            if clause.operator is Operator.EqualTo:
                yield clause.expected
            elif clause.operator is Operator.In:
                yield from clause.expected


def extract_negative_buckets(clause: Clause) -> Iterator[str]:
    if isinstance(clause, (AndClause, OrClause)):
        for child in clause.children:
            yield from extract_negative_buckets(child)

    elif isinstance(clause, SingleClause):
        if clause.key == 'attributes':
            if clause.operator is Operator.NotEqualTo:
                yield clause.expected
            elif clause.operator is Operator.NotIn:
                yield from clause.expected
