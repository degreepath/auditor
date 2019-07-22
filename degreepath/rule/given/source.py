from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from ppretty import ppretty
from ...constants import Constants


@dataclass(frozen=True)
class FromInput:
    mode: str
    itemtype: str
    requirements: Tuple[str, ...]
    saves: Tuple[str, ...]
    repeat_mode: Optional[str]

    def to_dict(self):
        return {
            "type": "from-input",
            "mode": self.mode,
            "itemtype": self.itemtype,
            "requirements": self.requirements,
            "saves": self.saves,
        }

    @staticmethod
    def load(data: Dict, c: Constants):
        saves: Tuple[str, ...] = tuple()
        requirements: Tuple[str, ...] = tuple()

        if "student" in data:
            mode = "student"
            itemtype = data["student"]
            repeat_mode = data.get('repeats', 'all')
            assert repeat_mode in ['first', 'all']

        elif "saves" in data or "save" in data:
            mode = "saves"
            saves = tuple(x for x in data.get("saves", [data.get("save", None)]) if x)
            itemtype = None
            repeat_mode = None

        elif "requirements" in data or "requirement" in data:
            mode = "requirements"
            requirements = tuple(x for x in data.get("requirements", [data.get("requirement", None)]) if x)
            itemtype = None
            repeat_mode = None

        elif "stored-values" in data:
            mode = "stored-values"
            requirements = tuple(data["stored-values"])
            itemtype = None
            repeat_mode = None

        else:
            raise KeyError(f"expected student, stored-values, saves, or requirements; got {list(data.keys())}")

        return FromInput(
            mode=mode,
            itemtype=itemtype,
            requirements=requirements,
            saves=saves,
            repeat_mode=repeat_mode,
        )

    def validate(self, *, ctx):
        assert isinstance(self.mode, str)

        saves = ctx.save_rules
        requirements = ctx.requirements

        lambda dbg: f"(when validating: {ppretty({'self': self, 'saves': saves, 'reqs': requirements})})"

        if self.mode == "requirements":
            # TODO: assert that the result type of all mentioned requirements is the same
            if not self.requirements and not requirements:
                raise ValueError("expected self.requirements and args.requirements to be lists")
            for name in self.requirements:
                assert isinstance(name, str), f"expected {name} to be a string"
                assert name in ctx.requirements, f"expected to find '{name}' once, but could not find it {dbg()}"

        elif self.mode == "saves":
            # TODO: assert that the result type of all mentioned saves is the same
            if not self.saves and not saves:
                raise ValueError("expected self.saves and args.saves to be lists")
            for name in self.saves:
                assert isinstance(name, str), f"expected {name} to be a string"
                assert name in ctx.save_rules, f"expected to find '{name}' once, but could not find it {dbg()}"

        elif self.mode == "student":
            allowed = ["courses", "music performances", "areas"]
            assert self.itemtype in allowed, f"when from:student, '{self.itemtype}' must in in {allowed}"

        else:
            raise NameError(f"unknown 'from' type {self.mode}")
