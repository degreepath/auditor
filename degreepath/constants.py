import attr
from typing import Any
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class KnownConstants(Enum):
    SeniorYear = "$senior-year"
    JuniorYear = "$junior-year"
    MajorDeclarationDate = "$major-declaration"
    MatriculationYear = "$matriculation-year"


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class Constants:
    matriculation_year: int

    def get_by_name(self, v: Any) -> Any:
        if type(v) != str:
            return v

        if not v.startswith('$'):
            return v

        key = KnownConstants(v)
        if key is KnownConstants.MatriculationYear:
            return self.matriculation_year
        else:
            logger.critical(f"TODO: support constant value `{v}`")
            return 0

    @staticmethod
    def validate(v: Any) -> bool:
        if type(v) != str:
            return True

        if not v.startswith('$'):
            return True

        assert KnownConstants(v)
