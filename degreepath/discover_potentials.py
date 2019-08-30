from typing import List, Iterator, Union, Dict
import requests
import os
import attr
import json

from .constants import Constants
from .area import AreaOfStudy

from .base import Base, BaseRequirementRule, BaseCountRule
from .base.query import QuerySourceType
from .rule.query import QueryRule
from .clause import ResolvedClause, AndClause, OrClause, SingleClause
from .operator import Operator


def discover_clause_potential(area: AreaOfStudy, c: Constants) -> Dict[int, List[str]]:
    url = os.getenv('POTENTIALS_URL', None)
    if not url:
        return {}

    result = {}
    s = requests.Session()
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

        response = s.post(url, data=data, headers={'accept': 'application/json'})
        parsed = response.json()

        if 'hash' in parsed and parsed['error'] is False:
            result[parsed['hash']] = parsed['clbids']
        else:
            raise ValueError(parsed)

    return result


def find_all_clauses(rule: Union[Base, ResolvedClause]) -> Iterator[ResolvedClause]:
    if isinstance(rule, (AreaOfStudy, BaseRequirementRule)):
        if rule.result:
            yield from find_all_clauses(rule.result)
    elif isinstance(rule, BaseCountRule):
        for child in rule.items:
            yield from find_all_clauses(child)
    elif isinstance(rule, QueryRule):
        if rule.source_type is QuerySourceType.Courses:
            if rule.where and rule.load_potentials:
                yield from find_all_clauses(rule.where)
    elif isinstance(rule, ResolvedClause):
        yield from strip_pointless_clauses(rule)


def strip_pointless_clauses(clause: ResolvedClause) -> Iterator[ResolvedClause]:
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


def extract_positive_buckets(clause: ResolvedClause) -> Iterator[str]:
    if isinstance(clause, (AndClause, OrClause)):
        for child in clause.children:
            yield from extract_positive_buckets(child)

    elif isinstance(clause, SingleClause):
        if clause.key == 'attributes':
            if clause.operator is Operator.EqualTo:
                yield clause.expected
            elif clause.operator is Operator.In:
                yield from clause.expected


def extract_negative_buckets(clause: ResolvedClause) -> Iterator[str]:
    if isinstance(clause, (AndClause, OrClause)):
        for child in clause.children:
            yield from extract_negative_buckets(child)

    elif isinstance(clause, SingleClause):
        if clause.key == 'attributes':
            if clause.operator is Operator.NotEqualTo:
                yield clause.expected
            elif clause.operator is Operator.NotIn:
                yield from clause.expected
