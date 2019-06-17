from typing import Union

from .count import CountResult
from .course import CourseResult
from .given import FromResult

# from .reference import ReferenceResult

Result = Union[CountResult, CourseResult, FromResult]
