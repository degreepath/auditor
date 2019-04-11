from typing import Union

from .count import CountResult
from .course import CourseResult

Result = Union[CountResult, CourseResult]
