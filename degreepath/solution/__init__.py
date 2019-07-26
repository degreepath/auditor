from typing import Union

from .course import CourseSolution
from .count import CountSolution
from .action import ActionSolution
from .given import FromSolution
from .requirement import RequirementSolution

Solution = Union[CourseSolution, CountSolution]
