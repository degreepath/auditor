from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any, Dict, Union, Set, TYPE_CHECKING
import logging
from collections import defaultdict
import itertools
import copy

from frozendict import frozendict

from .data import CourseInstance, CourseStatus
from .save import SaveRule
from .rule import CourseRule


@dataclass(frozen=False)
class RequirementContext:
    transcript: List = field(default_factory=list)
    requirements: Dict = field(default_factory=dict)
    save_rules: Dict = field(default_factory=dict)
    requirement_cache: Dict = field(default_factory=dict)
    multicountable: List[List] = field(default_factory=list)
    claims: Dict[str, Set] = field(default_factory=lambda: defaultdict(set))

    def find_course(self, c: str) -> Optional[CourseInstance]:
        try:
            return next(
                course
                for course in self.completed_courses()
                if (course.course() == c or course.course_shorthand() == c)
            )
        except StopIteration:
            return None

    def has_course(self, c: str) -> bool:
        return self.find_course(c) is not None

    def completed_courses(self):
        return (
            course
            for course in self.transcript
            if course.status != CourseStatus.DidNotComplete
        )

    def checkpoint(self):
        return copy.deepcopy(self.claims)

    def restore_to_checkpoint(self, claims):
        self.claims = copy.deepcopy(claims)

    def reset_claims(self):
        self.claims = defaultdict(set)

    def make_claim(
        self, *,
        course: CourseInstance,
        path: List[str],
        clause: Union,
        transcript: List[CourseInstance],
        allow_claimed: bool = False
    ):
        """
        If the crsid is not in the claims dictionary, insert it with an empty list.

        If the course that is being claimed has an empty list of claimants,
        then the claim succeeds.

        Otherwise...

        If the claimant is a {course} rule specified with the {including-claimed} option,
        the claim is recorded, and succeeds.

        If the claimed course matches multiple `multicountable` rulesets,
            the first ruleset applicable to both the course and the claimant is selected.

        If the claimed course matches a `multicountable` ruleset,
            and the claimant is within said `multicountable` ruleset,
            and the claimant's clause has not already been used as a claim on this course,
            then the claim is recorded, and succeeds.

        Otherwise, the claim is rejected, with a list of the prior confirmed claims.
        """
        if clause is None:
            raise Exception("clause must be provided")

        claim = Claim(crsid=course.crsid, clbid=course.clbid, claimant_path=tuple(path), value=clause)

        # If the claimant is a CourseRule specified with the `.allow_claimed` option,
        # the claim succeeds (and is not recorded).
        if allow_claimed or isinstance(clause, CourseRule) and clause.allow_claimed:
            return ClaimAttempt(claim)

        potential_conflicts = [cl for cl in self.claims[course.crsid] if cl.crsid == claim.crsid]

        # allow topics courses to be taken multiple times
        if course.is_topic:
            mapped_transcript = {c.clbid: c for c in transcript}
            conflicts_are_topics = (
                mapped_transcript[clm.clbid].is_topic
                for clm in potential_conflicts
                if clm.clbid in mapped_transcript
            )

            if all(conflicts_are_topics):
                conflicting_clbids = set(claim.clbid for claim in potential_conflicts)

                if course.clbid not in conflicting_clbids:
                    courses_are_equivalent = (course.crsid == claim.crsid for claim in potential_conflicts)

                    if all(courses_are_equivalent):
                        return ClaimAttempt(claim, conflict_with=set())

        # If the course that is being claimed has an empty list of claimants,
        # then the claim succeeds.
        if not potential_conflicts:
            # print(claim)
            self.claims[course.crsid].add(claim)
            return ClaimAttempt(claim)

        applicable_rulesets = [
            ruleset
            for ruleset in self.multicountable
            if any(c.applies_to(course) for c in ruleset)
            and any(c.mc_applies_same(clause) for c in ruleset)
        ]

        claim_conflicts = set()

        # If the claimed course matches multiple `multicountable` rulesets,
        if applicable_rulesets:
            # the first ruleset applicable to both the course and the claimant is selected.
            ruleset = applicable_rulesets[0]

            # If the claimed course matches a `multicountable` ruleset,
            #   and the claimant is within said `multicountable` ruleset,
            #   and the claimant's clause has not already been used as a claim on this course,
            #   then the claim is recorded, and succeeds.
            for ruleclause in ruleset:
                for c in potential_conflicts:
                    if not ruleclause.mc_applies_same(c):
                        continue
                    claim_conflicts.add(c)
        else:
            # print('no applicable rulesets')
            claim_conflicts = potential_conflicts

        if claim_conflicts:
            return ClaimAttempt(claim, conflict_with=claim_conflicts)
        else:
            self.claims[course.crsid].add(claim)
            return ClaimAttempt(claim, conflict_with=set())


@dataclass(frozen=True)
class Claim:
    crsid: str
    clbid: str
    claimant_path: Tuple[str, ...]
    value: Union

    def to_dict(self):
        return {
            "crsid": self.crsid,
            "clbid": self.clbid,
            "claimant_path": self.claimant_path,
            "value": self.value.to_dict(),
        }


@dataclass(frozen=True)
class ClaimAttempt:
    claim: Claim
    conflict_with: Set[Claim] = field(default_factory=set)

    def failed(self) -> bool:
        return len(self.conflict_with) > 0

    def to_dict(self):
        return {
            "claim": self.claim.to_dict(),
            "claimant_path": [c.to_dict() for c in self.conflict_with],
        }


