from typing import Optional
from pydantic import BaseModel


class GateSnapshot(BaseModel):
    state: str
    last_action: Optional[str]
    last_change: str
    is_busy: bool


class CommandResponse(BaseModel):
    ok: bool
    action: str
    state: str
    detail: str