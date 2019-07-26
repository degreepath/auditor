from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from ...constants import Constants


@dataclass(frozen=True)
class FromInput:
    mode: str
    itemtype: str
    repeat_mode: Optional[str]

    def to_dict(self):
        return {
            "type": "from-input",
            "mode": self.mode,
            "itemtype": self.itemtype,
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
            raise ValueError('from:saves not supported')

        elif "requirements" in data or "requirement" in data:
            raise ValueError('from:requirements not supported')

        else:
            raise KeyError(f"expected student; got {list(data.keys())}")

        return FromInput(
            mode=mode,
            itemtype=itemtype,
            repeat_mode=repeat_mode,
        )

    def validate(self, *, ctx):
        assert isinstance(self.mode, str)

        if self.mode == "student":
            allowed = ["courses", "music performances", "areas"]
            assert self.itemtype in allowed, f"when from:student, '{self.itemtype}' must in in {allowed}"

        else:
            raise NameError(f"unknown 'from' type {self.mode}")
