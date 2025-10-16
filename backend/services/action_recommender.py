from typing import List, Dict, Any
from datetime import datetime
import uuid


class ActionRecommender:
    """
    Generates and prioritizes action recommendations.
    Converts agent recommendations into actionable items with templates.
    """
    
    def __init__(self):
        self.priority_weights = {
            "urgent": 10,
            "high": 7,
            "medium": 4,
            "low": 2
        }
    
    def create_action_items(self, agent_recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert agent recommendations into action items.
        
        Args:
            agent_recommendations: List of recommendations from agents
            
        Returns:
            List of formatted action items
        """
        action_items = []
        
        for rec in agent_recommendations:
            action_item = {
                "action_id": f"act_{uuid.uuid4().hex[:8]}",
                "title": rec.get("title", "Action Required"),
                "description": rec.get("expected_impact", ""),
                "priority": rec.get("priority", "medium"),
                "priority_score": self._calculate_priority_score(rec),
                "impact": {
                    "description": rec.get("expected_impact", ""),
                    "probability": rec.get("success_probability", 70)
                },
                "effort": rec.get("effort", "Unknown"),
                "action_type": rec.get("action", "general"),
                "template": rec.get("template"),
                "deadline": self._calculate_deadline(rec.get("priority", "medium")),
                "created_by": rec.get("source_agent", "system"),
                "confidence": rec.get("agent_confidence", 70),
                "status": "pending",
                "created_at": datetime.utcnow().isoformat()
            }
            
            action_items.append(action_item)
        
        # Sort by priority score
        action_items.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return action_items
    
    def _calculate_priority_score(self, recommendation: Dict[str, Any]) -> float:
        """
        Calculate numeric priority score.
        Score = (Priority Weight × 0.4) + (Success Probability × 0.06)
        """
        priority = recommendation.get("priority", "medium")
        success_prob = recommendation.get("success_probability", 50)
        
        priority_score = self.priority_weights.get(priority, 4)
        
        # Combine priority and success probability
        score = (priority_score * 0.4) + (success_prob * 0.06)
        
        return round(score, 2)
    
    def _calculate_deadline(self, priority: str) -> str:
        """Calculate suggested deadline based on priority."""
        if priority == "urgent":
            return "today"
        elif priority == "high":
            return "this_week"
        elif priority == "medium":
            return "this_month"
        else:
            return "this_quarter"
    
    def get_top_actions(self, action_items: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Get top N priority actions."""
        return action_items[:limit]
    
    def format_for_display(self, action_item: Dict[str, Any]) -> Dict[str, Any]:
        """Format action item for UI display."""
        return {
            "id": action_item["action_id"],
            "title": action_item["title"],
            "priority": action_item["priority"],
            "impact": action_item["impact"]["description"],
            "effort": action_item["effort"],
            "deadline": action_item["deadline"],
            "has_template": action_item["template"] is not None
        }


