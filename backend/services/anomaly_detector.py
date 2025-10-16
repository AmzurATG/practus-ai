from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Anomaly detection service for identifying unusual patterns in effort data.
    Uses Isolation Forest and clustering techniques to detect outliers.
    """
    
    def __init__(self):
        self.isolation_forest = IsolationForest(
            contamination=0.1,  # Expect 10% of data to be anomalous
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
    
    def detect_effort_anomalies(self, variance_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect anomalous effort patterns in project variance data.
        
        Args:
            variance_df: DataFrame with columns ['Project name', 'Actual_Hours', 
                       'Budgeted_Hours_Per_Month', 'Variance_Percentage']
        
        Returns:
            Dictionary containing anomaly detection results
        """
        try:
            if len(variance_df) < 10:
                logger.warning("Insufficient data for anomaly detection")
                return {
                    'detected_anomalies': 0,
                    'anomaly_details': [],
                    'anomaly_rate': 0,
                    'method_used': 'insufficient_data'
                }
            
            # Prepare features for anomaly detection
            features = self._prepare_features(variance_df)
            
            # Detect anomalies using Isolation Forest
            anomalies = self._detect_with_isolation_forest(features, variance_df)
            
            # Detect clusters for pattern analysis
            clusters = self._detect_clusters(features, variance_df)
            
            # Generate anomaly explanations
            anomaly_details = self._explain_anomalies(anomalies, variance_df)
            
            return {
                'detected_anomalies': len(anomalies),
                'anomaly_details': anomaly_details,
                'anomaly_rate': len(anomalies) / len(variance_df) * 100,
                'method_used': 'isolation_forest',
                'clusters_detected': len(clusters),
                'cluster_summary': self._summarize_clusters(clusters)
            }
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}")
            return {
                'detected_anomalies': 0,
                'anomaly_details': [],
                'anomaly_rate': 0,
                'method_used': 'error',
                'error': str(e)
            }
    
    def _prepare_features(self, variance_df: pd.DataFrame) -> np.ndarray:
        """Prepare and standardize features for anomaly detection."""
        try:
            # Select relevant features
            feature_columns = ['Actual_Hours', 'Budgeted_Hours_Per_Month', 'Variance_Percentage']
            
            # Handle missing values
            features = variance_df[feature_columns].fillna(0)
            
            # Add derived features
            features['Variance_Ratio'] = np.where(
                features['Budgeted_Hours_Per_Month'] > 0,
                features['Actual_Hours'] / features['Budgeted_Hours_Per_Month'],
                0
            )
            
            features['Effort_Intensity'] = features['Actual_Hours'] / features['Actual_Hours'].max()
            
            # Standardize features
            features_scaled = self.scaler.fit_transform(features)
            
            return features_scaled
            
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            # Fallback to basic features
            basic_features = variance_df[['Actual_Hours', 'Variance_Percentage']].fillna(0)
            return self.scaler.fit_transform(basic_features)
    
    def _detect_with_isolation_forest(self, features: np.ndarray, variance_df: pd.DataFrame) -> pd.DataFrame:
        """Detect anomalies using Isolation Forest algorithm."""
        try:
            # Fit Isolation Forest
            anomaly_labels = self.isolation_forest.fit_predict(features)
            anomaly_scores = self.isolation_forest.decision_function(features)
            
            # Get anomalous records
            anomalies = variance_df[anomaly_labels == -1].copy()
            anomalies['Anomaly_Score'] = anomaly_scores[anomaly_labels == -1]
            
            # Sort by anomaly score (more negative = more anomalous)
            anomalies = anomalies.sort_values('Anomaly_Score')
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error in Isolation Forest detection: {str(e)}")
            return pd.DataFrame()
    
    def _detect_clusters(self, features: np.ndarray, variance_df: pd.DataFrame) -> Dict[int, List[str]]:
        """Detect clusters in the data to identify patterns."""
        try:
            # Use DBSCAN for clustering
            clustering = DBSCAN(eps=0.5, min_samples=3)
            cluster_labels = clustering.fit_predict(features)
            
            # Group projects by cluster
            clusters = {}
            for idx, label in enumerate(cluster_labels):
                if label != -1:  # -1 indicates noise/outliers
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(variance_df.iloc[idx]['Project name'])
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error in cluster detection: {str(e)}")
            return {}
    
    def _explain_anomalies(self, anomalies: pd.DataFrame, variance_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate human-readable explanations for detected anomalies."""
        anomaly_details = []
        
        for _, row in anomalies.iterrows():
            explanation = self._explain_single_anomaly(row, variance_df)
            anomaly_details.append({
                'project_name': row['Project name'],
                'actual_hours': round(row['Actual_Hours'], 1),
                'budgeted_hours': round(row['Budgeted_Hours_Per_Month'], 1),
                'variance_pct': round(row['Variance_Percentage'], 1),
                'anomaly_score': round(row['Anomaly_Score'], 3),
                'explanation': explanation,
                'severity': self._assess_severity(row),
                'recommended_action': self._recommend_action(row)
            })
        
        return anomaly_details
    
    def _explain_single_anomaly(self, row: pd.Series, variance_df: pd.DataFrame) -> str:
        """Explain why a specific project is considered anomalous."""
        variance_pct = row['Variance_Percentage']
        actual_hours = row['Actual_Hours']
        budgeted_hours = row['Budgeted_Hours_Per_Month']
        
        # Calculate percentiles for context
        variance_pct_95 = variance_df['Variance_Percentage'].quantile(0.95)
        actual_hours_95 = variance_df['Actual_Hours'].quantile(0.95)
        
        explanations = []
        
        # Variance-based explanations
        if variance_pct > variance_pct_95:
            explanations.append(f"Variance of {variance_pct:.1f}% is in top 5% of all projects")
        
        if variance_pct > 100:
            explanations.append("Actual hours more than double the budgeted amount")
        elif variance_pct > 50:
            explanations.append("Significant overrun - actual hours 50%+ over budget")
        elif variance_pct < -50:
            explanations.append("Severe underutilization - actual hours 50%+ under budget")
        
        # Hours-based explanations
        if actual_hours > actual_hours_95:
            explanations.append(f"Total hours ({actual_hours:.0f}) is in top 5% of all projects")
        
        if budgeted_hours > 0 and actual_hours / budgeted_hours > 3:
            explanations.append("Actual hours are more than 3x the budgeted amount")
        
        # Combine explanations
        if explanations:
            return "; ".join(explanations)
        else:
            return "Unusual pattern in effort distribution compared to other projects"
    
    def _assess_severity(self, row: pd.Series) -> str:
        """Assess the severity of an anomaly."""
        variance_pct = abs(row['Variance_Percentage'])
        actual_hours = row['Actual_Hours']
        
        if variance_pct > 100 or actual_hours > 2000:
            return "Critical"
        elif variance_pct > 50 or actual_hours > 1000:
            return "High"
        elif variance_pct > 25 or actual_hours > 500:
            return "Medium"
        else:
            return "Low"
    
    def _recommend_action(self, row: pd.Series) -> str:
        """Recommend action based on anomaly type."""
        variance_pct = row['Variance_Percentage']
        
        if variance_pct > 50:
            return "Immediate project review and resource reallocation needed"
        elif variance_pct > 25:
            return "Schedule project review meeting to assess progress"
        elif variance_pct < -25:
            return "Investigate underutilization and consider additional work allocation"
        else:
            return "Monitor closely and review estimation process"
    
    def _summarize_clusters(self, clusters: Dict[int, List[str]]) -> List[Dict[str, Any]]:
        """Summarize detected clusters."""
        cluster_summary = []
        
        for cluster_id, projects in clusters.items():
            cluster_summary.append({
                'cluster_id': cluster_id,
                'project_count': len(projects),
                'projects': projects[:5],  # Show first 5 projects
                'description': f"Cluster of {len(projects)} projects with similar effort patterns"
            })
        
        return cluster_summary
    
    def detect_resource_anomalies(self, resource_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect anomalous resource utilization patterns.
        
        Args:
            resource_df: DataFrame with resource utilization data
        
        Returns:
            Dictionary containing resource anomaly detection results
        """
        try:
            if len(resource_df) < 5:
                return {'detected_anomalies': 0, 'anomaly_details': []}
            
            # Prepare resource features
            resource_features = resource_df[['Total_Hours', 'Idle_Percentage', 'Project_Count']].fillna(0)
            resource_features_scaled = self.scaler.fit_transform(resource_features)
            
            # Detect anomalies
            anomaly_labels = self.isolation_forest.fit_predict(resource_features_scaled)
            anomalies = resource_df[anomaly_labels == -1].copy()
            
            # Generate explanations
            anomaly_details = []
            for _, row in anomalies.iterrows():
                explanation = self._explain_resource_anomaly(row)
                anomaly_details.append({
                    'employee_code': row['EmployeeCode'],
                    'total_hours': row['Total_Hours'],
                    'idle_percentage': row['Idle_Percentage'],
                    'project_count': row['Project_Count'],
                    'explanation': explanation,
                    'recommended_action': self._recommend_resource_action(row)
                })
            
            return {
                'detected_anomalies': len(anomalies),
                'anomaly_details': anomaly_details,
                'anomaly_rate': len(anomalies) / len(resource_df) * 100
            }
            
        except Exception as e:
            logger.error(f"Error detecting resource anomalies: {str(e)}")
            return {'detected_anomalies': 0, 'anomaly_details': []}
    
    def _explain_resource_anomaly(self, row: pd.Series) -> str:
        """Explain why a resource utilization is anomalous."""
        idle_pct = row['Idle_Percentage']
        total_hours = row['Total_Hours']
        
        if idle_pct > 80:
            return f"Extremely high idle time ({idle_pct:.1f}%) - resource severely underutilized"
        elif idle_pct > 50:
            return f"High idle time ({idle_pct:.1f}%) - resource underutilized"
        elif total_hours > 2000:
            return f"Unusually high total hours ({total_hours:.0f}) - potential overwork"
        else:
            return "Unusual utilization pattern compared to other resources"
    
    def _recommend_resource_action(self, row: pd.Series) -> str:
        """Recommend action for resource anomaly."""
        idle_pct = row['Idle_Percentage']
        
        if idle_pct > 70:
            return "Immediate action: Find new project assignments or consider bench management"
        elif idle_pct > 40:
            return "Schedule resource review and identify additional work opportunities"
        elif row['Total_Hours'] > 2000:
            return "Review workload distribution and consider resource relief"
        else:
            return "Monitor utilization patterns and adjust allocation as needed"
