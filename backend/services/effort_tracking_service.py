from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class EffortTrackingService:
    """
    Effort tracking service for analyzing variance between actual and budgeted effort.
    Provides statistical analysis, anomaly detection, and root cause identification.
    """
    
    def __init__(self):
        self.data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')
        self.whizible_file = os.path.join(self.data_path, 'Whizible data.csv')
        self.plotting_file = os.path.join(self.data_path, 'Plotting tool data.csv')
        self.skill_file = os.path.join(self.data_path, 'Skill mapping.csv')
        
        # Standard working hours per month (8 hours/day * 22 working days)
        self.standard_hours_per_month = 176
        
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
        """Load Whizible, Plotting, and Skill mapping data from root directory."""
        try:
            # Load Whizible data (actual effort)
            whizible_df = pd.read_csv(self.whizible_file)
            logger.info(f"Loaded Whizible data: {len(whizible_df)} records")
            
            # Load Plotting data (budgeted effort)
            plotting_df = pd.read_csv(self.plotting_file)
            logger.info(f"Loaded Plotting data: {len(plotting_df)} records")
            
            # Load Skill mapping data (optional)
            skill_df = None
            if os.path.exists(self.skill_file):
                skill_df = pd.read_csv(self.skill_file)
                logger.info(f"Loaded Skill mapping data: {len(skill_df)} records")
            else:
                logger.warning("Skill mapping file not found, proceeding without skill analysis")
            
            return whizible_df, plotting_df, skill_df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise Exception(f"Failed to load data files: {str(e)}")
    
    def preprocess_whizible_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess and clean Whizible timesheet data."""
        try:
            # Clean and convert data types
            df['Hours(Filled)'] = pd.to_numeric(df['Hours(Filled)'], errors='coerce')
            df['TimesheetDate'] = pd.to_datetime(df['TimesheetDate'], errors='coerce')
            df['Project name'] = df['Project name'].astype(str)
            df['EmployeeCode'] = df['EmployeeCode'].astype(str)
            df['TaskType'] = df['TaskType'].astype(str)
            
            # Remove invalid records
            df = df.dropna(subset=['Hours(Filled)', 'TimesheetDate', 'Project name'])
            df = df[df['Hours(Filled)'] > 0]  # Remove zero or negative hours
            
            # Add month column for aggregation
            df['Month'] = df['TimesheetDate'].dt.to_period('M')
            
            logger.info(f"Preprocessed Whizible data: {len(df)} valid records")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing Whizible data: {str(e)}")
            raise Exception(f"Failed to preprocess Whizible data: {str(e)}")
    
    def preprocess_plotting_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess and clean Plotting tool budget data."""
        try:
            # The CSV has headers in row 1, but actual column names in row 2
            # Use row 1 as column names
            if len(df) > 1:
                df.columns = df.iloc[0]
                df = df.drop(df.index[0]).reset_index(drop=True)
            
            # Clean column names and data
            df.columns = df.columns.str.strip()
            
            # Convert allocation percentages to numeric
            allocation_cols = [col for col in df.columns if '2025-' in col]
            for col in allocation_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Clean project names and resource codes
            df['Project name'] = df['Project name'].astype(str)
            df['Resource Code'] = df['Resource Code'].astype(str)
            df['Resource  Allocation'] = pd.to_numeric(df['Resource  Allocation'], errors='coerce').fillna(0)
            
            # Remove bench resources (allocation = 0)
            df = df[df['Resource  Allocation'] > 0]
            
            # Convert allocation % to budgeted hours per month
            df['Budgeted_Hours_Per_Month'] = (df['Resource  Allocation'] / 100) * self.standard_hours_per_month
            
            logger.info(f"Preprocessed Plotting data: {len(df)} valid records")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing Plotting data: {str(e)}")
            raise Exception(f"Failed to preprocess Plotting data: {str(e)}")
    
    def calculate_effort_variance(self, whizible_df: pd.DataFrame, plotting_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate effort variance between actual and budgeted hours."""
        try:
            # Aggregate actual hours by project and month
            actual_hours = whizible_df.groupby(['Project name', 'Month'])['Hours(Filled)'].sum().reset_index()
            actual_hours.columns = ['Project name', 'Month', 'Actual_Hours']
            
            # Aggregate budgeted hours by project (using average allocation)
            budgeted_hours = plotting_df.groupby('Project name')['Budgeted_Hours_Per_Month'].mean().reset_index()
            budgeted_hours.columns = ['Project name', 'Budgeted_Hours_Per_Month']
            
            # Merge actual and budgeted data
            variance_df = pd.merge(actual_hours, budgeted_hours, on='Project name', how='outer')
            
            # Fill missing values
            variance_df['Actual_Hours'] = variance_df['Actual_Hours'].fillna(0)
            variance_df['Budgeted_Hours_Per_Month'] = variance_df['Budgeted_Hours_Per_Month'].fillna(0)
            
            # Calculate variance metrics
            variance_df['Variance_Hours'] = variance_df['Actual_Hours'] - variance_df['Budgeted_Hours_Per_Month']
            variance_df['Variance_Percentage'] = np.where(
                variance_df['Budgeted_Hours_Per_Month'] > 0,
                (variance_df['Variance_Hours'] / variance_df['Budgeted_Hours_Per_Month']) * 100,
                0
            )
            
            # Clean NaN and inf values
            variance_df['Variance_Percentage'] = variance_df['Variance_Percentage'].replace([np.inf, -np.inf], 0)
            variance_df['Variance_Percentage'] = variance_df['Variance_Percentage'].fillna(0)
            variance_df['Variance_Hours'] = variance_df['Variance_Hours'].fillna(0)
            
            # Add variance status
            variance_df['Status'] = np.where(
                variance_df['Variance_Percentage'] > 20, 'Overrun',
                np.where(variance_df['Variance_Percentage'] < -10, 'Underutilized',
                'On Budget')
            )
            
            # Calculate total variance by project
            project_variance = variance_df.groupby('Project name').agg({
                'Actual_Hours': 'sum',
                'Budgeted_Hours_Per_Month': 'sum',
                'Variance_Hours': 'sum',
                'Variance_Percentage': 'mean'
            }).reset_index()
            
            # Clean project variance data
            project_variance['Variance_Percentage'] = project_variance['Variance_Percentage'].replace([np.inf, -np.inf], 0)
            project_variance['Variance_Percentage'] = project_variance['Variance_Percentage'].fillna(0)
            project_variance['Variance_Hours'] = project_variance['Variance_Hours'].fillna(0)
            project_variance['Actual_Hours'] = project_variance['Actual_Hours'].fillna(0)
            project_variance['Budgeted_Hours_Per_Month'] = project_variance['Budgeted_Hours_Per_Month'].fillna(0)
            
            project_variance['Status'] = np.where(
                project_variance['Variance_Percentage'] > 20, 'Overrun',
                np.where(project_variance['Variance_Percentage'] < -10, 'Underutilized',
                'On Budget')
            )
            
            logger.info(f"Calculated variance for {len(project_variance)} projects")
            return project_variance
            
        except Exception as e:
            logger.error(f"Error calculating effort variance: {str(e)}")
            raise Exception(f"Failed to calculate effort variance: {str(e)}")
    
    def analyze_by_task_type(self, whizible_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze effort variance by task type."""
        try:
            task_analysis = whizible_df.groupby('TaskType').agg({
                'Hours(Filled)': ['sum', 'mean', 'count'],
                'Project name': 'nunique'
            }).round(2)
            
            # Flatten column names
            task_analysis.columns = ['Total_Hours', 'Avg_Hours_Per_Entry', 'Entry_Count', 'Project_Count']
            task_analysis = task_analysis.reset_index()
            
            # Calculate utilization metrics
            task_analysis['Hours_Per_Project'] = task_analysis['Total_Hours'] / task_analysis['Project_Count']
            task_analysis = task_analysis.sort_values('Total_Hours', ascending=False)
            
            return {
                'task_summary': task_analysis.to_dict('records'),
                'top_task_types': task_analysis.head(10).to_dict('records'),
                'idle_time_analysis': self._analyze_idle_time(whizible_df)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing by task type: {str(e)}")
            return {'task_summary': [], 'top_task_types': [], 'idle_time_analysis': {}}
    
    def _analyze_idle_time(self, whizible_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze idle time patterns."""
        try:
            idle_data = whizible_df[whizible_df['TaskType'] == 'Idle Time']
            
            if len(idle_data) == 0:
                return {'total_idle_hours': 0, 'idle_employees': 0, 'idle_projects': 0}
            
            idle_by_employee = idle_data.groupby('EmployeeCode')['Hours(Filled)'].sum().sort_values(ascending=False)
            idle_by_project = idle_data.groupby('Project name')['Hours(Filled)'].sum().sort_values(ascending=False)
            
            return {
                'total_idle_hours': idle_data['Hours(Filled)'].sum(),
                'idle_employees': len(idle_by_employee),
                'idle_projects': len(idle_by_project),
                'top_idle_employees': idle_by_employee.head(5).to_dict(),
                'top_idle_projects': idle_by_project.head(5).to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing idle time: {str(e)}")
            return {'total_idle_hours': 0, 'idle_employees': 0, 'idle_projects': 0}
    
    def analyze_by_resource(self, whizible_df: pd.DataFrame, plotting_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze resource utilization and efficiency."""
        try:
            # Resource utilization from Whizible
            resource_util = whizible_df.groupby('EmployeeCode').agg({
                'Hours(Filled)': 'sum',
                'Project name': 'nunique',
                'TaskType': lambda x: (x == 'Idle Time').sum()
            }).reset_index()
            
            resource_util.columns = ['EmployeeCode', 'Total_Hours', 'Project_Count', 'Idle_Entries']
            resource_util['Idle_Percentage'] = (resource_util['Idle_Entries'] / 
                                              (resource_util['Idle_Entries'] + resource_util['Project_Count'])) * 100
            
            # Resource allocation from Plotting
            resource_allocation = plotting_df.groupby('Resource Code').agg({
                'Resource  Allocation': 'mean',
                'Project name': 'nunique'
            }).reset_index()
            
            resource_allocation.columns = ['Resource Code', 'Avg_Allocation', 'Allocated_Projects']
            
            # Merge utilization and allocation
            resource_analysis = pd.merge(
                resource_util, 
                resource_allocation, 
                left_on='EmployeeCode', 
                right_on='Resource Code', 
                how='outer'
            )
            
            resource_analysis['Efficiency_Score'] = np.where(
                resource_analysis['Idle_Percentage'] < 10, 'High',
                np.where(resource_analysis['Idle_Percentage'] < 30, 'Medium', 'Low')
            )
            
            return {
                'resource_summary': resource_analysis.to_dict('records'),
                'high_efficiency': resource_analysis[resource_analysis['Efficiency_Score'] == 'High'].to_dict('records'),
                'low_efficiency': resource_analysis[resource_analysis['Efficiency_Score'] == 'Low'].to_dict('records'),
                'underutilized': resource_analysis[resource_analysis['Idle_Percentage'] > 50].to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing by resource: {str(e)}")
            return {'resource_summary': [], 'high_efficiency': [], 'low_efficiency': [], 'underutilized': []}
    
    def detect_anomalies(self, variance_df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalous effort patterns using Isolation Forest."""
        try:
            if len(variance_df) < 10:
                return {'detected_anomalies': 0, 'anomaly_details': []}
            
            # Prepare features for anomaly detection
            features = variance_df[['Actual_Hours', 'Budgeted_Hours_Per_Month', 'Variance_Percentage']].fillna(0)
            
            # Standardize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Apply Isolation Forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomaly_labels = iso_forest.fit_predict(features_scaled)
            
            # Get anomaly details
            anomalies = variance_df[anomaly_labels == -1].copy()
            anomalies['Anomaly_Score'] = iso_forest.decision_function(features_scaled[anomaly_labels == -1])
            
            anomaly_details = []
            for _, row in anomalies.iterrows():
                anomaly_details.append({
                    'project_name': row['Project name'],
                    'actual_hours': row['Actual_Hours'],
                    'budgeted_hours': row['Budgeted_Hours_Per_Month'],
                    'variance_pct': row['Variance_Percentage'],
                    'anomaly_score': row['Anomaly_Score'],
                    'reason': self._explain_anomaly(row)
                })
            
            return {
                'detected_anomalies': len(anomalies),
                'anomaly_details': anomaly_details,
                'anomaly_rate': len(anomalies) / len(variance_df) * 100
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return {'detected_anomalies': 0, 'anomaly_details': [], 'anomaly_rate': 0}
    
    def _explain_anomaly(self, row: pd.Series) -> str:
        """Explain why a project is considered anomalous."""
        if row['Variance_Percentage'] > 100:
            return "Extreme overrun - actual hours more than double budgeted"
        elif row['Variance_Percentage'] > 50:
            return "Significant overrun - actual hours 50%+ over budget"
        elif row['Variance_Percentage'] < -50:
            return "Severe underutilization - actual hours 50%+ under budget"
        elif row['Actual_Hours'] > 1000:
            return "Unusually high total hours logged"
        else:
            return "Unusual pattern in effort distribution"
    
    def identify_root_causes(self, variance_df: pd.DataFrame, task_analysis: Dict, resource_analysis: Dict) -> Dict[str, Any]:
        """Identify root causes of effort variance."""
        try:
            overrun_projects = variance_df[variance_df['Variance_Percentage'] > 20]
            underutilized_projects = variance_df[variance_df['Variance_Percentage'] < -10]
            
            root_causes = {
                'overrun_factors': [],
                'underutilization_factors': [],
                'systemic_issues': []
            }
            
            # Analyze overrun factors
            if len(overrun_projects) > 0:
                avg_overrun = overrun_projects['Variance_Percentage'].mean()
                total_overrun_hours = overrun_projects['Variance_Hours'].sum()
                
                root_causes['overrun_factors'].append({
                    'factor': 'Project Estimation Accuracy',
                    'description': f"Average overrun of {avg_overrun:.1f}% across {len(overrun_projects)} projects",
                    'impact': f"{total_overrun_hours:.0f} hours over budget",
                    'severity': 'High' if avg_overrun > 40 else 'Medium'
                })
            
            # Analyze task type patterns
            if 'idle_time_analysis' in task_analysis:
                idle_data = task_analysis['idle_time_analysis']
                if idle_data['total_idle_hours'] > 500:
                    root_causes['systemic_issues'].append({
                        'factor': 'Resource Underutilization',
                        'description': f"{idle_data['total_idle_hours']:.0f} hours of idle time across {idle_data['idle_employees']} employees",
                        'impact': 'Lost productivity and revenue opportunity',
                        'severity': 'High'
                    })
            
            # Analyze resource efficiency
            if 'underutilized' in resource_analysis and len(resource_analysis['underutilized']) > 0:
                underutilized_count = len(resource_analysis['underutilized'])
                root_causes['systemic_issues'].append({
                    'factor': 'Resource Allocation Mismatch',
                    'description': f"{underutilized_count} resources with >50% idle time",
                    'impact': 'Inefficient resource utilization',
                    'severity': 'Medium'
                })
            
            return root_causes
            
        except Exception as e:
            logger.error(f"Error identifying root causes: {str(e)}")
            return {'overrun_factors': [], 'underutilization_factors': [], 'systemic_issues': []}
    
    def generate_effort_analysis(self) -> Dict[str, Any]:
        """Main method to generate complete effort analysis."""
        try:
            # Load and preprocess data
            whizible_df, plotting_df, skill_df = self.load_data()
            whizible_clean = self.preprocess_whizible_data(whizible_df)
            plotting_clean = self.preprocess_plotting_data(plotting_df)
            
            # Calculate variance
            variance_df = self.calculate_effort_variance(whizible_clean, plotting_clean)
            
            # Perform detailed analysis
            task_analysis = self.analyze_by_task_type(whizible_clean)
            resource_analysis = self.analyze_by_resource(whizible_clean, plotting_clean)
            anomalies = self.detect_anomalies(variance_df)
            root_causes = self.identify_root_causes(variance_df, task_analysis, resource_analysis)
            
            # Generate summary metrics
            total_projects = len(variance_df)
            overrun_projects = len(variance_df[variance_df['Variance_Percentage'] > 20])
            avg_variance = variance_df['Variance_Percentage'].mean()
            total_variance_hours = variance_df['Variance_Hours'].sum()
            
            # Get top at-risk projects
            at_risk_projects = variance_df.nlargest(5, 'Variance_Percentage')[
                ['Project name', 'Actual_Hours', 'Budgeted_Hours_Per_Month', 'Variance_Percentage', 'Status']
            ].to_dict('records')
            
            # Clean data for JSON serialization
            variance_summary = {
                "total_projects_analyzed": int(total_projects),
                "overrun_projects": int(overrun_projects),
                "avg_variance_pct": self._clean_float(avg_variance),
                "total_variance_hours": self._clean_float(total_variance_hours),
                "at_risk_projects": self._clean_for_json(at_risk_projects),
                "overrun_rate": self._clean_float((overrun_projects / total_projects) * 100) if total_projects > 0 else 0.0
            }
            
            # Clean variance_df records
            variance_records = variance_df.to_dict('records')
            variance_records = [self._clean_for_json(record) for record in variance_records]
            
            return {
                "variance_summary": variance_summary,
                "breakdown_analysis": {
                    "by_project": variance_records,
                    "by_task_type": self._clean_for_json(task_analysis),
                    "by_resource": self._clean_for_json(resource_analysis),
                    "by_skill_level": {}  # Will be populated if skill data available
                },
                "anomalies": self._clean_for_json(anomalies),
                "root_causes": self._clean_for_json(root_causes),
                "data_summary": {
                    "whizible_records": int(len(whizible_clean)),
                    "plotting_records": int(len(plotting_clean)),
                    "date_range": {
                        "earliest": whizible_clean['TimesheetDate'].min().strftime('%Y-%m-%d'),
                        "latest": whizible_clean['TimesheetDate'].max().strftime('%Y-%m-%d')
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating effort analysis: {str(e)}")
            raise Exception(f"Effort analysis generation failed: {str(e)}")
    
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
