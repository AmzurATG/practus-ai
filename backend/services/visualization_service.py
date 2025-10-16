"""
Enhanced Visualization Service with Caching and Real Data Analysis
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sklearn.linear_model import LinearRegression
import json
import google.generativeai as genai
import os

class VisualizationCache:
    """Simple in-memory cache for visualization data"""
    def __init__(self):
        self._cache = {}
        self._cache_times = {}
        self.ttl = 300  # 5 minutes
    
    def get(self, key: str) -> Optional[Dict]:
        if key in self._cache:
            if datetime.now().timestamp() - self._cache_times[key] < self.ttl:
                return self._cache[key]
            else:
                # Expired
                del self._cache[key]
                del self._cache_times[key]
        return None
    
    def set(self, key: str, value: Dict):
        self._cache[key] = value
        self._cache_times[key] = datetime.now().timestamp()
    
    def clear(self):
        self._cache.clear()
        self._cache_times.clear()

# Global cache instance
viz_cache = VisualizationCache()


class VisualizationService:
    """Service for generating problem-specific visualizations"""
    
    def __init__(self):
        self.cache = viz_cache
        self.gemini_model = None
        self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini model for insights generation"""
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key and api_key != 'your-gemini-api-key-here':
                genai.configure(api_key=api_key)
                # Try to get the best available model
                try:
                    self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                except:
                    try:
                        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                    except:
                        self.gemini_model = None
        except Exception as e:
            print(f"Gemini initialization failed: {e}")
            self.gemini_model = None
    
    def _generate_insights(self, problem_name: str, summary: Dict, visualizations: List[Dict]) -> List[str]:
        """Generate AI insights for the visualizations"""
        if not self.gemini_model:
            return [
                f"{problem_name} analysis shows {len(visualizations)} key metrics",
                "Review the visualizations above for detailed patterns",
                "Click on any chart to see detailed data points"
            ]
        
        try:
            prompt = f"""As a business intelligence expert, analyze this {problem_name} data and provide 3 concise, actionable insights.

Summary Metrics:
{json.dumps(summary, indent=2)}

Visualization Titles:
{[v.get('title', 'Untitled') for v in visualizations]}

Provide exactly 3 insights in this format (plain text, one per line):
1. [Insight about the data trend or pattern]
2. [Actionable recommendation based on the data]
3. [Risk or opportunity identified]

Keep each insight under 100 characters. Be specific with numbers from the summary."""

            response = self.gemini_model.generate_content(prompt)
            insights_text = response.text.strip()
            
            # Parse insights
            insights = []
            for line in insights_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Clean up the line
                    clean_line = line.lstrip('0123456789.-•) ').strip()
                    if clean_line:
                        insights.append(clean_line)
            
            return insights[:3] if insights else [
                f"{problem_name} data processed successfully",
                "Multiple visualization perspectives available",
                "Explore charts for detailed analysis"
            ]
        except Exception as e:
            print(f"Insight generation error: {e}")
            return [
                f"{problem_name} analysis complete",
                f"{len(visualizations)} visualizations generated",
                "Review the data patterns above"
            ]
    
    def _format_currency(self, value: float) -> str:
        """Format currency values for display"""
        if value >= 1_000_000:
            return f"${value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"${value/1_000:.0f}K"
        else:
            return f"${value:.0f}"
    
    def _format_date_axis(self, dates: pd.Series) -> List[str]:
        """Format dates for readable x-axis"""
        return [pd.to_datetime(d).strftime('%b %Y') if pd.notna(d) else '' for d in dates]
    
    def _truncate_labels(self, labels: List[str], max_len: int = 20) -> List[str]:
        """Truncate long labels for readability"""
        return [label[:max_len] + '...' if len(str(label)) > max_len else str(label) for label in labels]
    
    def get_visualizations(self, problem_id: int, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """Main entry point for getting visualizations"""
        cache_key = f"viz_problem_{problem_id}_{hash(frozenset(data_dict.keys()))}"
        
        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # Generate based on problem
        if problem_id == 1:
            result = self._revenue_forecasting(data_dict)
        elif problem_id == 2:
            result = self._deal_dropoff(data_dict)
        elif problem_id == 3:
            result = self._effort_budget(data_dict)
        elif problem_id == 4:
            result = self._client_retention(data_dict)
        elif problem_id == 5:
            result = self._hiring_decisions(data_dict)
        elif problem_id == 6:
            result = self._automation_opportunities(data_dict)
        else:
            result = {"error": "Invalid problem ID"}
        
        # Cache the result
        self.cache.set(cache_key, result)
        return result
    
    def _revenue_forecasting(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """Problem 1: Revenue Forecasting - Clear, actionable visualizations"""
        deals_df = self._find_deals_data(data_dict)
        if deals_df is None:
            return {"error": "Deals data not found", "visualizations": []}
        
        # Clean data
        deals_df['Deal Amount'] = pd.to_numeric(deals_df['Deal Amount'], errors='coerce')
        deals_df['Deal_Closing_Date'] = pd.to_datetime(deals_df['Deal_Closing_Date'], errors='coerce')
        
        # Filter to meaningful deals (> 0 amount)
        deals_df = deals_df[deals_df['Deal Amount'] > 0].copy()
        
        visualizations = []
        
        # 1. Monthly Revenue Trend (Last 12 months)
        deals_df['Month'] = deals_df['Deal_Closing_Date'].dt.to_period('M')
        monthly_revenue = deals_df.groupby('Month')['Deal Amount'].sum().sort_index().tail(12)
        
        if len(monthly_revenue) > 0:
            visualizations.append({
                "type": "line",
                "title": "Monthly Revenue Trend (Last 12 Months)",
                "data": {
                    "x": [str(m) for m in monthly_revenue.index],
                    "y": monthly_revenue.values.tolist(),
                    "labels": [self._format_currency(v) for v in monthly_revenue.values]
                }
            })
        
        # 2. Pipeline Value by Stage (Current Active Deals)
        active_deals = deals_df[deals_df['Stage'].notna()].copy()
        stage_value = active_deals.groupby('Stage')['Deal Amount'].sum().sort_values(ascending=False).head(8)
        
        if len(stage_value) > 0:
            visualizations.append({
                "type": "bar",
                "title": "Pipeline Value by Sales Stage (Top 8)",
                "data": {
                    "x": self._truncate_labels(stage_value.index.tolist(), 25),
                    "y": stage_value.values.tolist(),
                    "labels": [self._format_currency(v) for v in stage_value.values]
                }
            })
        
        # 3. Deal Size Categories
        if len(deals_df) > 0:
            bins = [0, 10000, 50000, 100000, 500000, float('inf')]
            labels = ['< $10K', '$10K-$50K', '$50K-$100K', '$100K-$500K', '> $500K']
            deals_df['Size_Category'] = pd.cut(deals_df['Deal Amount'], bins=bins, labels=labels)
            category_counts = deals_df['Size_Category'].value_counts().sort_index()
            
            visualizations.append({
                "type": "pie",
                "title": "Deal Distribution by Size",
                "data": {
                    "labels": category_counts.index.tolist(),
                    "values": category_counts.values.tolist()
                }
            })
        
        # 4. Win Rate by Probability Range
        deals_df['Probability'] = pd.to_numeric(deals_df['Probability'], errors='coerce')
        prob_bins = [0, 25, 50, 75, 100]
        prob_labels = ['0-25%', '25-50%', '50-75%', '75-100%']
        deals_df['Prob_Range'] = pd.cut(deals_df['Probability'], bins=prob_bins, labels=prob_labels)
        prob_analysis = deals_df.groupby('Prob_Range', observed=True).agg({
            'Deal Amount': ['sum', 'count']
        }).round(0)
        
        if len(prob_analysis) > 0:
            visualizations.append({
                "type": "bar",
                "title": "Deal Count by Probability Range",
                "data": {
                    "x": [str(idx) for idx in prob_analysis.index],
                    "y": prob_analysis[('Deal Amount', 'count')].values.tolist()
                }
            })
        
        # 5. Revenue Forecast (3-month projection using linear regression)
        if len(monthly_revenue) >= 3:
            x = np.arange(len(monthly_revenue)).reshape(-1, 1)
            y = monthly_revenue.values
            
            model = LinearRegression()
            model.fit(x, y)
            
            # Predict next 3 months
            future_x = np.arange(len(monthly_revenue), len(monthly_revenue) + 3).reshape(-1, 1)
            future_y = model.predict(future_x)
            
            last_month = monthly_revenue.index[-1]
            future_months = [(last_month + i).strftime('%b %Y') for i in range(1, 4)]
            
            visualizations.append({
                "type": "line",
                "title": "3-Month Revenue Forecast",
                "data": {
                    "x": [str(m) for m in monthly_revenue.index[-6:]] + future_months,
                    "y": monthly_revenue.values[-6:].tolist() + future_y.tolist(),
                    "forecast_start_index": 6
                }
            })
        
        summary = {
            "total_pipeline_value": float(deals_df['Deal Amount'].sum()),
            "total_deals": int(len(deals_df)),
            "avg_deal_size": float(deals_df['Deal Amount'].mean())
        }
        
        insights = self._generate_insights("Revenue Forecasting", summary, visualizations)
        
        return {
            "problem": "Revenue Forecasting",
            "visualizations": visualizations,
            "summary": summary,
            "insights": insights
        }
    
    def _deal_dropoff(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """Problem 2: Deal Drop-off Analysis - Real conversion metrics"""
        stage_df = self._find_stage_data(data_dict)
        if stage_df is None:
            return {"error": "Stage history data not found", "visualizations": []}
        
        visualizations = []
        
        # 1. Sales Funnel (Top stages only)
        stage_counts = stage_df['Stage'].value_counts().head(8)
        
        visualizations.append({
            "type": "funnel",
            "title": "Sales Funnel - Active Deals by Stage",
            "data": {
                "stages": self._truncate_labels(stage_counts.index.tolist(), 30),
                "counts": stage_counts.values.tolist()
            }
        })
        
        # 2. Average Time in Each Stage
        stage_df['Stage Duration Days'] = pd.to_numeric(stage_df['Stage Duration Days'], errors='coerce')
        avg_duration = stage_df.groupby('Stage')['Stage Duration Days'].mean().dropna().sort_values(ascending=False).head(10)
        
        if len(avg_duration) > 0:
            visualizations.append({
                "type": "bar",
                "title": "Average Days Spent in Each Stage (Top 10)",
                "data": {
                    "x": self._truncate_labels(avg_duration.index.tolist(), 25),
                    "y": avg_duration.values.round(1).tolist()
                }
            })
        
        # 3. REAL Stage Conversion Analysis
        # Track actual stage transitions per deal
        stage_df = stage_df.sort_values(['Deal ID', 'Modified_Time'])
        stage_transitions = {}
        
        for deal_id, group in stage_df.groupby('Deal ID'):
            stages = group['Stage'].tolist()
            for i in range(len(stages) - 1):
                from_stage = stages[i]
                to_stage = stages[i + 1]
                key = f"{from_stage} → {to_stage}"
                stage_transitions[key] = stage_transitions.get(key, 0) + 1
        
        # Top 10 transitions
        top_transitions = sorted(stage_transitions.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if top_transitions:
            visualizations.append({
                "type": "bar",
                "title": "Top 10 Stage Transitions (Actual Data)",
                "data": {
                    "x": self._truncate_labels([t[0] for t in top_transitions], 30),
                    "y": [t[1] for t in top_transitions]
                }
            })
        
        # 4. Deal Drop-off by Stage Group
        if 'Stage Group' in stage_df.columns:
            stage_group_counts = stage_df['Stage Group'].value_counts()
            visualizations.append({
                "type": "pie",
                "title": "Deal Distribution by Stage Group",
                "data": {
                    "labels": stage_group_counts.index.tolist(),
                    "values": stage_group_counts.values.tolist()
                }
            })
        
        # 5. Probability Progression
        stage_df['Probability'] = pd.to_numeric(stage_df['Probability'], errors='coerce')
        prob_by_stage = stage_df.groupby('Stage')['Probability'].mean().dropna().sort_values(ascending=False).head(10)
        
        if len(prob_by_stage) > 0:
            visualizations.append({
                "type": "bar",
                "title": "Average Win Probability by Stage",
                "data": {
                    "x": self._truncate_labels(prob_by_stage.index.tolist(), 25),
                    "y": prob_by_stage.values.round(1).tolist()
                }
            })
        
        summary = {
            "total_stage_records": int(len(stage_df)),
            "unique_deals": int(stage_df['Deal ID'].nunique()),
            "avg_stage_duration": float(stage_df['Stage Duration Days'].mean()) if 'Stage Duration Days' in stage_df.columns else 0
        }
        
        insights = self._generate_insights("Deal Drop-off Analysis", summary, visualizations)
        
        return {
            "problem": "Deal Drop-off Analysis",
            "visualizations": visualizations,
            "summary": summary,
            "insights": insights
        }
    
    def _effort_budget(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """Problem 3: Effort vs Budget Tracking - Resource utilization"""
        whizible_df = self._find_whizible_data(data_dict)
        if whizible_df is None:
            return {"error": "Timesheet data not found", "visualizations": []}
        
        visualizations = []
        
        # Clean data
        whizible_df['Hours(Filled)'] = pd.to_numeric(whizible_df['Hours(Filled)'], errors='coerce')
        whizible_df['TimesheetDate'] = pd.to_datetime(whizible_df['TimesheetDate'], errors='coerce')
        
        # 1. Top 10 Projects by Hours
        project_hours = whizible_df.groupby('Project name')['Hours(Filled)'].sum().sort_values(ascending=False).head(10)
        
        visualizations.append({
            "type": "bar",
            "title": "Top 10 Projects by Total Hours",
            "data": {
                "x": self._truncate_labels(project_hours.index.tolist(), 20),
                "y": project_hours.values.round(1).tolist()
            }
        })
        
        # 2. Weekly Hours Trend (Last 8 weeks)
        whizible_df['Week'] = whizible_df['TimesheetDate'].dt.to_period('W')
        weekly_hours = whizible_df.groupby('Week')['Hours(Filled)'].sum().sort_index().tail(8)
        
        if len(weekly_hours) > 0:
            visualizations.append({
                "type": "line",
                "title": "Weekly Hours Trend (Last 8 Weeks)",
                "data": {
                    "x": [str(w) for w in weekly_hours.index],
                    "y": weekly_hours.values.round(1).tolist()
                }
            })
        
        # 3. Hours by Task Type
        task_hours = whizible_df.groupby('TaskType')['Hours(Filled)'].sum().sort_values(ascending=False)
        
        visualizations.append({
            "type": "pie",
            "title": "Hours Distribution by Task Type",
            "data": {
                "labels": task_hours.index.tolist(),
                "values": task_hours.values.round(1).tolist()
            }
        })
        
        # 4. Top 15 Resources by Utilization
        resource_hours = whizible_df.groupby('EmployeeCode')['Hours(Filled)'].sum().sort_values(ascending=False).head(15)
        
        visualizations.append({
            "type": "bar",
            "title": "Top 15 Resources by Total Hours",
            "data": {
                "x": resource_hours.index.tolist(),
                "y": resource_hours.values.round(1).tolist()
            }
        })
        
        # 5. Business Unit Distribution
        bu_hours = whizible_df.groupby('BusinessGroup')['Hours(Filled)'].sum()
        
        visualizations.append({
            "type": "pie",
            "title": "Hours by Business Unit",
            "data": {
                "labels": bu_hours.index.tolist(),
                "values": bu_hours.values.round(1).tolist()
            }
        })
        
        summary = {
            "total_hours": float(whizible_df['Hours(Filled)'].sum()),
            "avg_hours_per_day": float(whizible_df.groupby('TimesheetDate')['Hours(Filled)'].sum().mean()),
            "active_resources": int(whizible_df['EmployeeCode'].nunique())
        }
        
        insights = self._generate_insights("Effort vs Budget Tracking", summary, visualizations)
        
        return {
            "problem": "Effort vs Budget Tracking",
            "visualizations": visualizations,
            "summary": summary,
            "insights": insights
        }
    
    def _client_retention(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """Problem 4: Client Retention Insights"""
        deals_df = self._find_deals_data(data_dict)
        if deals_df is None:
            return {"error": "Deals data not found", "visualizations": []}
        
        deals_df['Deal Amount'] = pd.to_numeric(deals_df['Deal Amount'], errors='coerce')
        deals_df = deals_df[deals_df['Deal Amount'] > 0].copy()
        
        visualizations = []
        
        # 1. Top 15 Clients by Revenue
        client_revenue = deals_df.groupby('Project name')['Deal Amount'].sum().sort_values(ascending=False).head(15)
        
        visualizations.append({
            "type": "bar",
            "title": "Top 15 Clients by Total Revenue",
            "data": {
                "x": self._truncate_labels(client_revenue.index.tolist(), 20),
                "y": client_revenue.values.tolist(),
                "labels": [self._format_currency(v) for v in client_revenue.values]
            }
        })
        
        # 2. Revenue by Industry
        industry_revenue = deals_df.groupby('Industry_Type')['Deal Amount'].sum().sort_values(ascending=False).head(8)
        
        visualizations.append({
            "type": "pie",
            "title": "Revenue by Industry (Top 8)",
            "data": {
                "labels": self._truncate_labels(industry_revenue.index.tolist(), 20),
                "values": industry_revenue.values.tolist()
            }
        })
        
        # 3. Client Type Distribution
        client_type_revenue = deals_df.groupby('Client_Type')['Deal Amount'].sum().sort_values(ascending=False)
        
        visualizations.append({
            "type": "bar",
            "title": "Revenue by Client Type",
            "data": {
                "x": client_type_revenue.index.tolist(),
                "y": client_revenue.values.tolist(),
                "labels": [self._format_currency(v) for v in client_type_revenue.values]
            }
        })
        
        # 4. Geographic Distribution
        country_deals = deals_df.groupby('Country').size().sort_values(ascending=False).head(10)
        
        visualizations.append({
            "type": "bar",
            "title": "Deal Count by Country (Top 10)",
            "data": {
                "x": country_deals.index.tolist(),
                "y": country_deals.values.tolist()
            }
        })
        
        # 5. Engagement Tenure Analysis
        deals_df['Engagement_Tenure_months'] = pd.to_numeric(deals_df['Engagement_Tenure_months'], errors='coerce')
        tenure_valid = deals_df[deals_df['Engagement_Tenure_months'] > 0]['Engagement_Tenure_months']
        
        if len(tenure_valid) > 20:
            bins = [0, 3, 6, 12, 24, 48, float('inf')]
            labels = ['0-3m', '3-6m', '6-12m', '1-2y', '2-4y', '4y+']
            tenure_cats = pd.cut(tenure_valid, bins=bins, labels=labels)
            tenure_dist = tenure_cats.value_counts().sort_index()
            
            visualizations.append({
                "type": "bar",
                "title": "Client Engagement Tenure Distribution",
                "data": {
                    "x": tenure_dist.index.tolist(),
                    "y": tenure_dist.values.tolist()
                }
            })
        
        summary = {
            "total_clients": int(deals_df['Project name'].nunique()),
            "total_revenue": float(deals_df['Deal Amount'].sum()),
            "avg_revenue_per_client": float(deals_df.groupby('Project name')['Deal Amount'].sum().mean())
        }
        
        insights = self._generate_insights("Client Retention Insights", summary, visualizations)
        
        return {
            "problem": "Client Retention Insights",
            "visualizations": visualizations,
            "summary": summary,
            "insights": insights
        }
    
    def _hiring_decisions(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """Problem 5: Data-Driven Hiring Decisions"""
        whizible_df = self._find_whizible_data(data_dict)
        skill_df = self._find_skill_data(data_dict)
        
        if whizible_df is None:
            return {"error": "Resource data not found", "visualizations": []}
        
        visualizations = []
        
        # 1. Resource Utilization Trend
        whizible_df['Hours(Filled)'] = pd.to_numeric(whizible_df['Hours(Filled)'], errors='coerce')
        whizible_df['TimesheetDate'] = pd.to_datetime(whizible_df['TimesheetDate'], errors='coerce')
        
        monthly_utilization = whizible_df.groupby(whizible_df['TimesheetDate'].dt.to_period('M'))['Hours(Filled)'].sum().tail(12)
        
        if len(monthly_utilization) > 0:
            visualizations.append({
                "type": "line",
                "title": "Monthly Resource Hours (Last 12 Months)",
                "data": {
                    "x": [str(m) for m in monthly_utilization.index],
                    "y": monthly_utilization.values.round(1).tolist()
                }
            })
        
        # 2. Top Resources by Hours
        top_resources = whizible_df.groupby('EmployeeCode')['Hours(Filled)'].sum().sort_values(ascending=False).head(20)
        
        visualizations.append({
            "type": "bar",
            "title": "Top 20 Resources by Total Hours",
            "data": {
                "x": top_resources.index.tolist(),
                "y": top_resources.values.round(1).tolist()
            }
        })
        
        # 3. Skill Gaps (if skill data available)
        if skill_df is not None and 'Reply' in skill_df.columns:
            skill_gaps = skill_df[skill_df['Reply'] == 'Yet to Acquire']
            if len(skill_gaps) > 0:
                gap_analysis = skill_gaps.groupby('Role').size().sort_values(ascending=False).head(10)
                
                visualizations.append({
                    "type": "bar",
                    "title": "Top 10 Roles with Skill Gaps",
                    "data": {
                        "x": self._truncate_labels(gap_analysis.index.tolist(), 25),
                        "y": gap_analysis.values.tolist()
                    }
                })
        
        # 4. Business Unit Capacity
        bu_capacity = whizible_df.groupby('BusinessGroup')['EmployeeCode'].nunique()
        
        visualizations.append({
            "type": "pie",
            "title": "Resource Count by Business Unit",
            "data": {
                "labels": bu_capacity.index.tolist(),
                "values": bu_capacity.values.tolist()
            }
        })
        
        # 5. Project Type Distribution
        project_type_hours = whizible_df.groupby('Type of project')['Hours(Filled)'].sum()
        
        visualizations.append({
            "type": "pie",
            "title": "Hours by Project Type",
            "data": {
                "labels": project_type_hours.index.tolist(),
                "values": project_type_hours.values.round(1).tolist()
            }
        })
        
        summary = {
            "total_resources": int(whizible_df['EmployeeCode'].nunique()),
            "total_hours": float(whizible_df['Hours(Filled)'].sum()),
            "avg_hours_per_resource": float(whizible_df.groupby('EmployeeCode')['Hours(Filled)'].sum().mean())
        }
        
        insights = self._generate_insights("Data-Driven Hiring Decisions", summary, visualizations)
        
        return {
            "problem": "Data-Driven Hiring Decisions",
            "visualizations": visualizations,
            "summary": summary,
            "insights": insights
        }
    
    def _automation_opportunities(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """Problem 6: Delivery Operations Automation"""
        whizible_df = self._find_whizible_data(data_dict)
        if whizible_df is None:
            return {"error": "Operations data not found", "visualizations": []}
        
        visualizations = []
        
        # 1. Most Frequent Tasks (Automation Candidates)
        task_frequency = whizible_df['TaskName'].value_counts().head(15)
        
        visualizations.append({
            "type": "bar",
            "title": "Top 15 Most Frequent Tasks (Automation Potential)",
            "data": {
                "x": self._truncate_labels(task_frequency.index.tolist(), 25),
                "y": task_frequency.values.tolist()
            }
        })
        
        # 2. Idle Time Analysis
        whizible_df['Hours(Filled)'] = pd.to_numeric(whizible_df['Hours(Filled)'], errors='coerce')
        idle_time = whizible_df[whizible_df['TaskType'] == 'Idle Time']
        
        if len(idle_time) > 0:
            idle_by_resource = idle_time.groupby('EmployeeCode')['Hours(Filled)'].sum().sort_values(ascending=False).head(15)
            
            visualizations.append({
                "type": "bar",
                "title": "Top 15 Resources with Idle Time",
                "data": {
                    "x": idle_by_resource.index.tolist(),
                    "y": idle_by_resource.values.round(1).tolist()
                }
            })
        
        # 3. Task Type Efficiency
        task_type_analysis = whizible_df.groupby('TaskType')['Hours(Filled)'].agg(['sum', 'count', 'mean']).round(1)
        task_type_analysis = task_type_analysis.sort_values('sum', ascending=False).head(10)
        
        visualizations.append({
            "type": "bar",
            "title": "Total Hours by Task Type (Top 10)",
            "data": {
                "x": self._truncate_labels(task_type_analysis.index.tolist(), 25),
                "y": task_type_analysis['sum'].values.tolist()
            }
        })
        
        # 4. Repetitive Task Hours
        task_hours = whizible_df.groupby('TaskName')['Hours(Filled)'].sum().sort_values(ascending=False).head(10)
        
        visualizations.append({
            "type": "bar",
            "title": "Top 10 Tasks by Total Hours (ROI Opportunity)",
            "data": {
                "x": self._truncate_labels(task_hours.index.tolist(), 25),
                "y": task_hours.values.round(1).tolist()
            }
        })
        
        # 5. Task Type Distribution
        task_dist = whizible_df.groupby('TaskType').size()
        
        visualizations.append({
            "type": "pie",
            "title": "Task Distribution by Type",
            "data": {
                "labels": task_dist.index.tolist(),
                "values": task_dist.values.tolist()
            }
        })
        
        summary = {
            "total_tasks": int(len(whizible_df)),
            "unique_task_types": int(whizible_df['TaskType'].nunique()),
            "total_idle_hours": float(idle_time['Hours(Filled)'].sum()) if len(idle_time) > 0 else 0
        }
        
        insights = self._generate_insights("Delivery Operations Automation", summary, visualizations)
        
        return {
            "problem": "Delivery Operations Automation",
            "visualizations": visualizations,
            "summary": summary,
            "insights": insights
        }
    
    # Helper methods to find data
    def _find_deals_data(self, data_dict: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        for name, df in data_dict.items():
            if 'deal' in name.lower() and 'Deal Amount' in df.columns:
                return df.copy()
        return None
    
    def _find_stage_data(self, data_dict: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        for name, df in data_dict.items():
            if 'stage' in name.lower() and 'history' in name.lower():
                return df.copy()
        return None
    
    def _find_whizible_data(self, data_dict: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        for name, df in data_dict.items():
            if 'whizible' in name.lower():
                return df.copy()
        return None
    
    def _find_skill_data(self, data_dict: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        for name, df in data_dict.items():
            if 'skill' in name.lower():
                return df.copy()
        return None

