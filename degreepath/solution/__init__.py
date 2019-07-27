from typing import Union

from .course import CourseSolution
from .count import CountSolution
from .query import QuerySolution

from .requirement import RequirementSolution

Solution = Union[CourseSolution, CountSolution, QuerySolution]
