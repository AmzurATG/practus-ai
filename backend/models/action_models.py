from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ActionStatus(str, Enum):
    """Action item status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ActionTemplate(BaseModel):
    """Template for an action"""
    type: str = Field(..., description="Template type: email, meeting, task, etc.")
    subject: Optional[str] = None
    body: Optional[str] = None
    recipients: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None


class ActionItemCreate(BaseModel):
    """Create new action item"""
    title: str = Field(..., min_length=1)
    description: str
    priority: str = Field(..., description="urgent, high, medium, low")
    impact: Dict[str, Any] = Field(..., description="Impact metrics")
    effort: str = Field(..., description="Effort required")
    action_type: str = Field(..., description="Type of action")
    template: Optional[ActionTemplate] = None
    deadline: Optional[str] = None


class ActionItemResponse(BaseModel):
    """Action item with full details"""
    action_id: str
    title: str
    description: str
    priority: str
    priority_score: float
    impact: Dict[str, Any]
    effort: str
    action_type: str
    template: Optional[ActionTemplate] = None
    deadline: Optional[str] = None
    created_by: str
    confidence: int
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime


class ActionOutcome(BaseModel):
    """Record outcome of an action"""
    action_id: str
    success: bool
    notes: Optional[str] = None
    metrics_change: Optional[Dict[str, Any]] = None


