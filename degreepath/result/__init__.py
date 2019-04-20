from typing import Union

from .count import CountResult
from .course import CourseResult

# from .reference import ReferenceResult

Result = Union[CountResult, CourseResult]
