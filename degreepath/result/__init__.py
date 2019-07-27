from typing import Union

from .count import CountResult
from .course import CourseResult
from .query import QueryResult
from .requirement import RequirementResult

Result = Union[CountResult, CourseResult, QueryResult]
