from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict
from .rule import Rule, SaveRule


@dataclass(frozen=True)
class Requirement:
    name: str
    message: Optional[str] = None
    result: Optional[Rule] = None
    save: Optional[List[SaveRule]] = None
    requirements: Optional[List[Requirement]] = None

    @staticmethod
    def load(data: Dict) -> Requirement:
        children = data.get("requirements", None)
        if children is not None:
            children = [Requirement.load(r) for r in children]

        result = data.get("result", None)
        if result is not None:
            result = Rule.load(result)

        save = data.get("save", None)
        if save is not None:
            save = [SaveRule.load(s) for s in save]

        return Requirement(
            name=data["name"],
            message=data.get("message", None),
            requirements=children,
            result=result,
            save=save,
        )

    def validate(self):
        assert isinstance(self.name, str)
        assert self.name.strip() != ""

        if self.message is not None:
            assert isinstance(self.message, str)
            assert self.message.strip() != ""

        if self.save is not None:
            validated_saves = []
            for save in self.save:
                save.validate(requirements=self.requirements, saves=validated_saves)
                validated_saves.append(save)

        if self.result is not None:
            self.result.validate(requirements=self.requirements, saves=self.save)

        if self.requirements is not None:
            for req in self.requirements:
                req.validate()
