# from __future__ import annotations
# from dataclasses import dataclass
# from typing import Dict, Union, List, Tuple, Optional, TYPE_CHECKING
# import re
# import itertools
# import logging

# from ..requirement import RequirementState
# from ..solution import CourseSolution
# from ..result import ReferenceResult

# if TYPE_CHECKING:
#     from ..requirement import RequirementContext, RequirementSolution
#     from ..result import Result


# @dataclass(frozen=True)
# class ReferenceSolution:
#     name: str
#     inputs: List[Tuple[str, int]]
#     solution: RequirementSolution

#     def to_dict(self):
#         return {
#             "type": "reference",
#             "name": self.name,
#             "inputs": self.inputs,
#             "state": self.state(),
#             "status": "pending",
#             "ok": self.ok(),
#             "rank": self.rank(),
#             "claims": self.claims(),
#         }

#     def state(self):
#         return "solution"

#     def claims(self):
#         return self.solution.claims()

#     def rank(self):
#         return self.solution.rank()

#     def ok(self):
#         return self.solution.ok()

#     def flatten(self):
#         return self.solution.flatten()

#     def audit(self, *, ctx: RequirementContext, path: List) -> Result:
#         return ReferenceResult.from_req(self.solution.audit(ctx=ctx, path=path))
