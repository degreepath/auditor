# mypy: warn_unreachable = False

from typing import Any, Union
from enum import Enum
import logging

import attr

logger = logging.getLogger(__name__)


class KnownConstants(Enum):
    MatriculationYear = "$matriculation-year"
    TermsSinceDeclaringMajor = "$terms-since-declaring-major"
    PrimaryPerformingMedium = "$primary-performing-medium"
    CurrentAreaCode = "$current-area-code"
    CurrentAreaCodeMusicExam = "$current-area-code-music-exam"


@attr.s(slots=True, kw_only=True, frozen=True, auto_attribs=True)
class Constants:
    matriculation_year: int = 0
    terms_since_declaring_major: int = 0
    primary_performing_medium: str = ''
    current_area_code: str = ''

    def get_by_name(self, v: Union[str, Any]) -> Any:
        if type(v) != str:
            return v

        if not v.startswith('$'):
            return v

        key = KnownConstants(v)

        if key is KnownConstants.MatriculationYear:
            return self.matriculation_year

        elif key is KnownConstants.TermsSinceDeclaringMajor:
            return self.terms_since_declaring_major

        elif key is KnownConstants.PrimaryPerformingMedium:
            return self.primary_performing_medium

        elif key is KnownConstants.CurrentAreaCode:
            return self.current_area_code

        elif key is KnownConstants.CurrentAreaCodeMusicExam:
            return f"Exam: {self.current_area_code}"

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
