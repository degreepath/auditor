from typing import Any, Iterator, Union, Dict
import requests
import os

from .constants import Constants
from .area import AreaOfStudy

from .base import Base, BaseRequirementRule, BaseCountRule, BaseQueryRule
from .base.query import QuerySourceType
from .clause import ResolvedClause, AndClause, OrClause, SingleClause
from .operator import Operator
import json


def discover_clause_potential(area: AreaOfStudy, c: Constants) -> Dict[int, Dict[str, Any]]:
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
            result[parsed['hash']] = {'error': False, 'clbids': parsed['clbids']}
        elif 'hash' in parsed and parsed['error'] is True:
            result[parsed['hash']] = {'error': True, 'clbids': []}
        else:
            result[dict_clause['hash']] = {'error': True, 'clbids': []}

    return result


def find_all_clauses(rule: Union[Base, ResolvedClause]) -> Iterator[ResolvedClause]:
    if isinstance(rule, (AreaOfStudy, BaseRequirementRule)):
        if rule.result:
            yield from find_all_clauses(rule.result)
    elif isinstance(rule, BaseCountRule):
        for child in rule.items:
            yield from find_all_clauses(child)
    elif isinstance(rule, BaseQueryRule):
        if rule.source_type is QuerySourceType.Courses:
            if rule.where:
                yield from find_all_clauses(rule.where)
    elif isinstance(rule, ResolvedClause):
        yield rule


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
