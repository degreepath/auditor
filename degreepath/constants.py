from dataclasses import dataclass
from typing import Any
import logging

logger = logging.getLogger(__name__)

VALID_CLAUSE_CONSTANTS = [
    '$senior-year',
    '$junior-year',
    '$major-declaration',
    '$matriculation-year',
]


@dataclass(frozen=True)
class Constants:
    matriculation_year: int

    def get_by_name(self, v: Any) -> Any:
        if type(v) != str:
            return v

        if not v.startswith('$'):
            return v

        if v == '$matriculation-year':
            return self.matriculation_year

        if v == '$senior-year':
            logger.critical("TODO: support constant value %s", v)
            return 0

        if v == '$junior-year':
            logger.critical("TODO: support constant value %s", v)
            return 0

        if v == '$major-declaration':
            logger.critical("TODO: support constant value %s", v)
            return 0

        raise Exception('value constants must be one of {}; got {} ({})'.format(VALID_CLAUSE_CONSTANTS, v, type(v)))

    @staticmethod
    def validate(v: Any) -> bool:
        if type(v) != str:
            return True

        if not v.startswith('$'):
            return True

        return v in VALID_CLAUSE_CONSTANTS
