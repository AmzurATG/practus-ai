from typing import Dict, List, Optional, Any
import pandas as pd
from .revenue_agent import RevenueAgent
from .operations_agent import OperationsAgent


class AgentRegistry:
    """
    Central registry for managing all agents.
    Routes queries to appropriate agents and coordinates multi-agent responses.
    """
    
    def __init__(self):
        self.agents = {}
        self._register_agents()
    
    def _register_agents(self):
        """Register all available agents."""
        self.agents["revenue"] = RevenueAgent()
        self.agents["operations"] = OperationsAgent()
    
    def get_agent(self, agent_id: str):
        """Get specific agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "description": agent.description
            }
            for agent in self.agents.values()
        ]
    
    def route_query(self, query: str) -> str:
        """
        Determine which agent should handle a query based on intent.
        
        Args:
            query: Natural language query
            
        Returns:
            Agent ID to handle the query
        """
        query_lower = query.lower()
        
        # Revenue-related keywords
        if any(keyword in query_lower for keyword in ['deal', 'revenue', 'forecast', 'pipeline', 'sales', 'win', 'close']):
            return "revenue"
        
        # Operations-related keywords
        if any(keyword in query_lower for keyword in ['project', 'resource', 'utilization', 'capacity', 'hours', 'budget', 'team']):
            return "operations"
        
        # Default to revenue agent
        return "revenue"
    
    def analyze_all(self, data: Dict[str, pd.DataFrame], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run analysis across all agents.
        
        Args:
            data: Dictionary of dataframes
            context: Optional context
            
        Returns:
            Combined analysis from all agents
        """
        results = {}
        
        for agent_id, agent in self.agents.items():
            try:
                analysis = agent.analyze(data, context)
                insights = agent.generate_insights(analysis)
                recommendations = agent.recommend_actions(insights)
                
                results[agent_id] = agent.format_response(
                    analysis=analysis,
                    insights=insights,
                    recommendations=recommendations,
                    confidence=agent.calculate_confidence(85, 80)  # Default quality scores
                )
            except Exception as e:
                print(f"Error in agent {agent_id}: {e}")
                results[agent_id] = {
                    "error": str(e),
                    "agent_id": agent_id
                }
        
        return results
    
    def get_priority_actions(self, agent_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and prioritize all recommended actions across agents.
        
        Args:
            agent_results: Combined results from analyze_all()
            
        Returns:
            Prioritized list of actions
        """
        all_actions = []
        
        for agent_id, result in agent_results.items():
            if "recommendations" in result:
                for rec in result["recommendations"]:
                    action = rec.copy()
                    action["source_agent"] = agent_id
                    action["agent_confidence"] = result.get("confidence", 70)
                    all_actions.append(action)
        
        # Priority mapping for sorting
        priority_order = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
        
        # Sort by priority and success probability
        all_actions.sort(
            key=lambda x: (
                priority_order.get(x.get("priority", "low"), 1),
                x.get("success_probability", 0)
            ),
            reverse=True
        )
        
        return all_actions


