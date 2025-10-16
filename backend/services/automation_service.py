import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from services.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)

class AutomationService:
    """Service for detecting automation opportunities using ML/AI analysis."""
    
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
    
    def load_skill_mapping(self) -> pd.DataFrame:
        """Load skill mapping data from local CSV file."""
        try:
            file_path = os.path.join(self.data_path, 'Skill mapping.csv')
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} skill mapping records")
            return df
        except Exception as e:
            logger.error(f"Error loading skill mapping data: {str(e)}")
            raise Exception(f"Failed to load skill mapping data: {str(e)}")
    
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
            
            # Add month column for frequency analysis
            df['Month'] = df['TimesheetDate'].dt.to_period('M')
            
            logger.info(f"Preprocessed {len(df)} valid Whizible records")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing Whizible data: {str(e)}")
            raise Exception(f"Failed to preprocess Whizible data: {str(e)}")
    
    def preprocess_skill_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess and clean skill mapping data."""
        try:
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Clean text columns
            text_columns = ['Role', 'Business Area', 'Question', 'Reply', 'Industry', 'EmployeeCode']
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = df[col].replace('nan', 'Unknown')
            
            # Filter out invalid records
            df = df[df['EmployeeCode'] != 'Unknown']
            
            logger.info(f"Preprocessed {len(df)} valid skill mapping records")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing skill mapping data: {str(e)}")
            raise Exception(f"Failed to preprocess skill mapping data: {str(e)}")
    
    def merge_task_skill_data(self, whizible_df: pd.DataFrame, skill_df: pd.DataFrame) -> pd.DataFrame:
        """Merge timesheet data with skill mapping for enriched analysis."""
        try:
            # Get unique employee skills (take the most common role for each employee)
            employee_skills = skill_df.groupby('EmployeeCode').agg({
                'Role': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown',
                'Business Area': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown',
                'Industry': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown'
            }).reset_index()
            
            # Merge with timesheet data
            merged_df = pd.merge(
                whizible_df,
                employee_skills,
                on='EmployeeCode',
                how='left'
            )
            
            # Fill missing values
            merged_df['Role'] = merged_df['Role'].fillna('Unknown')
            merged_df['Business Area'] = merged_df['Business Area'].fillna('Unknown')
            merged_df['Industry'] = merged_df['Industry'].fillna('Unknown')
            
            logger.info(f"Merged data: {len(merged_df)} records with skill information")
            return merged_df
            
        except Exception as e:
            logger.error(f"Error merging task-skill data: {str(e)}")
            return whizible_df  # Return original data if merge fails
    
    def calculate_task_frequency(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate frequency of each task type."""
        try:
            # Group by task name and month to get frequency
            task_frequency = df.groupby(['TaskName', 'Month']).size().reset_index(name='Monthly_Count')
            
            # Calculate average monthly frequency
            avg_frequency = task_frequency.groupby('TaskName')['Monthly_Count'].agg(['mean', 'std', 'count']).reset_index()
            avg_frequency.columns = ['TaskName', 'Avg_Monthly_Frequency', 'Frequency_Std', 'Months_Observed']
            
            # Fill NaN values
            avg_frequency['Frequency_Std'] = avg_frequency['Frequency_Std'].fillna(0)
            
            logger.info(f"Calculated frequency for {len(avg_frequency)} unique tasks")
            return avg_frequency
            
        except Exception as e:
            logger.error(f"Error calculating task frequency: {str(e)}")
            return pd.DataFrame()
    
    def calculate_task_effort(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate effort metrics for each task type."""
        try:
            # Group by task name to get effort metrics
            task_effort = df.groupby('TaskName').agg({
                'Hours(Filled)': ['sum', 'mean', 'std', 'count'],
                'EmployeeCode': 'nunique',
                'Project name': 'nunique'
            }).reset_index()
            
            # Flatten column names
            task_effort.columns = [
                'TaskName', 'Total_Hours', 'Avg_Hours_Per_Entry', 'Hours_Std', 'Total_Entries',
                'Unique_Employees', 'Unique_Projects'
            ]
            
            # Fill NaN values
            task_effort['Hours_Std'] = task_effort['Hours_Std'].fillna(0)
            
            # Calculate monthly effort
            task_effort['Monthly_Hours'] = task_effort['Total_Hours'] / 2  # Assuming 2-year period
            
            logger.info(f"Calculated effort for {len(task_effort)} unique tasks")
            return task_effort
            
        except Exception as e:
            logger.error(f"Error calculating task effort: {str(e)}")
            return pd.DataFrame()
    
    def calculate_task_variance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate variance/consistency metrics for tasks."""
        try:
            # Calculate variance in hours per task
            task_variance = df.groupby('TaskName')['Hours(Filled)'].agg(['std', 'mean']).reset_index()
            task_variance.columns = ['TaskName', 'Hours_Std', 'Hours_Mean']
            
            # Calculate coefficient of variation (std/mean)
            task_variance['Coefficient_Variation'] = np.where(
                task_variance['Hours_Mean'] > 0,
                task_variance['Hours_Std'] / task_variance['Hours_Mean'],
                0
            )
            
            # Calculate repeatability score (inverse of variation)
            task_variance['Repeatability_Score'] = np.where(
                task_variance['Coefficient_Variation'] > 0,
                1 / (1 + task_variance['Coefficient_Variation']),
                1
            )
            
            logger.info(f"Calculated variance for {len(task_variance)} unique tasks")
            return task_variance
            
        except Exception as e:
            logger.error(f"Error calculating task variance: {str(e)}")
            return pd.DataFrame()
    
    def create_task_embeddings(self, task_names: List[str]) -> np.ndarray:
        """Create TF-IDF embeddings for task names."""
        try:
            # Clean task names
            cleaned_tasks = [str(task).lower().strip() for task in task_names]
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )
            
            # Fit and transform
            embeddings = vectorizer.fit_transform(cleaned_tasks)
            
            logger.info(f"Created embeddings for {len(task_names)} tasks")
            return embeddings.toarray(), vectorizer
            
        except Exception as e:
            logger.error(f"Error creating task embeddings: {str(e)}")
            # Return simple one-hot encoding as fallback
            return np.eye(len(task_names)), None
    
    def cluster_similar_tasks(self, task_features: pd.DataFrame, embeddings: np.ndarray) -> pd.DataFrame:
        """Cluster similar tasks using K-Means."""
        try:
            # Determine optimal number of clusters (5-15% of total tasks)
            n_tasks = len(task_features)
            n_clusters = max(5, min(20, n_tasks // 10))
            
            # Perform K-Means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Add cluster labels to features
            task_features['Cluster'] = cluster_labels
            
            # Calculate cluster statistics - only use available columns
            agg_dict = {
                'TaskName': 'count',
                'Avg_Monthly_Frequency': 'mean',
                'Monthly_Hours': 'sum'
            }
            
            # Only add Automation_Score if it exists
            if 'Automation_Score' in task_features.columns:
                agg_dict['Automation_Score'] = 'mean'
            
            cluster_stats = task_features.groupby('Cluster').agg(agg_dict).reset_index()
            
            # Set column names based on what was aggregated
            if 'Automation_Score' in task_features.columns:
                cluster_stats.columns = ['Cluster', 'Task_Count', 'Avg_Frequency', 'Total_Hours', 'Avg_Automation_Score']
            else:
                cluster_stats.columns = ['Cluster', 'Task_Count', 'Avg_Frequency', 'Total_Hours']
                cluster_stats['Avg_Automation_Score'] = 0  # Default value
            
            logger.info(f"Clustered {n_tasks} tasks into {n_clusters} clusters")
            return task_features, cluster_stats
            
        except Exception as e:
            logger.error(f"Error clustering tasks: {str(e)}")
            # Return original data with dummy cluster
            task_features['Cluster'] = 0
            return task_features, pd.DataFrame()
    
    def calculate_automation_score(self, task_features: pd.DataFrame) -> pd.DataFrame:
        """Calculate automation feasibility score for each task."""
        try:
            # Normalize features for scoring
            task_features['Frequency_Score'] = np.where(
                task_features['Avg_Monthly_Frequency'] >= 15, 100,
                np.where(task_features['Avg_Monthly_Frequency'] >= 10, 75,
                np.where(task_features['Avg_Monthly_Frequency'] >= 5, 50, 25))
            )
            
            task_features['Effort_Score'] = np.where(
                task_features['Avg_Hours_Per_Entry'] >= 2, 100,
                np.where(task_features['Avg_Hours_Per_Entry'] >= 1, 75,
                np.where(task_features['Avg_Hours_Per_Entry'] >= 0.5, 50, 25))
            )
            
            task_features['Repeatability_Score_Normalized'] = task_features['Repeatability_Score'] * 100
            
            # Calculate complexity score based on task type and role
            complexity_mapping = {
                'Idle Time': 10,  # Very low complexity
                'Advance': 20,    # Low complexity
                'Development': 60, # Medium complexity
                'Testing': 50,    # Medium complexity
                'Analysis': 80,   # High complexity
                'Design': 70,     # High complexity
                'Review': 40,     # Medium complexity
                'Documentation': 30, # Low complexity
                'Reporting': 25,  # Low complexity
                'Data Entry': 15, # Very low complexity
            }
            
            # Check if TaskType column exists, if not create a default
            if 'TaskType' in task_features.columns:
                task_features['Complexity_Score'] = task_features['TaskType'].map(complexity_mapping).fillna(50)
            else:
                task_features['Complexity_Score'] = 50  # Default medium complexity
            task_features['Complexity_Score'] = 100 - task_features['Complexity_Score']  # Invert (lower complexity = higher automation potential)
            
            # Calculate overall automation score (weighted average)
            task_features['Automation_Score'] = (
                task_features['Frequency_Score'] * 0.3 +
                task_features['Effort_Score'] * 0.3 +
                task_features['Repeatability_Score_Normalized'] * 0.2 +
                task_features['Complexity_Score'] * 0.2
            )
            
            # Classify automation priority
            task_features['Automation_Priority'] = np.where(
                task_features['Automation_Score'] >= 75, 'High',
                np.where(task_features['Automation_Score'] >= 50, 'Medium', 'Low')
            )
            
            logger.info(f"Calculated automation scores for {len(task_features)} tasks")
            return task_features
            
        except Exception as e:
            logger.error(f"Error calculating automation scores: {str(e)}")
            return task_features
    
    def classify_automation_type(self, task_features: pd.DataFrame) -> pd.DataFrame:
        """Classify tasks by automation type."""
        try:
            # Define automation type rules
            def get_automation_type(row):
                task_name = str(row['TaskName']).lower()
                task_type = str(row.get('TaskType', '')).lower() if 'TaskType' in row else ''
                
                # RPA candidates (repetitive UI interactions)
                if any(keyword in task_name for keyword in ['entry', 'input', 'copy', 'paste', 'transfer', 'sync']):
                    return 'RPA'
                elif task_type in ['data entry', 'advance']:
                    return 'RPA'
                
                # API automation (system integrations)
                elif any(keyword in task_name for keyword in ['api', 'integration', 'sync', 'import', 'export']):
                    return 'API'
                elif any(keyword in task_name for keyword in ['report', 'dashboard', 'analytics']):
                    return 'API'
                
                # Excel/Script automation (calculations, transformations)
                elif any(keyword in task_name for keyword in ['calculation', 'formula', 'analysis', 'summary']):
                    return 'Script'
                elif task_type in ['reporting', 'documentation']:
                    return 'Script'
                
                # Process optimization (workflow improvements)
                elif any(keyword in task_name for keyword in ['approval', 'review', 'validation', 'check']):
                    return 'Process'
                elif task_type in ['review', 'testing']:
                    return 'Process'
                
                else:
                    return 'General'
            
            task_features['Automation_Type'] = task_features.apply(get_automation_type, axis=1)
            
            logger.info(f"Classified automation types for {len(task_features)} tasks")
            return task_features
            
        except Exception as e:
            logger.error(f"Error classifying automation types: {str(e)}")
            task_features['Automation_Type'] = 'General'
            return task_features
    
    def estimate_time_savings(self, task_features: pd.DataFrame) -> Dict[str, Any]:
        """Estimate potential time savings from automation."""
        try:
            # Calculate savings by automation type
            agg_dict = {
                'Monthly_Hours': 'sum',
                'TaskName': 'count'
            }
            
            # Only add Automation_Score if it exists
            if 'Automation_Score' in task_features.columns:
                agg_dict['Automation_Score'] = 'mean'
            
            savings_by_type = task_features.groupby('Automation_Type').agg(agg_dict).reset_index()
            
            # Set column names based on what was aggregated
            if 'Automation_Score' in task_features.columns:
                savings_by_type.columns = ['Automation_Type', 'Monthly_Hours', 'Avg_Score', 'Task_Count']
            else:
                savings_by_type.columns = ['Automation_Type', 'Monthly_Hours', 'Task_Count']
                savings_by_type['Avg_Score'] = 50  # Default score
            
            # Estimate automation potential (percentage of time that can be saved)
            automation_potential = {
                'RPA': 0.8,      # 80% of time can be saved
                'API': 0.7,      # 70% of time can be saved
                'Script': 0.6,   # 60% of time can be saved
                'Process': 0.4,  # 40% of time can be saved
                'General': 0.3   # 30% of time can be saved
            }
            
            savings_by_type['Savings_Potential'] = savings_by_type['Automation_Type'].map(automation_potential)
            savings_by_type['Estimated_Monthly_Savings'] = savings_by_type['Monthly_Hours'] * savings_by_type['Savings_Potential']
            
            # Calculate total potential savings
            total_monthly_hours = task_features['Monthly_Hours'].sum()
            total_potential_savings = savings_by_type['Estimated_Monthly_Savings'].sum()
            automation_percentage = (total_potential_savings / total_monthly_hours) * 100 if total_monthly_hours > 0 else 0
            
            roi_analysis = {
                'total_monthly_hours': total_monthly_hours,
                'total_potential_savings': total_potential_savings,
                'automation_percentage': automation_percentage,
                'savings_by_type': savings_by_type.to_dict('records'),
                'top_opportunities': task_features.nlargest(10, 'Estimated_Monthly_Savings').to_dict('records')
            }
            
            logger.info(f"Estimated {total_potential_savings:.1f} hours/month in potential savings")
            return roi_analysis
            
        except Exception as e:
            logger.error(f"Error estimating time savings: {str(e)}")
            return {'total_monthly_hours': 0, 'total_potential_savings': 0, 'automation_percentage': 0}
    
    def identify_top_candidates(self, task_features: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify top automation candidates."""
        try:
            # Filter for high-potential tasks - check if Automation_Score exists
            if 'Automation_Score' in task_features.columns:
                high_potential = task_features[
                    (task_features['Automation_Score'] >= 60) &
                    (task_features['Monthly_Hours'] >= 5)
                ].copy()
            else:
                # If no automation score, use frequency and hours as criteria
                high_potential = task_features[
                    (task_features['Avg_Monthly_Frequency'] >= 5) &
                    (task_features['Monthly_Hours'] >= 5)
                ].copy()
                high_potential['Automation_Score'] = 60  # Default score
                high_potential['Automation_Priority'] = 'Medium'  # Default priority
            
            # Calculate estimated monthly savings
            automation_potential = {
                'RPA': 0.8, 'API': 0.7, 'Script': 0.6, 'Process': 0.4, 'General': 0.3
            }
            high_potential['Estimated_Monthly_Savings'] = high_potential['Monthly_Hours'] * high_potential['Automation_Type'].map(automation_potential)
            
            # Sort by automation score and savings
            sort_column = 'Automation_Score' if 'Automation_Score' in high_potential.columns else 'Monthly_Hours'
            top_candidates = high_potential.nlargest(15, sort_column)
            
            # Select columns that exist
            available_columns = []
            for col in ['TaskName', 'TaskType', 'Avg_Monthly_Frequency', 'Avg_Hours_Per_Entry', 
                       'Monthly_Hours', 'Automation_Score', 'Automation_Priority', 'Automation_Type', 
                       'Estimated_Monthly_Savings', 'Unique_Employees', 'Unique_Projects']:
                if col in top_candidates.columns:
                    available_columns.append(col)
            
            top_candidates = top_candidates[available_columns].to_dict('records')
            
            logger.info(f"Identified {len(top_candidates)} top automation candidates")
            return top_candidates
            
        except Exception as e:
            logger.error(f"Error identifying top candidates: {str(e)}")
            return []
    
    def generate_automation_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive automation opportunity analysis."""
        try:
            logger.info("Starting automation opportunity analysis...")
            
            # Load and preprocess data
            whizible_df = self.load_whizible_data()
            skill_df = self.load_skill_mapping()
            
            whizible_clean = self.preprocess_whizible_data(whizible_df)
            skill_clean = self.preprocess_skill_mapping(skill_df)
            
            # Merge data
            merged_df = self.merge_task_skill_data(whizible_clean, skill_clean)
            
            # Calculate task metrics
            frequency_df = self.calculate_task_frequency(merged_df)
            effort_df = self.calculate_task_effort(merged_df)
            variance_df = self.calculate_task_variance(merged_df)
            
            # Merge all metrics
            task_features = pd.merge(frequency_df, effort_df, on='TaskName', how='inner')
            task_features = pd.merge(task_features, variance_df, on='TaskName', how='inner')
            
            # Add TaskType column from original data if it exists
            if 'TaskType' in merged_df.columns:
                task_type_mapping = merged_df.groupby('TaskName')['TaskType'].first().to_dict()
                task_features['TaskType'] = task_features['TaskName'].map(task_type_mapping).fillna('Unknown')
            
            # Create embeddings and cluster tasks
            task_names = task_features['TaskName'].tolist()
            embeddings, vectorizer = self.create_task_embeddings(task_names)
            
            # Calculate automation scores
            task_features = self.calculate_automation_score(task_features)
            task_features = self.classify_automation_type(task_features)
            
            # Cluster similar tasks
            task_features, cluster_stats = self.cluster_similar_tasks(task_features, embeddings)
            
            # Generate analysis results
            roi_analysis = self.estimate_time_savings(task_features)
            top_candidates = self.identify_top_candidates(task_features)
            
            # Generate summary metrics
            total_tasks = len(task_features)
            
            # Handle missing columns gracefully
            if 'Automation_Score' in task_features.columns:
                automatable_tasks = len(task_features[task_features['Automation_Score'] >= 50])
                avg_automation_score = self._clean_float(task_features['Automation_Score'].mean())
            else:
                automatable_tasks = len(task_features[task_features['Avg_Monthly_Frequency'] >= 5])
                avg_automation_score = 50  # Default score
            
            if 'Automation_Priority' in task_features.columns:
                high_priority_tasks = len(task_features[task_features['Automation_Priority'] == 'High'])
            else:
                high_priority_tasks = len(task_features[task_features['Avg_Monthly_Frequency'] >= 10])
            
            automation_summary = {
                "total_tasks_analyzed": int(total_tasks),
                "automatable_tasks": int(automatable_tasks),
                "high_priority_tasks": int(high_priority_tasks),
                "automation_percentage": self._clean_float((automatable_tasks / total_tasks) * 100) if total_tasks > 0 else 0,
                "avg_automation_score": avg_automation_score,
                "total_monthly_hours": self._clean_float(roi_analysis.get('total_monthly_hours', 0)),
                "potential_monthly_savings": self._clean_float(roi_analysis.get('total_potential_savings', 0)),
                "top_automation_type": task_features['Automation_Type'].mode().iloc[0] if len(task_features) > 0 else 'Unknown'
            }
            
            # Prepare task clusters for display
            task_clusters = []
            for _, cluster in cluster_stats.iterrows():
                cluster_tasks = task_features[task_features['Cluster'] == cluster['Cluster']]
                cluster_info = {
                    "cluster_id": int(cluster['Cluster']),
                    "task_count": int(cluster['Task_Count']),
                    "avg_frequency": self._clean_float(cluster['Avg_Frequency']),
                    "total_hours": self._clean_float(cluster['Total_Hours']),
                    "avg_automation_score": self._clean_float(cluster['Avg_Automation_Score']),
                    "sample_tasks": cluster_tasks['TaskName'].head(3).tolist()
                }
                task_clusters.append(cluster_info)
            
            # Prepare automation breakdown
            automation_breakdown = task_features.groupby('Automation_Type').agg({
                'TaskName': 'count',
                'Monthly_Hours': 'sum',
                'Automation_Score': 'mean'
            }).reset_index()
            automation_breakdown.columns = ['Automation_Type', 'Task_Count', 'Total_Hours', 'Avg_Score']
            
            logger.info("Automation opportunity analysis completed successfully")
            
            return {
                "automation_summary": automation_summary,
                "task_clusters": self._clean_for_json(task_clusters),
                "top_candidates": self._clean_for_json(top_candidates),
                "automation_breakdown": self._clean_for_json(automation_breakdown.to_dict('records')),
                "roi_analysis": self._clean_for_json(roi_analysis),
                "data_summary": {
                    "whizible_records": int(len(whizible_clean)),
                    "skill_records": int(len(skill_clean)),
                    "unique_tasks": int(total_tasks),
                    "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating automation analysis: {str(e)}")
            raise Exception(f"Automation analysis generation failed: {str(e)}")
    
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
