from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd


class BaseAgent(ABC):
    """
    Base class for all intelligent agents.
    Agents analyze data and provide insights, recommendations, and actions.
    """
    
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.confidence_threshold = 70  # Minimum confidence to report insights
    
    @abstractmethod
    def analyze(self, data: Dict[str, pd.DataFrame], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform analysis on provided data.
        
        Args:
            data: Dictionary of dataframes keyed by source name
            context: Optional context information
            
        Returns:
            Analysis results as dictionary
        """
        pass
    
    @abstractmethod
    def generate_insights(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert analysis results into actionable insights.
        
        Args:
            analysis_results: Output from analyze() method
            
        Returns:
            List of insight dictionaries
        """
        pass
    
    @abstractmethod
    def recommend_actions(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations based on insights.
        
        Args:
            insights: List of insights from generate_insights()
            
        Returns:
            List of recommended actions
        """
        pass
    
    def calculate_confidence(self, data_quality: float, analysis_strength: float) -> int:
        """
        Calculate confidence score for analysis.
        
        Args:
            data_quality: Quality score of input data (0-100)
            analysis_strength: Strength of analytical evidence (0-100)
            
        Returns:
            Confidence score (0-100)
        """
        return int((data_quality * 0.4 + analysis_strength * 0.6))
    
    def format_response(
        self,
        analysis: Dict[str, Any],
        insights: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        confidence: int
    ) -> Dict[str, Any]:
        """
        Format agent response in standard structure.
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "analysis": analysis,
            "insights": insights,
            "recommendations": recommendations,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def safe_mean(self, series: pd.Series) -> float:
        """Safely calculate mean, handling errors."""
        try:
            return float(series.mean()) if len(series) > 0 else 0.0
        except:
            return 0.0
    
    def safe_sum(self, series: pd.Series) -> float:
        """Safely calculate sum, handling errors."""
        try:
            return float(series.sum()) if len(series) > 0 else 0.0
        except:
            return 0.0
    
    def safe_count(self, series: pd.Series) -> int:
        """Safely count non-null values."""
        try:
            return int(series.notna().sum())
        except:
            return 0


