from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict, Iterable, TYPE_CHECKING
import logging
import itertools

from frozendict import frozendict

from .data import CourseInstance, CourseStatus
from .save import SaveRule

if TYPE_CHECKING:
    from .rule import Rule


@dataclass(frozen=False)
class RequirementContext:
    transcript: List[CourseInstance] = field(default_factory=list)
    requirements: Dict[str, Requirement] = field(default_factory=dict)
    save_rules: Dict[str, SaveRule] = field(default_factory=dict)
    requirement_cache: Dict[Requirement, RequirementState] = field(default_factory=dict)

    def find_course(self, c: str) -> Optional[CourseInstance]:
        try:
            return next(
                course
                for course in self.transcript
                if course.status != CourseStatus.DidNotComplete and course.course() == c
            )
        except StopIteration:
            return None


class RequirementState(object):
    def __init__(self, iterable):
        self.iterable = iterable
        self.iter = iter(iterable)
        self.done = False
        self.vals = []

    def __iter__(self):
        if self.done:
            return iter(self.vals)

        # chain vals so far & then gen the rest
        return itertools.chain(self.vals, self._gen_iter())

    def _gen_iter(self):
        # gen new vals, appending as it goes
        for new_val in self.iter:
            self.vals.append(new_val)
            yield new_val

        self.done = True


@dataclass(frozen=True)
class Requirement:
    name: str
    saves: Any  # frozendict[str, SaveRule]
    requirements: Any  # frozendict[str, Requirement]
    message: Optional[str] = None
    result: Optional[Rule] = None
    audited_by: Optional[str] = None
    contract: bool = False

    def to_dict(self):
        return {
            "name": self.name,
            "saves": {name: s.to_dict() for name, s in self.saves.items()},
            "requirements": {
                name: r.to_dict() for name, r in self.requirements.items()
            },
            "message": self.message,
            "result": self.result.to_dict(),
            "audited_by": self.audited_by,
            "contract": self.contract,
        }

    @staticmethod
    def load(name: str, data: Dict[str, Any]) -> Requirement:
        from .rule import load_rule

        children = frozendict(
            {
                name: Requirement.load(name, r)
                for name, r in data.get("requirements", {}).items()
            }
        )

        result = data.get("result", None)
        if result is not None:
            result = load_rule(result)

        saves = frozendict(
            {name: SaveRule.load(name, s) for name, s in data.get("saves", {}).items()}
        )

        audited_by = None
        if data.get("department_audited", False):
            audited_by = "department"
        elif data.get("registrar_audited", False):
            audited_by = "registrar"

        return Requirement(
            name=name,
            message=data.get("message", None),
            requirements=children,
            result=result,
            saves=saves,
            contract=data.get("contract", False),
            audited_by=audited_by,
        )

    def validate(self, *, ctx: RequirementContext):
        assert isinstance(self.name, str)
        assert self.name.strip() != ""

        if self.message is not None:
            assert isinstance(self.message, str)
            assert self.message.strip() != ""

        children = self.requirements

        validated_saves: Dict[str, SaveRule] = {}
        for save in self.saves.values():
            new_ctx = RequirementContext(
                transcript=ctx.transcript,
                save_rules={name: s for name, s in validated_saves.items()},
                requirements=children,
            )
            save.validate(ctx=new_ctx)
            validated_saves[save.name] = save

        new_ctx = RequirementContext(
            transcript=ctx.transcript,
            save_rules={name: s for name, s in self.saves.items() or {}},
            requirements=children,
        )

        if self.result is not None:
            self.result.validate(ctx=new_ctx)

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        path = [*path, f"$req->{self.name}"]

        header = f'{path}\n\trequirement "{self.name}"'

        logging.debug(f"{header} has not been evaluated")

        if not self.message:
            logging.debug(f"{header} has no message")

        if not self.audited_by:
            logging.debug(f"{header} is not audited")

        if not self.result:
            logging.debug(f"{header} does not have a result")
            return
        else:
            logging.debug(f"{header} has a result")

        new_ctx = RequirementContext(
            transcript=ctx.transcript,
            save_rules={s.name: s for s in self.saves.values()},
            requirements={r.name: r for r in self.requirements.values()},
        )

        path = [*path, ".result"]
        for sol in self.result.solutions(ctx=new_ctx, path=path):
            yield RequirementSolution(solution=sol, name=self.name)


@dataclass(frozen=True)
class RequirementSolution:
    solution: Any
    name: str

    def matched(self):
        return self.solution

    def to_dict(self):
        return {"type": "requirement", "solution": self.solution.to_dict()}

    def flatten(self):
        return self.solution.flatten()

    def audit(self, *, ctx: RequirementContext, path: List) -> RequirementResult:
        result = self.solution.audit(ctx=ctx, path=path)

        return RequirementResult(result=result, name=self.name)


@dataclass(frozen=True)
class RequirementResult:
    result: RequirementResult
    name: str

    def to_dict(self):
        return {
            "type": "requirement",
            "result": self.result.to_dict(),
            "name": self.name,
            "ok": self.ok(),
            "rank": self.rank(),
        }

    def ok(self) -> bool:
        return self.result.ok()

    def rank(self):
        boost = 1 if self.ok() else 0
        return self.result.rank() + boost
