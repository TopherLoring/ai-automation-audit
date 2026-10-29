from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    CRITICAL = "critical"   # Likely to cause silent data loss or security issue
    HIGH = "high"           # Will cause production pain / duplicates / missed alerts
    MEDIUM = "medium"       # Best-practice gap that increases operational risk
    LOW = "low"             # Nice-to-have hygiene
    INFO = "info"           # Observation only


SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}


@dataclass
class Finding:
    check_id: str
    title: str
    severity: Severity
    node_name: str | None
    description: str
    evidence: str
    recommendation: str
    effort_minutes: int = 15
    tags: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "title": self.title,
            "severity": self.severity.value,
            "node_name": self.node_name,
            "description": self.description,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "effort_minutes": self.effort_minutes,
            "tags": self.tags,
            "meta": self.meta,
        }