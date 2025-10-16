import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import os
from services.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)

class RetentionService:
    """Service for analyzing client retention and repeat business patterns."""
    
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        
    def load_deals_data(self) -> pd.DataFrame:
        """Load deals data from local CSV file."""
        try:
            file_path = os.path.join(self.data_path, 'Deals Archive.csv')
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} deals records")
            return df
        except Exception as e:
            logger.error(f"Error loading deals data: {str(e)}")
            raise Exception(f"Failed to load deals data: {str(e)}")
    
    def load_stage_history_data(self) -> pd.DataFrame:
        """Load stage history data from local CSV file."""
        try:
            file_path = os.path.join(self.data_path, 'Stage History Archive.csv')
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} stage history records")
            return df
        except Exception as e:
            logger.error(f"Error loading stage history data: {str(e)}")
            raise Exception(f"Failed to load stage history data: {str(e)}")
    
    def load_whizible_data(self) -> pd.DataFrame:
        """Load whizible data for project delivery patterns."""
        try:
            file_path = os.path.join(self.data_path, 'Whizible data.csv')
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} whizible records")
            return df
        except Exception as e:
            logger.warning(f"Whizible data not available: {str(e)}")
            return pd.DataFrame()
    
    def preprocess_deals_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess and clean deals data."""
        try:
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Convert date columns
            date_columns = [
                'Deal_Closing_Date', 'Created_Time', 'Modified_Time', 'Last_Activity_Time',
                'Date_on_which_proposal_sent', 'Original_expected_closure_date',
                'Date_on_which_became_a_Potential', 'Date_on_which_became_a_Qualified_Prospect',
                'Date_on_which_walk_through_scheduled', 'Date_on_which_walk_through_conducted',
                'Date_on_which_follow_up_conducted', 'Date_on_which_converted_to_a_client',
                'Date_on_which_follow_up_scheduled', 'Mandate_start_date', 'Mandate_end_date',
                'Date_on_which_client_lost', 'Date_on_which_became_Need_Identification'
            ]
            
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Convert numeric columns
            numeric_columns = ['Deal Amount', 'Probability', 'Engagement_Tenure_months', 'Monthly_recurring_revenue_amount']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Clean text columns
            text_columns = ['Project name', 'Industry_Type', 'Client_Type', 'Stage', 'Country']
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = df[col].replace('nan', 'Unknown')
            
            # Filter out invalid records
            df = df[df['Project name'] != 'Unknown']
            df = df[df['Project name'] != '']
            
            logger.info(f"Preprocessed {len(df)} valid deals records")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing deals data: {str(e)}")
            raise Exception(f"Failed to preprocess deals data: {str(e)}")
    
    def preprocess_stage_history_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess and clean stage history data."""
        try:
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Convert date columns
            date_columns = ['Modified_Time', 'Deal_Closing_Date', 'Last_Activity_Time', 'Expected_closure_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Convert numeric columns
            numeric_columns = ['Deal Amount', 'Probability', 'Stage Duration Days', 'Stage_Duration_Calendar_Days']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Clean text columns
            text_columns = ['Project name', 'Stage', 'Stage Group']
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = df[col].replace('nan', 'Unknown')
            
            # Filter out invalid records
            df = df[df['Project name'] != 'Unknown']
            df = df[df['Project name'] != '']
            
            logger.info(f"Preprocessed {len(df)} valid stage history records")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing stage history data: {str(e)}")
            raise Exception(f"Failed to preprocess stage history data: {str(e)}")
    
    def calculate_client_retention_score(self, deals_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RFM-style retention scores for clients."""
        try:
            # Group by client (Project name) and calculate metrics
            client_metrics = deals_df.groupby('Project name').agg({
                'Deal Amount': ['sum', 'count', 'mean'],
                'Deal_Closing_Date': 'max',
                'Last_Activity_Time': 'max',
                'Industry_Type': 'first',
                'Client_Type': 'first',
                'Country': 'first'
            }).reset_index()
            
            # Flatten column names
            client_metrics.columns = [
                'Client_Name', 'Total_Revenue', 'Deal_Count', 'Avg_Deal_Size',
                'Last_Deal_Date', 'Last_Activity', 'Industry_Type', 'Client_Type', 'Country'
            ]
            
            # Calculate recency (days since last activity)
            current_date = datetime.now()
            client_metrics['Days_Since_Last_Activity'] = (
                current_date - client_metrics['Last_Activity']
            ).dt.days
            
            # Calculate frequency (deals per year)
            client_metrics['Deals_Per_Year'] = client_metrics['Deal_Count'] / 2  # Assuming 2-year period
            
            # Calculate monetary value (total revenue)
            client_metrics['Monetary_Score'] = client_metrics['Total_Revenue']
            
            # Calculate retention score (0-100)
            # Higher score = better retention potential
            client_metrics['Recency_Score'] = np.where(
                client_metrics['Days_Since_Last_Activity'] <= 30, 100,
                np.where(client_metrics['Days_Since_Last_Activity'] <= 90, 75,
                np.where(client_metrics['Days_Since_Last_Activity'] <= 180, 50,
                np.where(client_metrics['Days_Since_Last_Activity'] <= 365, 25, 0)))
            )
            
            client_metrics['Frequency_Score'] = np.where(
                client_metrics['Deal_Count'] >= 3, 100,
                np.where(client_metrics['Deal_Count'] == 2, 75,
                np.where(client_metrics['Deal_Count'] == 1, 25, 0))
            )
            
            client_metrics['Monetary_Score_Normalized'] = np.where(
                client_metrics['Total_Revenue'] > 100000, 100,
                np.where(client_metrics['Total_Revenue'] > 50000, 75,
                np.where(client_metrics['Total_Revenue'] > 10000, 50,
                np.where(client_metrics['Total_Revenue'] > 0, 25, 0)))
            )
            
            # Overall retention score (weighted average)
            client_metrics['Retention_Score'] = (
                client_metrics['Recency_Score'] * 0.4 +
                client_metrics['Frequency_Score'] * 0.4 +
                client_metrics['Monetary_Score_Normalized'] * 0.2
            )
            
            # Churn risk (inverse of retention score)
            client_metrics['Churn_Risk_Score'] = 100 - client_metrics['Retention_Score']
            
            # Clean NaN values
            client_metrics = client_metrics.fillna(0)
            
            logger.info(f"Calculated retention scores for {len(client_metrics)} clients")
            return client_metrics
            
        except Exception as e:
            logger.error(f"Error calculating retention scores: {str(e)}")
            raise Exception(f"Failed to calculate retention scores: {str(e)}")
    
    def identify_repeat_clients(self, deals_df: pd.DataFrame) -> Dict[str, Any]:
        """Identify clients with repeat business patterns."""
        try:
            # Group by client and analyze deal patterns
            client_deals = deals_df.groupby('Project name').agg({
                'Deal ID': 'count',
                'Deal Amount': ['sum', 'mean'],
                'Deal_Closing_Date': ['min', 'max'],
                'Industry_Type': 'first',
                'Client_Type': 'first'
            }).reset_index()
            
            client_deals.columns = [
                'Client_Name', 'Deal_Count', 'Total_Revenue', 'Avg_Deal_Size',
                'First_Deal_Date', 'Last_Deal_Date', 'Industry_Type', 'Client_Type'
            ]
            
            # Calculate time between deals
            client_deals['Deal_Span_Days'] = (
                client_deals['Last_Deal_Date'] - client_deals['First_Deal_Date']
            ).dt.days
            
            client_deals['Avg_Days_Between_Deals'] = np.where(
                client_deals['Deal_Count'] > 1,
                client_deals['Deal_Span_Days'] / (client_deals['Deal_Count'] - 1),
                0
            )
            
            # Categorize clients
            repeat_clients = client_deals[client_deals['Deal_Count'] >= 2]
            one_time_clients = client_deals[client_deals['Deal_Count'] == 1]
            
            # High-value repeat clients (top 20% by revenue)
            high_value_threshold = repeat_clients['Total_Revenue'].quantile(0.8)
            high_value_repeat = repeat_clients[repeat_clients['Total_Revenue'] >= high_value_threshold]
            
            # Quick repeaters (deals within 6 months)
            quick_repeaters = repeat_clients[repeat_clients['Avg_Days_Between_Deals'] <= 180]
            
            # Long-term clients (deals over 12 months apart)
            long_term_clients = repeat_clients[repeat_clients['Avg_Days_Between_Deals'] > 365]
            
            repeat_analysis = {
                'total_clients': len(client_deals),
                'repeat_clients': len(repeat_clients),
                'one_time_clients': len(one_time_clients),
                'repeat_rate': (len(repeat_clients) / len(client_deals)) * 100 if len(client_deals) > 0 else 0,
                'high_value_repeat': len(high_value_repeat),
                'quick_repeaters': len(quick_repeaters),
                'long_term_clients': len(long_term_clients),
                'avg_deals_per_client': client_deals['Deal_Count'].mean(),
                'avg_time_between_deals': repeat_clients['Avg_Days_Between_Deals'].mean() if len(repeat_clients) > 0 else 0,
                'repeat_client_details': repeat_clients.to_dict('records'),
                'high_value_details': high_value_repeat.to_dict('records'),
                'one_time_details': one_time_clients.to_dict('records')
            }
            
            logger.info(f"Identified {len(repeat_clients)} repeat clients out of {len(client_deals)} total")
            return repeat_analysis
            
        except Exception as e:
            logger.error(f"Error identifying repeat clients: {str(e)}")
            return {'total_clients': 0, 'repeat_clients': 0, 'repeat_rate': 0}
    
    def calculate_engagement_velocity(self, deals_df: pd.DataFrame, stage_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate client engagement velocity metrics."""
        try:
            # Merge deals and stage data
            merged_df = pd.merge(
                deals_df[['Deal ID', 'Project name', 'Deal Amount', 'Stage', 'Deal_Closing_Date']],
                stage_df[['Deal ID', 'Stage', 'Modified_Time', 'Stage Duration Days']],
                on=['Deal ID', 'Stage'],
                how='left'
            )
            
            # Calculate stage velocity by client
            client_velocity = merged_df.groupby('Project name').agg({
                'Stage Duration Days': 'mean',
                'Deal Amount': ['sum', 'count'],
                'Deal_Closing_Date': 'max'
            }).reset_index()
            
            client_velocity.columns = [
                'Client_Name', 'Avg_Stage_Duration', 'Total_Revenue', 'Deal_Count', 'Last_Deal_Date'
            ]
            
            # Calculate days since last deal
            current_date = datetime.now()
            client_velocity['Days_Since_Last_Deal'] = (
                current_date - client_velocity['Last_Deal_Date']
            ).dt.days
            
            # Engagement velocity score (lower stage duration = higher velocity)
            client_velocity['Velocity_Score'] = np.where(
                client_velocity['Avg_Stage_Duration'] <= 30, 100,
                np.where(client_velocity['Avg_Stage_Duration'] <= 60, 75,
                np.where(client_velocity['Avg_Stage_Duration'] <= 90, 50, 25))
            )
            
            # Recent engagement (clients active in last 6 months)
            recent_clients = client_velocity[client_velocity['Days_Since_Last_Deal'] <= 180]
            
            # High velocity clients (fast stage progression)
            high_velocity = client_velocity[client_velocity['Velocity_Score'] >= 75]
            
            velocity_analysis = {
                'total_clients_analyzed': len(client_velocity),
                'avg_stage_duration': client_velocity['Avg_Stage_Duration'].mean(),
                'recent_engagement_count': len(recent_clients),
                'high_velocity_count': len(high_velocity),
                'avg_velocity_score': client_velocity['Velocity_Score'].mean(),
                'client_velocity_details': client_velocity.to_dict('records'),
                'recent_clients': recent_clients.to_dict('records'),
                'high_velocity_clients': high_velocity.to_dict('records')
            }
            
            logger.info(f"Calculated engagement velocity for {len(client_velocity)} clients")
            return velocity_analysis
            
        except Exception as e:
            logger.error(f"Error calculating engagement velocity: {str(e)}")
            return {'total_clients_analyzed': 0, 'avg_stage_duration': 0, 'avg_velocity_score': 0}
    
    def segment_by_industry_and_size(self, deals_df: pd.DataFrame) -> Dict[str, Any]:
        """Segment clients by industry type and deal size."""
        try:
            # Create size categories
            deals_df['Deal_Size_Category'] = pd.cut(
                deals_df['Deal Amount'],
                bins=[0, 10000, 50000, 100000, float('inf')],
                labels=['Small', 'Medium', 'Large', 'Enterprise']
            )
            
            # Segment by industry and size
            industry_size_segments = deals_df.groupby(['Industry_Type', 'Deal_Size_Category']).agg({
                'Project name': 'nunique',
                'Deal Amount': ['sum', 'mean', 'count'],
                'Deal ID': 'count'
            }).reset_index()
            
            industry_size_segments.columns = [
                'Industry_Type', 'Deal_Size_Category', 'Unique_Clients', 'Total_Revenue',
                'Avg_Deal_Size', 'Deal_Count', 'Total_Deals'
            ]
            
            # Top performing segments
            top_segments = industry_size_segments.nlargest(10, 'Total_Revenue')
            
            # Industry analysis
            industry_analysis = deals_df.groupby('Industry_Type').agg({
                'Project name': 'nunique',
                'Deal Amount': ['sum', 'mean'],
                'Deal ID': 'count'
            }).reset_index()
            
            industry_analysis.columns = [
                'Industry_Type', 'Client_Count', 'Total_Revenue', 'Avg_Deal_Size', 'Deal_Count'
            ]
            
            # Size analysis
            size_analysis = deals_df.groupby('Deal_Size_Category').agg({
                'Project name': 'nunique',
                'Deal Amount': ['sum', 'mean'],
                'Deal ID': 'count'
            }).reset_index()
            
            size_analysis.columns = [
                'Deal_Size_Category', 'Client_Count', 'Total_Revenue', 'Avg_Deal_Size', 'Deal_Count'
            ]
            
            segmentation = {
                'industry_size_segments': industry_size_segments.to_dict('records'),
                'top_segments': top_segments.to_dict('records'),
                'industry_analysis': industry_analysis.to_dict('records'),
                'size_analysis': size_analysis.to_dict('records'),
                'total_segments': len(industry_size_segments),
                'top_industry': industry_analysis.loc[industry_analysis['Total_Revenue'].idxmax(), 'Industry_Type'] if len(industry_analysis) > 0 else 'Unknown',
                'top_size_category': size_analysis.loc[size_analysis['Total_Revenue'].idxmax(), 'Deal_Size_Category'] if len(size_analysis) > 0 else 'Unknown'
            }
            
            logger.info(f"Created {len(industry_size_segments)} industry-size segments")
            return segmentation
            
        except Exception as e:
            logger.error(f"Error in industry-size segmentation: {str(e)}")
            return {'total_segments': 0, 'industry_size_segments': []}
    
    def segment_by_behavior(self, deals_df: pd.DataFrame, stage_df: pd.DataFrame) -> Dict[str, Any]:
        """Segment clients by behavioral patterns."""
        try:
            # Merge data for behavioral analysis
            merged_df = pd.merge(
                deals_df[['Deal ID', 'Project name', 'Deal Amount', 'Deal_Closing_Date', 'Stage']],
                stage_df[['Deal ID', 'Stage Duration Days', 'Stage Group']],
                on='Deal ID',
                how='left'
            )
            
            # Calculate behavioral metrics by client
            client_behavior = merged_df.groupby('Project name').agg({
                'Deal Amount': ['sum', 'count', 'mean'],
                'Stage Duration Days': 'mean',
                'Deal_Closing_Date': ['min', 'max'],
                'Stage Group': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown'
            }).reset_index()
            
            client_behavior.columns = [
                'Client_Name', 'Total_Revenue', 'Deal_Count', 'Avg_Deal_Size',
                'Avg_Stage_Duration', 'First_Deal_Date', 'Last_Deal_Date', 'Preferred_Stage_Group'
            ]
            
            # Calculate behavioral scores
            client_behavior['Revenue_Growth'] = client_behavior['Total_Revenue'] / client_behavior['Deal_Count']
            client_behavior['Deal_Frequency'] = client_behavior['Deal_Count']
            client_behavior['Stage_Efficiency'] = 100 - (client_behavior['Avg_Stage_Duration'] / 365 * 100)
            
            # Behavioral segments
            # High-value frequent buyers
            high_value_frequent = client_behavior[
                (client_behavior['Total_Revenue'] >= client_behavior['Total_Revenue'].quantile(0.7)) &
                (client_behavior['Deal_Count'] >= 2)
            ]
            
            # Quick converters
            quick_converters = client_behavior[
                client_behavior['Avg_Stage_Duration'] <= client_behavior['Avg_Stage_Duration'].quantile(0.3)
            ]
            
            # Large deal specialists
            large_deal_specialists = client_behavior[
                client_behavior['Avg_Deal_Size'] >= client_behavior['Avg_Deal_Size'].quantile(0.8)
            ]
            
            # One-time buyers
            one_time_buyers = client_behavior[client_behavior['Deal_Count'] == 1]
            
            behavioral_segments = {
                'high_value_frequent': len(high_value_frequent),
                'quick_converters': len(quick_converters),
                'large_deal_specialists': len(large_deal_specialists),
                'one_time_buyers': len(one_time_buyers),
                'total_clients_analyzed': len(client_behavior),
                'high_value_frequent_details': high_value_frequent.to_dict('records'),
                'quick_converters_details': quick_converters.to_dict('records'),
                'large_deal_specialists_details': large_deal_specialists.to_dict('records'),
                'one_time_buyers_details': one_time_buyers.to_dict('records'),
                'avg_deal_frequency': client_behavior['Deal_Count'].mean(),
                'avg_stage_efficiency': client_behavior['Stage_Efficiency'].mean()
            }
            
            logger.info(f"Created behavioral segments for {len(client_behavior)} clients")
            return behavioral_segments
            
        except Exception as e:
            logger.error(f"Error in behavioral segmentation: {str(e)}")
            return {'total_clients_analyzed': 0, 'avg_deal_frequency': 0}
    
    def detect_anomalies(self, retention_scores: pd.DataFrame, deals_df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalous client behavior patterns."""
        try:
            # Prepare features for anomaly detection
            features = retention_scores[['Retention_Score', 'Churn_Risk_Score', 'Deal_Count', 'Total_Revenue']].fillna(0)
            
            # Detect anomalies
            anomalies = self.anomaly_detector.detect_anomalies(features)
            
            # Get anomalous clients
            anomalous_clients = retention_scores[anomalies['anomaly_indices']].copy()
            anomalous_clients['Anomaly_Score'] = anomalies['anomaly_scores']
            anomalous_clients['Anomaly_Type'] = 'Unusual_Behavior'
            
            # Add specific anomaly types
            anomalous_clients['Anomaly_Type'] = np.where(
                (anomalous_clients['Churn_Risk_Score'] > 80) & (anomalous_clients['Deal_Count'] > 1),
                'High_Churn_Risk_Repeat_Client',
                np.where(
                    anomalous_clients['Total_Revenue'] > anomalous_clients['Total_Revenue'].quantile(0.9),
                    'High_Revenue_Anomaly',
                    np.where(
                        anomalous_clients['Deal_Count'] > anomalous_clients['Deal_Count'].quantile(0.9),
                        'High_Frequency_Anomaly',
                        'General_Anomaly'
                    )
                )
            )
            
            # Sort by anomaly score
            anomalous_clients = anomalous_clients.sort_values('Anomaly_Score', ascending=False)
            
            anomaly_analysis = {
                'total_anomalies': len(anomalous_clients),
                'high_risk_anomalies': len(anomalous_clients[anomalous_clients['Churn_Risk_Score'] > 70]),
                'anomaly_details': anomalous_clients.head(20).to_dict('records'),
                'anomaly_types': anomalous_clients['Anomaly_Type'].value_counts().to_dict(),
                'avg_anomaly_score': anomalous_clients['Anomaly_Score'].mean() if len(anomalous_clients) > 0 else 0
            }
            
            logger.info(f"Detected {len(anomalous_clients)} anomalous client behaviors")
            return anomaly_analysis
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return {'total_anomalies': 0, 'anomaly_details': []}
    
    def generate_retention_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive retention analysis."""
        try:
            logger.info("Starting client retention analysis...")
            
            # Load data
            deals_df = self.load_deals_data()
            stage_df = self.load_stage_history_data()
            whizible_df = self.load_whizible_data()
            
            # Preprocess data
            deals_clean = self.preprocess_deals_data(deals_df)
            stage_clean = self.preprocess_stage_history_data(stage_df)
            
            # Calculate retention scores
            retention_scores = self.calculate_client_retention_score(deals_clean)
            
            # Identify repeat clients
            repeat_analysis = self.identify_repeat_clients(deals_clean)
            
            # Calculate engagement velocity
            velocity_analysis = self.calculate_engagement_velocity(deals_clean, stage_clean)
            
            # Segment clients
            industry_segmentation = self.segment_by_industry_and_size(deals_clean)
            behavioral_segmentation = self.segment_by_behavior(deals_clean, stage_clean)
            
            # Detect anomalies
            anomaly_analysis = self.detect_anomalies(retention_scores, deals_clean)
            
            # Generate summary metrics
            total_clients = len(retention_scores)
            at_risk_clients = len(retention_scores[retention_scores['Churn_Risk_Score'] > 70])
            high_value_clients = len(retention_scores[retention_scores['Total_Revenue'] > retention_scores['Total_Revenue'].quantile(0.8)])
            
            # Top at-risk clients
            top_at_risk = retention_scores.nlargest(10, 'Churn_Risk_Score')[
                ['Client_Name', 'Churn_Risk_Score', 'Days_Since_Last_Activity', 'Deal_Count', 'Total_Revenue', 'Industry_Type']
            ].to_dict('records')
            
            retention_summary = {
                "total_clients_analyzed": int(total_clients),
                "at_risk_clients": int(at_risk_clients),
                "high_value_clients": int(high_value_clients),
                "repeat_business_rate": self._clean_float(repeat_analysis.get('repeat_rate', 0)),
                "avg_time_between_deals": self._clean_float(repeat_analysis.get('avg_time_between_deals', 0)),
                "avg_retention_score": self._clean_float(retention_scores['Retention_Score'].mean()),
                "avg_churn_risk": self._clean_float(retention_scores['Churn_Risk_Score'].mean()),
                "top_at_risk_clients": self._clean_for_json(top_at_risk)
            }
            
            logger.info("Client retention analysis completed successfully")
            
            return {
                "retention_summary": retention_summary,
                "segmentation_analysis": {
                    "by_industry_size": self._clean_for_json(industry_segmentation),
                    "by_behavior": self._clean_for_json(behavioral_segmentation)
                },
                "at_risk_clients": self._clean_for_json(top_at_risk),
                "repeat_patterns": self._clean_for_json(repeat_analysis),
                "engagement_velocity": self._clean_for_json(velocity_analysis),
                "anomalies": self._clean_for_json(anomaly_analysis),
                "data_summary": {
                    "deals_records": int(len(deals_clean)),
                    "stage_records": int(len(stage_clean)),
                    "whizible_records": int(len(whizible_df)) if not whizible_df.empty else 0,
                    "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating retention analysis: {str(e)}")
            raise Exception(f"Retention analysis generation failed: {str(e)}")
    
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
