"""Names and types that remove interpretation work.

The candidates make units and identities part of the type, so a type checker
(pyright/mypy) rejects a swapped argument that the baseline accepts.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import NewType

# --- Units in names and types -------------------------------------------


def baseline_deadline(start: float, timeout: float) -> float:
    # Seconds? Milliseconds? The reader must find a caller to know.
    return start + timeout


Milliseconds = NewType("Milliseconds", int)


def candidate_deadline_ms(
    start_ms: Milliseconds, timeout_ms: Milliseconds
) -> Milliseconds:
    return Milliseconds(start_ms + timeout_ms)


# --- Distinct identifier types -------------------------------------------

UserId = NewType("UserId", int)
TenantId = NewType("TenantId", int)


def baseline_membership_key(user_id: int, tenant_id: int) -> str:
    return f"{tenant_id}:{user_id}"


def candidate_membership_key(user_id: UserId, tenant_id: TenantId) -> str:
    return f"{tenant_id}:{user_id}"


# --- Illegal states unrepresentable --------------------------------------


@dataclass
class BaselineUpload:
    # Four booleans allow 16 combinations; only 4 are meaningful, and
    # nothing stops is_done and is_failed from both being True.
    is_started: bool = False
    is_done: bool = False
    is_failed: bool = False
    is_cancelled: bool = False


class UploadState(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CandidateUpload:
    state: UploadState = UploadState.PENDING


def baseline_describe(upload: BaselineUpload) -> str:
    if upload.is_failed:
        return "failed"
    if upload.is_cancelled:
        return "cancelled"
    if upload.is_done:
        return "done"
    if upload.is_started:
        return "running"
    return "pending"


def candidate_describe(upload: CandidateUpload) -> str:
    return upload.state.value


# --- Boolean predicates read as predicates -------------------------------


def baseline_check(path: str) -> bool:
    return path.endswith((".yml", ".yaml"))


def is_yaml_path(path: str) -> bool:
    return path.endswith((".yml", ".yaml"))
