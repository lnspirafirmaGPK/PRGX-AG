from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from prgx_ag.schemas.enums import AuditStatus, IntentType


class AkashicEnvelope(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

    id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sender_id: str
    intent_type: IntentType
    payload: dict[str, Any]
    audit_status: AuditStatus
    integrity_hash: str = ''

    def compute_hash(self) -> str:
        data = {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'sender_id': self.sender_id,
            'intent_type': self.intent_type.value,
            'payload': self.payload,
            'audit_status': self.audit_status.value,
        }
        self.integrity_hash = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode('utf-8')).hexdigest()
        return self.integrity_hash
