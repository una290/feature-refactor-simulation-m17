from __future__ import annotations
from typing import Dict, Any
import datetime as dt
from pydantic import BaseModel, Field
from ..core.types import Observation, Domain

class RawIngest(BaseModel):
    ts: dt.datetime
    device_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class IngressAdapter:
    domain: Domain = "unknown"

    def normalize(self, raw: RawIngest) -> Observation:
        raise NotImplementedError
