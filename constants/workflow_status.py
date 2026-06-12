from enum import Enum


class WorkflowStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_HUMAN_CONFIRMATION = "waiting_human_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"


class ConfirmationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REVISE_REQUIRED = "revise_required"
    REJECTED = "rejected"


class ConfirmationAction(str, Enum):
    APPROVE = "approve"
    REVISE = "revise"
    REJECT = "reject"

class AgentStepStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class CheckpointMode(str, Enum):
    RECOVERY = "recovery"
    CONFIRMATION = "confirmation"
    