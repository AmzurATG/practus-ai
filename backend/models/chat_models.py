from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatQuery(BaseModel):
    """Request model for chat queries"""
    query: str = Field(..., min_length=1, description="User's natural language query")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class VisualizationConfig(BaseModel):
    """Configuration for chart visualization"""
    type: str = Field(..., description="Chart type: table, bar, line, pie, funnel")
    data: Dict[str, Any] = Field(..., description="Chart data")
    layout: Optional[Dict[str, Any]] = Field(default=None, description="Plotly layout config")


class ActionItem(BaseModel):
    """Recommended action from chat"""
    action_id: str
    label: str
    impact: str
    description: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat queries"""
    query: str
    intent: str = Field(..., description="Detected intent: pipeline_analysis, forecast, resource, etc.")
    agent: str = Field(..., description="Agent that handled the query")
    answer: str = Field(..., description="Natural language answer")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Raw data for visualization")
    visualization: Optional[VisualizationConfig] = Field(default=None, description="Chart configuration")
    actions: Optional[List[ActionItem]] = Field(default=[], description="Recommended actions")
    suggested_followups: Optional[List[str]] = Field(default=[], description="Suggested next questions")
    confidence: int = Field(default=85, ge=0, le=100, description="Confidence score")


class ChatHistory(BaseModel):
    """Chat message history"""
    id: int
    query: str
    response: str
    agent_used: str
    timestamp: datetime


