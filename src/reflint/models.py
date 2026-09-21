from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ReferenceEntry:
    key: str
    entry_type: str
    fields: dict[str, str]
    line: int | None = None


@dataclass(frozen=True)
class Finding:
    path: Path
    severity: Severity
    code: str
    message: str
    entry_key: str | None = None
    line: int | None = None
