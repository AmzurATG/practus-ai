from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from .base_agent import BaseAgent


class OperationsAgent(BaseAgent):
    """
    Operations Agent - Monitors project health, resource utilization, and delivery.
    Identifies budget overruns, capacity issues, and optimization opportunities.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="operations_agent",
            name="Operations Intelligence Agent",
            description="Monitors projects, resources, and utilization"
        )
    
    def analyze(self, data: Dict[str, pd.DataFrame], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze operations and resource data."""
        analysis = {
            "utilization": 0,
            "total_hours": 0,
            "project_count": 0,
            "overrun_projects": [],
            "capacity_status": {}
        }
        
        # Find timesheet/resource data
        timesheet_df = self._find_timesheet_data(data)
        resource_df = self._find_resource_data(data)
        
        if timesheet_df is not None and not timesheet_df.empty:
            analysis.update(self._analyze_timesheet(timesheet_df))
        
        if resource_df is not None and not resource_df.empty:
            analysis.update(self._analyze_resources(resource_df))
        
        return analysis
    
    def generate_insights(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate operational insights."""
        insights = []
        
        # Utilization insight
        utilization = analysis_results.get("utilization", 0)
        if utilization < 70:
            insights.append({
                "type": "risk",
                "priority": "high",
                "message": f"Low resource utilization at {utilization}%",
                "impact": "Capacity underutilized, revenue at risk",
                "confidence": 85,
                "data": {"utilization": utilization}
            })
        elif utilization > 90:
            insights.append({
                "type": "risk",
                "priority": "high",
                "message": f"High resource utilization at {utilization}%",
                "impact": "Team burnout risk, quality concerns",
                "confidence": 82,
                "data": {"utilization": utilization}
            })
        elif utilization >= 75 and utilization <= 85:
            insights.append({
                "type": "opportunity",
                "priority": "low",
                "message": f"Optimal utilization at {utilization}%",
                "impact": "Well-balanced capacity",
                "confidence": 88,
                "data": {"utilization": utilization}
            })
        
        # Project health insights
        overrun_projects = analysis_results.get("overrun_projects", [])
        if len(overrun_projects) > 0:
            insights.append({
                "type": "risk",
                "priority": "urgent",
                "message": f"{len(overrun_projects)} projects showing budget concerns",
                "impact": "Margin erosion and client satisfaction risk",
                "confidence": 80,
                "data": {"projects": overrun_projects}
            })
        
        # Capacity insight
        capacity = analysis_results.get("capacity_status", {})
        bench_count = capacity.get("bench_resources", 0)
        if bench_count > 5:
            insights.append({
                "type": "opportunity",
                "priority": "medium",
                "message": f"{bench_count} consultants available on bench",
                "impact": "Opportunity for new projects or internal initiatives",
                "confidence": 90,
                "data": capacity
            })
        
        return insights
    
    def recommend_actions(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate action recommendations."""
        recommendations = []
        
        for insight in insights:
            if "utilization" in insight["message"].lower() and insight["priority"] == "high":
                if "low" in insight["message"].lower():
                    recommendations.append({
                        "action": "find_new_opportunities",
                        "title": "Identify new project opportunities",
                        "priority": "high",
                        "expected_impact": "Increase utilization by 10-15%",
                        "effort": "2 hours",
                        "success_probability": 70,
                        "template": None
                    })
                else:  # High utilization
                    recommendations.append({
                        "action": "review_team_capacity",
                        "title": "Review team capacity and workload",
                        "priority": "urgent",
                        "expected_impact": "Prevent burnout, maintain quality",
                        "effort": "1 hour",
                        "success_probability": 85,
                        "template": None
                    })
            
            if "budget" in insight["message"].lower() or "overrun" in insight["message"].lower():
                recommendations.append({
                    "action": "project_budget_review",
                    "title": "Conduct project budget reviews",
                    "priority": "urgent",
                    "expected_impact": "Identify cost savings and prevent further overruns",
                    "effort": "30 minutes per project",
                    "success_probability": 75,
                    "template": {
                        "type": "meeting",
                        "agenda": ["Review budget variance", "Identify causes", "Action plan"]
                    }
                })
            
            if "bench" in insight["message"].lower():
                recommendations.append({
                    "action": "market_bench_resources",
                    "title": "Market available consultants",
                    "priority": "medium",
                    "expected_impact": f"Convert bench capacity to revenue",
                    "effort": "1 hour",
                    "success_probability": 65,
                    "template": None
                })
        
        return recommendations
    
    # Helper methods
    def _find_timesheet_data(self, data: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Find timesheet dataframe."""
        for key, df in data.items():
            if 'whizible' in key.lower() or 'timesheet' in key.lower():
                return df
            if 'hours' in str(df.columns).lower() and 'project' in str(df.columns).lower():
                return df
        return None
    
    def _find_resource_data(self, data: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Find resource allocation dataframe."""
        for key, df in data.items():
            if 'plotting' in key.lower() or 'resource' in key.lower():
                return df
        return None
    
    def _analyze_timesheet(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze timesheet data for utilization."""
        result = {}
        
        try:
            hours_col = self._find_column(df, ['hours', 'Hours'])
            project_col = self._find_column(df, ['project', 'Project'])
            
            if hours_col:
                result["total_hours"] = self.safe_sum(df[hours_col])
                
                # Simple utilization calculation (assuming 8 hour days, 20 work days/month)
                unique_employees = df.get('EmployeeCode', df.get('employee', pd.Series())).nunique()
                if unique_employees > 0:
                    available_hours = unique_employees * 8 * 20  # Rough estimate
                    result["utilization"] = min(100, int((result["total_hours"] / available_hours) * 100))
            
            if project_col:
                result["project_count"] = df[project_col].nunique()
        except Exception as e:
            print(f"Error analyzing timesheet: {e}")
        
        return result
    
    def _analyze_resources(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze resource allocation data."""
        result = {}
        
        try:
            # Look for allocation percentages or bench indicators
            if 'Bench' in str(df.columns) or 'bench' in str(df.columns).lower():
                bench_resources = df[df.apply(lambda row: 'bench' in str(row).lower(), axis=1)]
                result["capacity_status"] = {
                    "bench_resources": len(bench_resources),
                    "total_resources": len(df)
                }
        except Exception as e:
            print(f"Error analyzing resources: {e}")
        
        return result
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Find column by checking multiple possible names."""
        for col in df.columns:
            col_lower = col.lower()
            if any(name.lower() in col_lower for name in possible_names):
                return col
        return None


