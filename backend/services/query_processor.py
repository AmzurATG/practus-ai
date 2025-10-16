import google.generativeai as genai
from typing import Dict, Any, Optional
import pandas as pd
import json


class QueryProcessor:
    """
    Processes natural language queries using Gemini AI.
    Converts user questions into structured responses with data and visualizations.
    """
    
    def __init__(self, gemini_model: str):
        self.model_name = gemini_model
        self.model = genai.GenerativeModel(gemini_model)
    
    def process_query(
        self,
        query: str,
        agent_response: Dict[str, Any],
        data_summary: Optional[Dict[str, Any]] = None,
        cache_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a natural language query and generate structured response.
        
        Args:
            query: User's natural language query
            agent_response: Analysis from the agent
            data_summary: Optional summary of available data
            cache_data: Optional cached insights from all problems
            
        Returns:
            Structured response with answer, data, and visualizations
        """
        # Build context for Gemini
        context = self._build_context(agent_response, data_summary, cache_data)
        
        # Create prompt
        prompt = f"""You are a senior business intelligence consultant at Practus, a leading consulting and staffing company. You help executives make data-driven decisions about revenue forecasting, client retention, hiring, and operational efficiency.

BUSINESS CONTEXT:
- Practus is a consulting and staffing company
- We work with clients across various industries
- Our services include project delivery, resource staffing, and business consulting
- We track deals, projects, client relationships, and team performance

USER QUERY: {query}

AVAILABLE DATA CONTEXT:
{context}

INSTRUCTIONS:
1. Provide a professional, executive-level response that demonstrates deep business insight
2. Use specific numbers, percentages, and metrics from the data
3. Highlight business impact and strategic implications
4. Be concise but comprehensive (2-4 sentences)
5. Suggest 2-3 strategic follow-up questions that would help with decision-making
6. Maintain a confident, professional tone suitable for client presentations

Return response in this JSON format:
{{
  "answer": "Your professional business analysis here with specific metrics",
  "key_metrics": {{"metric_name": value, ...}},
  "suggested_followups": ["Strategic question 1?", "Strategic question 2?", "Strategic question 3?"]
}}

Return ONLY the JSON, no other text."""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean JSON response
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            result = json.loads(response_text)
            return result
            
        except Exception as e:
            print(f"Error processing query with Gemini: {e}")
            # Fallback response
            return {
                "answer": f"Based on the analysis: {agent_response.get('insights', [{}])[0].get('message', 'Analysis complete')}",
                "key_metrics": {},
                "suggested_followups": [
                    "What should I focus on today?",
                    "Show me more details",
                    "What are the biggest risks?"
                ]
            }
    
    def detect_intent(self, query: str) -> str:
        """
        Detect the intent/category of a query.
        
        Args:
            query: User's question
            
        Returns:
            Intent category: pipeline_analysis, forecast, resource, performance, etc.
        """
        query_lower = query.lower()
        
        # Intent patterns
        if any(word in query_lower for word in ['stuck', 'stalled', 'delayed', 'pipeline', 'deals']):
            return "pipeline_analysis"
        
        if any(word in query_lower for word in ['forecast', 'predict', 'future', 'next month', 'next quarter']):
            return "forecast"
        
        if any(word in query_lower for word in ['resource', 'team', 'capacity', 'utilization', 'available']):
            return "resource"
        
        if any(word in query_lower for word in ['project', 'budget', 'overrun', 'performance']):
            return "performance"
        
        if any(word in query_lower for word in ['client', 'retention', 'churn', 'satisfaction']):
            return "client"
        
        return "general"
    
    def _build_context(self, agent_response: Dict[str, Any], data_summary: Optional[Dict[str, Any]], cache_data: Optional[Dict[str, Any]] = None) -> str:
        """Build context string for Gemini."""
        context_parts = []
        
        if data_summary:
            context_parts.append(f"Data Summary: {json.dumps(data_summary, indent=2)}")
        
        if cache_data:
            context_parts.append(f"Recent Analytics Insights: {json.dumps(cache_data, indent=2)}")
        
        context_parts.append(f"Current Analysis: {json.dumps(agent_response, indent=2)}")
        
        return "\n\n".join(context_parts)
    
    def generate_visualization_config(self, data: Dict[str, Any], chart_type: str = "table") -> Dict[str, Any]:
        """
        Generate Plotly configuration for visualization.
        
        Args:
            data: Data to visualize
            chart_type: Type of chart (table, bar, line, pie, funnel)
            
        Returns:
            Visualization configuration
        """
        config = {
            "type": chart_type,
            "data": data,
            "layout": {}
        }
        
        # Add chart-specific layout
        if chart_type == "bar":
            config["layout"] = {
                "xaxis": {"title": "Category"},
                "yaxis": {"title": "Value"},
                "margin": {"l": 50, "r": 50, "t": 50, "b": 50}
            }
        elif chart_type == "line":
            config["layout"] = {
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Value"},
                "margin": {"l": 50, "r": 50, "t": 50, "b": 50}
            }
        
        return config


