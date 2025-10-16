from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class InsightType(str, Enum):
    """Types of insights agents can generate"""
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    ANOMALY = "anomaly"
    TREND = "trend"
    RECOMMENDATION = "recommendation"


class Priority(str, Enum):
    """Priority levels"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentInsight(BaseModel):
    """Individual insight from an agent"""
    type: InsightType
    priority: Priority
    message: str = Field(..., description="Human-readable insight message")
    impact: str = Field(..., description="Expected impact description")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Supporting data")


class AgentRecommendation(BaseModel):
    """Actionable recommendation from an agent"""
    action: str = Field(..., description="Action identifier")
    title: str = Field(..., description="Action title")
    priority: Priority
    expected_impact: str = Field(..., description="Expected outcome")
    effort: str = Field(..., description="Effort required: 15 minutes, 1 hour, etc.")
    success_probability: int = Field(..., ge=0, le=100, description="Success probability 0-100")
    template: Optional[Dict[str, Any]] = Field(default=None, description="Action template data")


class AgentAnalysis(BaseModel):
    """Analysis result from an agent"""
    metric: str = Field(..., description="Metric being analyzed")
    value: Any = Field(..., description="Current value")
    trend: Optional[str] = Field(default=None, description="Trend: increasing, decreasing, stable")
    context: str = Field(..., description="Context description")


class AgentResponse(BaseModel):
    """Standard response format from agents"""
    agent_id: str = Field(..., description="Agent identifier")
    analysis: AgentAnalysis
    insights: List[AgentInsight] = Field(default_factory=list)
    recommendations: List[AgentRecommendation] = Field(default_factory=list)
    confidence: int = Field(default=85, ge=0, le=100)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


