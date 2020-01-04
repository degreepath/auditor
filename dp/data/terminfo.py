from typing import Dict, Iterable, Optional
import datetime
import enum

import attr


class TermType(enum.Enum):
    Semester = "SE"
    Interim = "IN"
    Summer = "SM"


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class TermInfo:
    start: datetime.date
    end: datetime.date
    term: str
    name: str
    type: TermType

    @staticmethod
    def from_dict(data: Dict) -> 'TermInfo':
        return TermInfo(
            start=datetime.datetime.strptime(data['start'], '%Y-%m-%d'),
            end=datetime.datetime.strptime(data['end'], '%Y-%m-%d'),
            term=data['term'],
            name=data['name'],
            type=TermType(data['type'])
        )

    def is_current_term(self, *, now: datetime.datetime) -> bool:
        return self.start <= now <= self.end


def find_current_or_next_term(terms: Iterable[TermInfo], ts: datetime.datetime) -> Optional[TermInfo]:
    terms = sorted(terms)

    for t in terms:
        if t.start <= ts <= t.end:
            return t
        elif ts <= t.end:
            return t

    return None
