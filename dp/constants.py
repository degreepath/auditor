# mypy: warn_unreachable = False

from typing import Any, Union
from enum import Enum
import logging

import attr

logger = logging.getLogger(__name__)


class KnownConstants(Enum):
    MatriculationYear = "$matriculation-year"
    TermsOnCampusSinceMajorDeclaration = "$terms-on-campus-since-major-declaration"


@attr.s(slots=True, kw_only=True, frozen=True, auto_attribs=True)
class Constants:
    matriculation_year: int = 0

    def get_by_name(self, v: Union[str, Any]) -> Any:
        if type(v) != str:
            return v

        if not v.startswith('$'):
            return v

        key = KnownConstants(v)

        if key is KnownConstants.MatriculationYear:
            return self.matriculation_year
        elif key is KnownConstants.TermsOnCampusSinceMajorDeclaration:
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

        return True