class RequirementState(object):
    def __init__(self, iterable):
        # self.iterable = iterable
        self.iter = iter(iterable)
        self.done = False
        self.vals = []

    def iter_solutions(self):
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
    result: Optional[Any] = None
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
    def load(name: str, data: Dict[str, Any], c):
        from .rule import load_rule

        children = frozendict({
            name: Requirement.load(name, r, c)
            for name, r in data.get("requirements", {}).items()
        })

        result = data.get("result", None)
        if result is not None:
            result = load_rule(result, c)

        saves = data.get("saves", data.get("save", {}))
        assert type(saves) != list

        saves = frozendict({name: SaveRule.load(name, s, c) for name, s in saves.items()})

        audited_by = None
        if data.get("department_audited", False):
            audited_by = "department"
        if data.get("department-audited", False):
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

        validated_saves: Dict = {}
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
            yield RequirementSolution.from_requirement(self, solution=None, inputs=[])
            return
        else:
            logging.debug(f"{header} has a result")

        new_ctx = RequirementContext(
            transcript=ctx.transcript,
            save_rules={s.name: s for s in self.saves.values()},
            requirements={r.name: r for r in self.requirements.values()},
        )

        path = [*path, ".result"]

        ident = ",".join([*path, self.name])

        for i, solution in enumerate(self.result.solutions(ctx=new_ctx, path=path)):
            yield RequirementSolution.from_requirement(
                self, inputs=[(ident, i)], solution=solution
            )

    def estimate(self, *, ctx: RequirementContext):
        new_ctx = RequirementContext(
            transcript=ctx.transcript,
            save_rules={s.name: s for s in self.saves.values()},
            requirements={r.name: r for r in self.requirements.values()},
        )

        return self.result.estimate(ctx=new_ctx)


@dataclass(frozen=True)
class RequirementSolution:
    name: str
    saves: Any  # frozendict[str, SaveRule]
    requirements: Any  # frozendict[str, Requirement]
    result: Optional[Any]
    inputs: List[Tuple[str, int]]
    message: Optional[str] = None
    audited_by: Optional[str] = None
    contract: bool = False

    @staticmethod
    def from_requirement(req: Requirement, *, solution: Optional[Any], inputs: List[Tuple[str, int]]):
        return RequirementSolution(
            inputs=inputs,
            result=solution,
            name=req.name,
            saves=req.saves,
            requirements=req.requirements,
            message=req.message,
            audited_by=req.audited_by,
            contract=req.contract,
        )

    def matched(self):
        return self.result

    def to_dict(self):
        return {
            "type": "requirement",
            "name": self.name,
            "saves": {name: s.to_dict() for name, s in self.saves.items()},
            "requirements": {name: r.to_dict() for name, r in self.requirements.items()},
            "message": self.message,
            "result": self.result.to_dict() if self.result else None,
            "audited_by": self.audited_by,
            "contract": self.contract,
            "state": self.state(),
            "status": "pending",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": self.claims(),
        }

    def state(self):
        if self.audited_by:
            return "solution"
        if not self.result:
            return "solution"
        return self.result.state()

    def claims(self):
        if self.audited_by:
            return []
        if not self.result:
            return []
        return self.result.claims()

    def ok(self):
        if not self.result:
            return False
        return self.result.ok()

    def audit(self, *, ctx: RequirementContext, path: List):
        if not self.result:
            # TODO: return something better
            return RequirementResult.from_solution(self, result=None)

        result = self.result.audit(ctx=ctx, path=path)

        return RequirementResult.from_solution(self, result=result)


@dataclass(frozen=True)
class RequirementResult:
    name: str
    saves: Any  # frozendict[str, SaveRule]
    requirements: Any  # frozendict[str, Requirement]
    inputs: List[Tuple[str, int]]
    message: Optional[str] = None
    result: Optional[Any] = None
    audited_by: Optional[str] = None
    contract: bool = False

    @staticmethod
    def from_solution(sol: RequirementSolution, *, result: Optional[Any]):
        return RequirementResult(
            name=sol.name,
            saves=sol.saves,
            requirements=sol.requirements,
            inputs=sol.inputs,
            message=sol.message,
            audited_by=sol.audited_by,
            contract=sol.contract,
            result=result,
        )

    def to_dict(self):
        return {
            "type": "requirement",
            "name": self.name,
            "saves": {name: s.to_dict() for name, s in self.saves.items()},
            "requirements": {
                name: r.to_dict() for name, r in self.requirements.items()
            },
            "message": self.message,
            "result": self.result.to_dict() if self.result else None,
            "audited_by": self.audited_by,
            "contract": self.contract,
            "state": self.state(),
            "status": "pass" if self.ok() else "problem",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": [c.to_dict() for c in self.claims()],
        }

    def state(self):
        if self.audited_by:
            return "result"
        if not self.result:
            return []
        return self.result.state()

    def claims(self):
        if self.audited_by:
            return []
        if not self.result:
            return []
        return self.result.claims()

    def ok(self) -> bool:
        # TODO: remove this once exceptions are in place
        if self.audited_by:
            return True
        if not self.result:
            return False
        return self.result.ok()

    def rank(self):
        if not self.result:
            return 0

        boost = 1 if self.ok() else 0
        return self.result.rank() + boost
