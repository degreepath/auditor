from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import logging


@dataclass(frozen=True)
class AuditedRule:
    by: str
    message: Optional[str]

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "department-audited" in data or "department_audited" in data or "department audited" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict):
        by = 'department' if data.get("department-audited", data.get("department_audited", data.get("department audited", False))) else 'unknown'
        message = data.get('message', None)
        return AuditedRule(by=by, message=message)

    def validate(self, ctx: Any) -> bool:
        assert self.validate != 'unknown'
        return True

    def solutions(self, *, ctx, path: List):
        logging.debug(f"{path} AuditedRule#solutions")
        yield self
