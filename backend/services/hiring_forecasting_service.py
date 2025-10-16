import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import os
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from services.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)

class HiringForecastingService:
    """Service for data-driven hiring decisions and cost forecasting."""
    
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        
    def load_whizible_data(self) -> pd.DataFrame:
        """Load Whizible timesheet data from local CSV file."""
        try:
            file_path = os.path.join(self.data_path, 'Whizible data.csv')
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} Whizible records")
            return df
        except Exception as e:
            logger.error(f"Error loading Whizible data: {str(e)}")
            raise Exception(f"Failed to load Whizible data: {str(e)}")
    
    def load_plotting_data(self) -> pd.DataFrame:
        """Load Plotting tool data from local CSV file."""
        try:
            file_path = os.path.join(self.data_path, 'Plotting tool data.csv')
            # Read with header in second row
            df = pd.read_csv(file_path, header=1)
            logger.info(f"Loaded {len(df)} Plotting tool records")
            return df
        except Exception as e:
            logger.error(f"Error loading Plotting tool data: {str(e)}")
            raise Exception(f"Failed to load Plotting tool data: {str(e)}")
    
    def preprocess_whizible_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess and clean Whizible timesheet data."""
        try:
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Convert date column
            df['TimesheetDate'] = pd.to_datetime(df['TimesheetDate'], errors='coerce')
            
            # Convert numeric columns
            df['Hours(Filled)'] = pd.to_numeric(df['Hours(Filled)'], errors='coerce').fillna(0)
            
            # Clean text columns
            text_columns = ['TaskName', 'TaskType', 'Project name', 'EmployeeCode', 'BusinessGroup']
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = df[col].replace('nan', 'Unknown')
            
            # Filter out invalid records
            df = df[df['TaskName'] != 'Unknown']
            df = df[df['Hours(Filled)'] > 0]
            
            # Add month column for time series analysis
            df['Month'] = df['TimesheetDate'].dt.to_period('M')
            
            logger.info(f"Preprocessed {len(df)} valid Whizible records")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing Whizible data: {str(e)}")
            raise Exception(f"Failed to preprocess Whizible data: {str(e)}")
    
    def preprocess_plotting_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess and clean Plotting tool data."""
        try:
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Convert numeric columns
            numeric_columns = ['Resource Allocation', 'Budgeted Hours', 'Actual Hours', 'Cost']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Clean text columns
            text_columns = ['Project name', 'Employee Name', 'Role', 'Skill Level']
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = df[col].replace('nan', 'Unknown')
            
            # Filter out invalid records
            df = df[df['Project name'] != 'Unknown']
            
            logger.info(f"Preprocessed {len(df)} valid Plotting tool records")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing Plotting tool data: {str(e)}")
            raise Exception(f"Failed to preprocess Plotting tool data: {str(e)}")
    
    def analyze_workload_trends(self, whizible_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze workload trends and capacity utilization."""
        try:
            # Monthly workload analysis
            monthly_workload = whizible_df.groupby('Month').agg({
                'Hours(Filled)': 'sum',
                'EmployeeCode': 'nunique',
                'Project name': 'nunique'
            }).reset_index()
            
            monthly_workload.columns = ['Month', 'Total_Hours', 'Unique_Employees', 'Unique_Projects']
            monthly_workload['Avg_Hours_Per_Employee'] = monthly_workload['Total_Hours'] / monthly_workload['Unique_Employees']
            monthly_workload['Avg_Hours_Per_Project'] = monthly_workload['Total_Hours'] / monthly_workload['Unique_Projects']
            
            # Calculate trends
            if len(monthly_workload) >= 2:
                hours_trend = (monthly_workload['Total_Hours'].iloc[-1] - monthly_workload['Total_Hours'].iloc[-2]) / monthly_workload['Total_Hours'].iloc[-2] * 100
                employee_trend = (monthly_workload['Unique_Employees'].iloc[-1] - monthly_workload['Unique_Employees'].iloc[-2]) / monthly_workload['Unique_Employees'].iloc[-2] * 100
            else:
                hours_trend = 0
                employee_trend = 0
            
            # Capacity utilization analysis
            avg_monthly_hours = monthly_workload['Total_Hours'].mean()
            avg_employees = monthly_workload['Unique_Employees'].mean()
            avg_hours_per_employee = avg_monthly_hours / avg_employees if avg_employees > 0 else 0
            
            # Assuming 160 hours per month per employee (40 hours/week * 4 weeks)
            capacity_utilization = (avg_hours_per_employee / 160) * 100 if avg_hours_per_employee > 0 else 0
            
            workload_analysis = {
                "monthly_workload": monthly_workload.to_dict('records'),
                "avg_monthly_hours": self._clean_float(avg_monthly_hours),
                "avg_employees": self._clean_float(avg_employees),
                "avg_hours_per_employee": self._clean_float(avg_hours_per_employee),
                "capacity_utilization": self._clean_float(capacity_utilization),
                "hours_trend": self._clean_float(hours_trend),
                "employee_trend": self._clean_float(employee_trend),
                "total_months_analyzed": len(monthly_workload)
            }
            
            logger.info(f"Analyzed workload trends for {len(monthly_workload)} months")
            return workload_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing workload trends: {str(e)}")
            return {"monthly_workload": [], "avg_monthly_hours": 0, "avg_employees": 0, "capacity_utilization": 0}
    
    def analyze_skill_demand(self, whizible_df: pd.DataFrame, plotting_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze skill demand and resource allocation patterns."""
        try:
            # Skill analysis from Whizible data
            task_skill_analysis = whizible_df.groupby('TaskType').agg({
                'Hours(Filled)': 'sum',
                'EmployeeCode': 'nunique',
                'Project name': 'nunique'
            }).reset_index()
            
            task_skill_analysis.columns = ['Skill_Type', 'Total_Hours', 'Unique_Employees', 'Unique_Projects']
            task_skill_analysis['Avg_Hours_Per_Employee'] = task_skill_analysis['Total_Hours'] / task_skill_analysis['Unique_Employees']
            task_skill_analysis = task_skill_analysis.sort_values('Total_Hours', ascending=False)
            
            # Resource allocation analysis from Plotting data
            if 'Role' in plotting_df.columns and 'Resource Allocation' in plotting_df.columns:
                role_allocation = plotting_df.groupby('Role').agg({
                    'Resource Allocation': 'mean',
                    'Budgeted Hours': 'sum',
                    'Actual Hours': 'sum',
                    'Cost': 'sum'
                }).reset_index()
                
                role_allocation['Utilization_Rate'] = (role_allocation['Actual Hours'] / role_allocation['Budgeted Hours'] * 100).fillna(0)
                role_allocation['Cost_Per_Hour'] = (role_allocation['Cost'] / role_allocation['Actual Hours']).fillna(0)
                role_allocation = role_allocation.sort_values('Cost', ascending=False)
            else:
                role_allocation = pd.DataFrame()
            
            # Identify skill gaps
            high_demand_skills = task_skill_analysis.head(5)['Skill_Type'].tolist()
            skill_gaps = []
            
            for skill in high_demand_skills:
                skill_data = task_skill_analysis[task_skill_analysis['Skill_Type'] == skill]
                if len(skill_data) > 0:
                    avg_hours = skill_data['Avg_Hours_Per_Employee'].iloc[0]
                    if avg_hours > 40:  # More than 40 hours per employee indicates high demand
                        skill_gaps.append({
                            'skill': skill,
                            'demand_level': 'High',
                            'avg_hours_per_employee': self._clean_float(avg_hours),
                            'total_hours': self._clean_float(skill_data['Total_Hours'].iloc[0])
                        })
            
            skill_analysis = {
                "task_skill_breakdown": self._clean_for_json(task_skill_analysis.to_dict('records')),
                "role_allocation": self._clean_for_json(role_allocation.to_dict('records')) if len(role_allocation) > 0 else [],
                "high_demand_skills": high_demand_skills,
                "skill_gaps": skill_gaps,
                "total_skill_types": len(task_skill_analysis)
            }
            
            logger.info(f"Analyzed {len(task_skill_analysis)} skill types and identified {len(skill_gaps)} skill gaps")
            return skill_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing skill demand: {str(e)}")
            return {"task_skill_breakdown": [], "role_allocation": [], "high_demand_skills": [], "skill_gaps": []}
    
    def forecast_hiring_needs(self, workload_analysis: Dict, skill_analysis: Dict) -> Dict[str, Any]:
        """Forecast hiring needs based on workload and skill analysis."""
        try:
            # Extract key metrics
            avg_monthly_hours = workload_analysis.get('avg_monthly_hours', 0)
            avg_employees = workload_analysis.get('avg_employees', 0)
            capacity_utilization = workload_analysis.get('capacity_utilization', 0)
            hours_trend = workload_analysis.get('hours_trend', 0)
            
            # Calculate hiring needs
            hiring_forecast = {}
            
            # Scenario 1: Maintain current capacity utilization
            if capacity_utilization > 85:  # High utilization
                hiring_forecast['scenario_1'] = {
                    'name': 'Maintain Current Utilization',
                    'additional_employees_needed': max(1, int(avg_employees * 0.1)),  # 10% increase
                    'timeline': 'Next 3 months',
                    'priority': 'High',
                    'reasoning': f'Current utilization at {capacity_utilization:.1f}% is high'
                }
            elif capacity_utilization > 70:  # Medium utilization
                hiring_forecast['scenario_1'] = {
                    'name': 'Maintain Current Utilization',
                    'additional_employees_needed': max(0, int(avg_employees * 0.05)),  # 5% increase
                    'timeline': 'Next 6 months',
                    'priority': 'Medium',
                    'reasoning': f'Current utilization at {capacity_utilization:.1f}% is moderate'
                }
            else:
                hiring_forecast['scenario_1'] = {
                    'name': 'Maintain Current Utilization',
                    'additional_employees_needed': 0,
                    'timeline': 'No immediate need',
                    'priority': 'Low',
                    'reasoning': f'Current utilization at {capacity_utilization:.1f}% is low'
                }
            
            # Scenario 2: Growth-based hiring
            if hours_trend > 10:  # Growing workload
                growth_factor = hours_trend / 100
                additional_employees = max(1, int(avg_employees * growth_factor))
                hiring_forecast['scenario_2'] = {
                    'name': 'Growth-Based Hiring',
                    'additional_employees_needed': additional_employees,
                    'timeline': 'Next 6 months',
                    'priority': 'High',
                    'reasoning': f'Workload growing at {hours_trend:.1f}% per month'
                }
            elif hours_trend > 5:
                growth_factor = hours_trend / 100
                additional_employees = max(1, int(avg_employees * growth_factor * 0.5))
                hiring_forecast['scenario_2'] = {
                    'name': 'Growth-Based Hiring',
                    'additional_employees_needed': additional_employees,
                    'timeline': 'Next 12 months',
                    'priority': 'Medium',
                    'reasoning': f'Moderate growth at {hours_trend:.1f}% per month'
                }
            else:
                hiring_forecast['scenario_2'] = {
                    'name': 'Growth-Based Hiring',
                    'additional_employees_needed': 0,
                    'timeline': 'No immediate need',
                    'priority': 'Low',
                    'reasoning': f'Stable workload with {hours_trend:.1f}% growth'
                }
            
            # Scenario 3: Skill-based hiring
            skill_gaps = skill_analysis.get('skill_gaps', [])
            high_demand_skills = skill_analysis.get('high_demand_skills', [])
            
            if len(skill_gaps) > 0:
                hiring_forecast['scenario_3'] = {
                    'name': 'Skill-Based Hiring',
                    'additional_employees_needed': len(skill_gaps),
                    'timeline': 'Next 3 months',
                    'priority': 'High',
                    'reasoning': f'Critical skill gaps in: {", ".join([gap["skill"] for gap in skill_gaps[:3]])}',
                    'target_skills': [gap['skill'] for gap in skill_gaps]
                }
            else:
                hiring_forecast['scenario_3'] = {
                    'name': 'Skill-Based Hiring',
                    'additional_employees_needed': 0,
                    'timeline': 'No immediate need',
                    'priority': 'Low',
                    'reasoning': 'No critical skill gaps identified'
                }
            
            # Overall recommendation
            total_needed = max(
                hiring_forecast['scenario_1']['additional_employees_needed'],
                hiring_forecast['scenario_2']['additional_employees_needed'],
                hiring_forecast['scenario_3']['additional_employees_needed']
            )
            
            if total_needed > 0:
                overall_priority = 'High' if total_needed >= 3 else 'Medium'
                overall_timeline = 'Next 3 months' if total_needed >= 3 else 'Next 6 months'
            else:
                overall_priority = 'Low'
                overall_timeline = 'No immediate need'
            
            hiring_forecast['overall_recommendation'] = {
                'total_employees_needed': total_needed,
                'priority': overall_priority,
                'timeline': overall_timeline,
                'confidence': 'High' if len(workload_analysis.get('monthly_workload', [])) >= 3 else 'Medium'
            }
            
            logger.info(f"Generated hiring forecast: {total_needed} employees needed")
            return hiring_forecast
            
        except Exception as e:
            logger.error(f"Error forecasting hiring needs: {str(e)}")
            return {"overall_recommendation": {"total_employees_needed": 0, "priority": "Low", "timeline": "No immediate need"}}
    
    def calculate_hiring_costs(self, hiring_forecast: Dict, plotting_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate hiring costs and ROI analysis."""
        try:
            total_needed = hiring_forecast.get('overall_recommendation', {}).get('total_employees_needed', 0)
            
            if total_needed == 0:
                return {
                    "total_hiring_cost": 0,
                    "cost_per_employee": 0,
                    "roi_analysis": "No hiring needed",
                    "cost_breakdown": []
                }
            
            # Calculate average cost per employee from plotting data
            if 'Cost' in plotting_df.columns and 'Employee Name' in plotting_df.columns:
                employee_costs = plotting_df.groupby('Employee Name')['Cost'].sum()
                avg_cost_per_employee = employee_costs.mean() if len(employee_costs) > 0 else 50000  # Default $50k
            else:
                avg_cost_per_employee = 50000  # Default $50k
            
            # Hiring cost breakdown
            recruitment_cost = 5000  # Average recruitment cost
            onboarding_cost = 3000   # Onboarding and training
            salary_cost = avg_cost_per_employee * 0.8  # 80% of total cost is salary
            benefits_cost = avg_cost_per_employee * 0.2  # 20% benefits
            
            cost_per_employee = recruitment_cost + onboarding_cost + salary_cost + benefits_cost
            total_hiring_cost = cost_per_employee * total_needed
            
            # ROI Analysis
            # Calculate potential revenue increase (assuming each employee generates 1.5x their cost in revenue)
            potential_revenue_increase = total_hiring_cost * 1.5
            roi_percentage = ((potential_revenue_increase - total_hiring_cost) / total_hiring_cost) * 100
            
            cost_breakdown = [
                {
                    'category': 'Recruitment',
                    'cost_per_employee': recruitment_cost,
                    'total_cost': recruitment_cost * total_needed,
                    'percentage': (recruitment_cost / cost_per_employee) * 100
                },
                {
                    'category': 'Onboarding',
                    'cost_per_employee': onboarding_cost,
                    'total_cost': onboarding_cost * total_needed,
                    'percentage': (onboarding_cost / cost_per_employee) * 100
                },
                {
                    'category': 'Salary (Annual)',
                    'cost_per_employee': salary_cost,
                    'total_cost': salary_cost * total_needed,
                    'percentage': (salary_cost / cost_per_employee) * 100
                },
                {
                    'category': 'Benefits',
                    'cost_per_employee': benefits_cost,
                    'total_cost': benefits_cost * total_needed,
                    'percentage': (benefits_cost / cost_per_employee) * 100
                }
            ]
            
            cost_analysis = {
                "total_hiring_cost": self._clean_float(total_hiring_cost),
                "cost_per_employee": self._clean_float(cost_per_employee),
                "potential_revenue_increase": self._clean_float(potential_revenue_increase),
                "roi_percentage": self._clean_float(roi_percentage),
                "payback_period_months": self._clean_float(12),  # Assuming 12 months payback
                "cost_breakdown": self._clean_for_json(cost_breakdown),
                "employees_to_hire": total_needed
            }
            
            logger.info(f"Calculated hiring costs: ${total_hiring_cost:,.0f} for {total_needed} employees")
            return cost_analysis
            
        except Exception as e:
            logger.error(f"Error calculating hiring costs: {str(e)}")
            return {"total_hiring_cost": 0, "cost_per_employee": 0, "roi_analysis": "Error in calculation"}
    
    def generate_hiring_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive hiring and cost forecasting analysis."""
        try:
            logger.info("Starting hiring forecasting analysis...")
            
            # Load and preprocess data
            whizible_df = self.load_whizible_data()
            plotting_df = self.load_plotting_data()
            
            whizible_clean = self.preprocess_whizible_data(whizible_df)
            plotting_clean = self.preprocess_plotting_data(plotting_df)
            
            # Perform analysis
            workload_analysis = self.analyze_workload_trends(whizible_clean)
            skill_analysis = self.analyze_skill_demand(whizible_clean, plotting_clean)
            hiring_forecast = self.forecast_hiring_needs(workload_analysis, skill_analysis)
            cost_analysis = self.calculate_hiring_costs(hiring_forecast, plotting_clean)
            
            # Generate summary metrics
            total_employees_needed = hiring_forecast.get('overall_recommendation', {}).get('total_employees_needed', 0)
            total_cost = cost_analysis.get('total_hiring_cost', 0)
            capacity_utilization = workload_analysis.get('capacity_utilization', 0)
            
            hiring_summary = {
                "total_employees_needed": int(total_employees_needed),
                "total_hiring_cost": self._clean_float(total_cost),
                "current_capacity_utilization": self._clean_float(capacity_utilization),
                "hiring_priority": hiring_forecast.get('overall_recommendation', {}).get('priority', 'Low'),
                "recommended_timeline": hiring_forecast.get('overall_recommendation', {}).get('timeline', 'No immediate need'),
                "roi_percentage": self._clean_float(cost_analysis.get('roi_percentage', 0)),
                "confidence_level": hiring_forecast.get('overall_recommendation', {}).get('confidence', 'Low'),
                "data_quality": "High" if len(workload_analysis.get('monthly_workload', [])) >= 3 else "Medium"
            }
            
            logger.info("Hiring forecasting analysis completed successfully")
            
            return {
                "hiring_summary": hiring_summary,
                "workload_analysis": workload_analysis,
                "skill_analysis": skill_analysis,
                "hiring_forecast": hiring_forecast,
                "cost_analysis": cost_analysis,
                "data_summary": {
                    "whizible_records": int(len(whizible_clean)),
                    "plotting_records": int(len(plotting_clean)),
                    "months_analyzed": int(workload_analysis.get('total_months_analyzed', 0)),
                    "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating hiring analysis: {str(e)}")
            raise Exception(f"Hiring analysis generation failed: {str(e)}")
    
    def _clean_float(self, value):
        """Clean float values for JSON serialization."""
        import math
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                return 0.0
            return round(float(value), 2)
        return value
    
    def _clean_for_json(self, data):
        """Clean data to ensure JSON serialization compatibility."""
        import math
        
        if isinstance(data, dict):
            return {k: self._clean_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_for_json(item) for item in data]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return 0.0
            return round(data, 2)
        elif isinstance(data, (int, str, bool)) or data is None:
            return data
        else:
            # Convert other types to string
            return str(data)
