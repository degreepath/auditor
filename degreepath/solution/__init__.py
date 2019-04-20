from typing import Union

from .course import CourseSolution
from .count import CountSolution
from .action import ActionSolution
from .given import FromSolution

Solution = Union[CourseSolution, CountSolution]
