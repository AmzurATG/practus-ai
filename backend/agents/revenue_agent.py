from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .base_agent import BaseAgent


class RevenueAgent(BaseAgent):
    """
    Revenue Agent - Analyzes deals, pipeline health, and revenue forecasting.
    Identifies stuck deals, upsell opportunities, and win probability.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="revenue_agent",
            name="Revenue Intelligence Agent",
            description="Analyzes deals, forecasts revenue, identifies opportunities"
        )
    
    def analyze(self, data: Dict[str, pd.DataFrame], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze revenue and pipeline data."""
        analysis = {
            "pipeline_health": 0,
            "total_pipeline_value": 0,
            "deal_count": 0,
            "avg_deal_size": 0,
            "stuck_deals": [],
            "forecast": {}
        }
        
        # Find deals data
        deals_df = self._find_deals_data(data)
        if deals_df is None or deals_df.empty:
            return analysis
        
        # Find amount and stage columns
        amount_col = self._find_column(deals_df, ['amount', 'value', 'deal_amount', 'revenue'])
        stage_col = self._find_column(deals_df, ['stage', 'status', 'deal_stage'])
        date_col = self._find_column(deals_df, ['date', 'closing_date', 'modified_time', 'updated'])
        
        if amount_col:
            analysis["total_pipeline_value"] = self.safe_sum(deals_df[amount_col])
            analysis["avg_deal_size"] = self.safe_mean(deals_df[amount_col])
        
        analysis["deal_count"] = len(deals_df)
        
        # Analyze stuck deals (in proposal/negotiation stages)
        if stage_col and date_col:
            stuck = self._identify_stuck_deals(deals_df, stage_col, date_col, amount_col)
            analysis["stuck_deals"] = stuck
        
        # Calculate pipeline health score
        analysis["pipeline_health"] = self._calculate_pipeline_health(deals_df, stage_col, analysis["stuck_deals"])
        
        # Simple forecast
        if amount_col:
            analysis["forecast"] = self._forecast_revenue(deals_df, amount_col, stage_col)
        
        return analysis
    
    def generate_insights(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable insights from analysis."""
        insights = []
        
        # Stuck deals insight
        stuck_deals = analysis_results.get("stuck_deals", [])
        if len(stuck_deals) > 0:
            total_at_risk = sum(deal.get("amount", 0) for deal in stuck_deals)
            insights.append({
                "type": "risk",
                "priority": "high" if total_at_risk > 500000 else "medium",
                "message": f"{len(stuck_deals)} deals stuck in pipeline for 14+ days",
                "impact": f"${total_at_risk:,.0f} at risk",
                "confidence": 87,
                "data": {"deals": stuck_deals[:5]}  # Top 5 for display
            })
        
        # Pipeline health insight
        health_score = analysis_results.get("pipeline_health", 0)
        if health_score < 70:
            insights.append({
                "type": "risk",
                "priority": "high",
                "message": f"Pipeline health declining at {health_score}%",
                "impact": "Revenue forecast at risk",
                "confidence": 82,
                "data": {"health_score": health_score}
            })
        elif health_score > 85:
            insights.append({
                "type": "opportunity",
                "priority": "medium",
                "message": f"Strong pipeline health at {health_score}%",
                "impact": "Good position for growth",
                "confidence": 85,
                "data": {"health_score": health_score}
            })
        
        # Forecast insight
        forecast = analysis_results.get("forecast", {})
        if forecast:
            next_month = forecast.get("next_month", 0)
            insights.append({
                "type": "trend",
                "priority": "medium",
                "message": f"Revenue forecast: ${next_month:,.0f} next month",
                "impact": "Planning and resource allocation",
                "confidence": 75,
                "data": forecast
            })
        
        return insights
    
    def recommend_actions(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate action recommendations."""
        recommendations = []
        
        for insight in insights:
            if insight["type"] == "risk" and "stuck" in insight["message"].lower():
                # Recommend follow-ups for stuck deals
                stuck_deals = insight.get("data", {}).get("deals", [])
                if stuck_deals:
                    recommendations.append({
                        "action": "follow_up_deals",
                        "title": "Follow up on stuck deals",
                        "priority": "urgent",
                        "expected_impact": f"${insight['impact']} potential recovery",
                        "effort": "15 minutes",
                        "success_probability": 68,
                        "template": {
                            "type": "email",
                            "recipients": [deal.get("id") for deal in stuck_deals[:5]],
                            "subject": "Following up on our proposal",
                            "body": "Template for personalized follow-up"
                        }
                    })
            
            if insight["type"] == "risk" and "health" in insight["message"].lower():
                # Recommend pipeline review
                recommendations.append({
                    "action": "pipeline_review",
                    "title": "Conduct pipeline health review",
                    "priority": "high",
                    "expected_impact": "Identify and address bottlenecks",
                    "effort": "1 hour",
                    "success_probability": 75,
                    "template": None
                })
        
        return recommendations
    
    # Helper methods
    def _find_deals_data(self, data: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Find deals dataframe from available data."""
        for key, df in data.items():
            if 'deal' in key.lower() or 'Deal' in str(df.columns):
                return df
        return None
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Find column by checking multiple possible names."""
        for col in df.columns:
            col_lower = col.lower()
            if any(name.lower() in col_lower for name in possible_names):
                return col
        return None
    
    def _identify_stuck_deals(self, df: pd.DataFrame, stage_col: str, date_col: str, amount_col: Optional[str]) -> List[Dict[str, Any]]:
        """Identify deals stuck in stages for too long."""
        stuck_deals = []
        
        try:
            # Convert date column to datetime
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            current_date = datetime.now()
            
            # Look for deals in proposal/negotiation stages
            proposal_stages = df[stage_col].str.contains('Proposal|Negotiation|Contact', case=False, na=False)
            
            for idx, row in df[proposal_stages].iterrows():
                try:
                    days_since_update = (current_date - row[date_col]).days
                    if days_since_update > 14:  # Stuck for more than 14 days
                        stuck_deals.append({
                            "id": str(idx),
                            "stage": row[stage_col],
                            "days_stuck": days_since_update,
                            "amount": float(row[amount_col]) if amount_col and pd.notna(row[amount_col]) else 0
                        })
                except:
                    continue
            
            # Sort by amount descending
            stuck_deals.sort(key=lambda x: x["amount"], reverse=True)
        except Exception as e:
            print(f"Error identifying stuck deals: {e}")
        
        return stuck_deals
    
    def _calculate_pipeline_health(self, df: pd.DataFrame, stage_col: Optional[str], stuck_deals: List[Dict]) -> int:
        """Calculate overall pipeline health score."""
        score = 100
        
        # Deduct for stuck deals
        if len(stuck_deals) > 0:
            score -= min(len(stuck_deals) * 3, 30)  # Max 30 point deduction
        
        # Deduct for low activity
        if len(df) < 20:
            score -= 15
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))
    
    def _forecast_revenue(self, df: pd.DataFrame, amount_col: str, stage_col: Optional[str]) -> Dict[str, float]:
        """Simple revenue forecast."""
        try:
            # Calculate average for next month (very simple model)
            avg_deal = self.safe_mean(df[amount_col])
            total_pipeline = self.safe_sum(df[amount_col])
            
            # Assume 30% conversion rate
            conversion_rate = 0.30
            
            return {
                "next_month": total_pipeline * conversion_rate / 3,  # Rough monthly estimate
                "next_quarter": total_pipeline * conversion_rate,
                "confidence": 75
            }
        except:
            return {}


