from __future__ import annotations
from typing import List, Optional
from .requirement import Requirement
from .rule.save import Rule as SaveRule

ReqList = List[Requirement]
OptReqList = Optional[ReqList]

SaveList = List[SaveRule]
OptSaveList = Optional[SaveList]
