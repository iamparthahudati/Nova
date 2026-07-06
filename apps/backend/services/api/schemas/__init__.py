"""Pydantic API schemas — canonical HTTP contracts."""

from .chat import ChatRequest, ChatResponse, ToolCallRecord
from .calendar import CalendarEventResponse, CalendarResponse
from .common import HealthResponse, MutationMeta, OkResponse
from .graph import (
    GraphEdgeResponse,
    GraphEntityResponse,
    GraphRelatedResponse,
    GraphSnapshotResponse,
    GraphStatsResponse,
)
from .home import HomeCard, HomePanel, HomePanelItem, HomeResponse
from .memory import MemoryRecallResponse, MemoryResponse
from .memories import MemoriesListResponse, MemoriesStatsResponse
from .products import ProductResponse, ProductsResponse
from .reminders import (
    CreateReminderRequest,
    ReminderMutationResponse,
    ReminderResponse,
    RemindersResponse,
)
from .settings import ProfileObservationResponse, SettingsResponse
from .spending import (
    LogSpendingRequest,
    SpendingMutationResponse,
    SpendingResponse,
    SpendingSummaryResponse,
    SpendingTransactionResponse,
)
from .system import SubsystemDiagnostic, SystemStatusResponse
from .tasks import CreateTaskRequest, TaskMutationResponse, TaskResponse, TasksResponse

__all__ = [
    "HealthResponse",
    "OkResponse",
    "MutationMeta",
    "ChatRequest",
    "ChatResponse",
    "ToolCallRecord",
    "TaskResponse",
    "TasksResponse",
    "CreateTaskRequest",
    "TaskMutationResponse",
    "ReminderResponse",
    "RemindersResponse",
    "CreateReminderRequest",
    "ReminderMutationResponse",
    "MemoryResponse",
    "MemoryRecallResponse",
    "MemoriesListResponse",
    "MemoriesStatsResponse",
    "CalendarEventResponse",
    "CalendarResponse",
    "GraphEntityResponse",
    "GraphEdgeResponse",
    "GraphRelatedResponse",
    "GraphSnapshotResponse",
    "GraphStatsResponse",
    "HomeCard",
    "HomePanel",
    "HomePanelItem",
    "HomeResponse",
    "SpendingTransactionResponse",
    "SpendingSummaryResponse",
    "SpendingResponse",
    "LogSpendingRequest",
    "SpendingMutationResponse",
    "ProductResponse",
    "ProductsResponse",
    "SettingsResponse",
    "ProfileObservationResponse",
    "SubsystemDiagnostic",
    "SystemStatusResponse",
]
