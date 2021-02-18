sources = ['json', 'specification-yaml']

'''

this should replace the Class.load methods

If we define a set of lambdas for determining if a particular loader should be called,
and we keep all of the loaders in here, maybe in distinct files but maybe not, then
we should be able to easily switch between "load from ambiguous yaml-spec" to "load from dumped json".

I hope.

'''

from ..base import RuleState

from ..rule.course import CourseRule
from ..solution.course import CourseSolution
from ..result.course import CourseResult


RESULT = 'result'
RULE = 'rule'


def load(data: Dict) -> Any:
    key = data['type']

    if key == 'course':
        state = RuleState(data['state'])
        if state == RuleState.Rule:
            return CourseRule(**data)
        elif state == RuleState.Solution:
            return CourseSolution(**data)
        elif state == RuleState.Result:
            return CourseResult(**data)
