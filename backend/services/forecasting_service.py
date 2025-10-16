from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import logging
from prophet import Prophet
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_percentage_error
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class RevenueForecastingService:
    """
    Revenue forecasting service using Prophet and statistical baselines.
    Generates forecasts and actionable insights for revenue planning.
    """
    
    def __init__(self):
        # Use data/ directory instead of root directory
        self.data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')
        self.deals_file = os.path.join(self.data_path, 'Deals Archive.csv')
        self.stage_file = os.path.join(self.data_path, 'Stage History Archive.csv')
        
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load deals and stage history data from root directory."""
        try:
            # Load deals data
            deals_df = pd.read_csv(self.deals_file)
            logger.info(f"Loaded deals data: {len(deals_df)} records")
            
            # Load stage history data
            stage_df = pd.read_csv(self.stage_file)
            logger.info(f"Loaded stage data: {len(stage_df)} records")
            
            return deals_df, stage_df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise Exception(f"Failed to load data files: {str(e)}")
    
    def preprocess_data(self, deals_df: pd.DataFrame, stage_df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess and clean the data for forecasting."""
        try:
            # Clean deals data
            deals_df['Deal Amount'] = pd.to_numeric(deals_df['Deal Amount'], errors='coerce')
            deals_df['Deal_Closing_Date'] = pd.to_datetime(deals_df['Deal_Closing_Date'], errors='coerce')
            deals_df['Created_Time'] = pd.to_datetime(deals_df['Created_Time'], errors='coerce')
            deals_df['Modified_Time'] = pd.to_datetime(deals_df['Modified_Time'], errors='coerce')
            
            # Filter for won deals only
            won_deals = deals_df[
                (deals_df['Stage'].str.contains('Won', case=False, na=False)) &
                (deals_df['Deal Amount'] > 0) &
                (deals_df['Deal_Closing_Date'].notna())
            ].copy()
            
            if len(won_deals) == 0:
                logger.warning("No won deals found, using all deals with amounts > 0")
                won_deals = deals_df[
                    (deals_df['Deal Amount'] > 0) &
                    (deals_df['Deal_Closing_Date'].notna())
                ].copy()
            
            # Create Prophet format
            won_deals['ds'] = won_deals['Deal_Closing_Date']
            won_deals['y'] = won_deals['Deal Amount']
            
            # Remove outliers (deals > 3 standard deviations)
            mean_amount = won_deals['y'].mean()
            std_amount = won_deals['y'].std()
            won_deals = won_deals[won_deals['y'] <= mean_amount + 3 * std_amount]
            
            logger.info(f"Preprocessed data: {len(won_deals)} valid deals for forecasting")
            return won_deals
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {str(e)}")
            raise Exception(f"Failed to preprocess data: {str(e)}")
    
    def create_baseline_forecast(self, data: pd.DataFrame) -> Dict[str, float]:
        """Create a simple statistical baseline forecast."""
        try:
            # Group by month and sum revenue
            data['month'] = data['ds'].dt.to_period('M')
            monthly_revenue = data.groupby('month')['y'].sum().reset_index()
            monthly_revenue['month'] = monthly_revenue['month'].dt.to_timestamp()
            
            if len(monthly_revenue) < 3:
                # Not enough data for baseline
                return {
                    "next_3_months": data['y'].mean() * 3,
                    "next_6_months": data['y'].mean() * 6,
                    "next_12_months": data['y'].mean() * 12,
                    "confidence": 50
                }
            
            # Simple moving average
            recent_months = monthly_revenue.tail(6)  # Last 6 months
            avg_monthly = recent_months['y'].mean()
            
            # Linear trend
            X = np.arange(len(monthly_revenue)).reshape(-1, 1)
            y = monthly_revenue['y'].values
            
            if len(X) > 1:
                model = LinearRegression()
                model.fit(X, y)
                trend = model.coef_[0]
            else:
                trend = 0
            
            # Forecast with trend
            next_3 = avg_monthly * 3 + trend * 3
            next_6 = avg_monthly * 6 + trend * 6
            next_12 = avg_monthly * 12 + trend * 12
            
            return {
                "next_3_months": max(0, next_3),
                "next_6_months": max(0, next_6),
                "next_12_months": max(0, next_12),
                "confidence": 60
            }
            
        except Exception as e:
            logger.error(f"Error creating baseline forecast: {str(e)}")
            # Fallback to simple average
            avg_deal = data['y'].mean()
            return {
                "next_3_months": avg_deal * 3,
                "next_6_months": avg_deal * 6,
                "next_12_months": avg_deal * 12,
                "confidence": 40
            }
    
    def create_prophet_forecast(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Create Prophet-based forecast."""
        try:
            if len(data) < 10:
                logger.warning("Insufficient data for Prophet, using baseline")
                return self.create_baseline_forecast(data)
            
            # Prepare data for Prophet
            prophet_data = data[['ds', 'y']].copy()
            prophet_data = prophet_data.dropna()
            
            # Initialize Prophet model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                interval_width=0.95,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10.0
            )
            
            # Fit the model
            model.fit(prophet_data)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=365, freq='D')
            
            # Make predictions
            forecast = model.predict(future)
            
            # Extract forecasts for specific periods
            today = datetime.now()
            next_3_months = today + timedelta(days=90)
            next_6_months = today + timedelta(days=180)
            next_12_months = today + timedelta(days=365)
            
            # Get forecast values
            forecast_3m = forecast[forecast['ds'] <= next_3_months]['yhat'].sum()
            forecast_6m = forecast[forecast['ds'] <= next_6_months]['yhat'].sum()
            forecast_12m = forecast[forecast['ds'] <= next_12_months]['yhat'].sum()
            
            # Calculate confidence based on historical accuracy
            historical_accuracy = self._calculate_historical_accuracy(model, prophet_data)
            
            return {
                "next_3_months": max(0, forecast_3m),
                "next_6_months": max(0, forecast_6m),
                "next_12_months": max(0, forecast_12m),
                "confidence": historical_accuracy,
                "model_details": {
                    "trend": model.params.get('trend', {}),
                    "seasonality": model.params.get('seasonal', {}),
                    "changepoints": len(model.changepoints) if hasattr(model, 'changepoints') else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating Prophet forecast: {str(e)}")
            return self.create_baseline_forecast(data)
    
    def _calculate_historical_accuracy(self, model: Prophet, data: pd.DataFrame) -> int:
        """Calculate historical accuracy for confidence scoring."""
        try:
            if len(data) < 10:
                return 50
            
            # Use last 20% of data for validation
            split_point = int(len(data) * 0.8)
            train_data = data.iloc[:split_point]
            test_data = data.iloc[split_point:]
            
            if len(train_data) < 5 or len(test_data) < 2:
                return 60
            
            # Train on subset
            temp_model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False
            )
            temp_model.fit(train_data)
            
            # Predict on test data
            future = temp_model.make_future_dataframe(periods=len(test_data))
            forecast = temp_model.predict(future)
            
            # Calculate MAPE
            actual = test_data['y'].values
            predicted = forecast['yhat'].iloc[-len(test_data):].values
            
            mape = mean_absolute_percentage_error(actual, predicted)
            accuracy = max(0, min(100, (1 - mape) * 100))
            
            return int(accuracy)
            
        except Exception as e:
            logger.error(f"Error calculating accuracy: {str(e)}")
            return 70
    
    def calculate_pipeline_metrics(self, deals_df: pd.DataFrame, stage_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate pipeline health and metrics."""
        try:
            # Current pipeline value
            current_deals = deals_df[
                (deals_df['Stage'].str.contains('Lead|Proposal|Negotiation', case=False, na=False)) &
                (deals_df['Deal Amount'] > 0)
            ]
            
            pipeline_value = current_deals['Deal Amount'].sum()
            pipeline_count = len(current_deals)
            
            # Average deal size
            avg_deal_size = current_deals['Deal Amount'].mean() if len(current_deals) > 0 else 0
            
            # Stuck deals (no activity for 30+ days)
            current_date = datetime.now()
            stuck_deals = []
            
            for _, deal in current_deals.iterrows():
                last_activity = deal.get('Modified_Time', deal.get('Created_Time'))
                if pd.notna(last_activity):
                    days_since_activity = (current_date - last_activity).days
                    if days_since_activity > 30:
                        stuck_deals.append({
                            'id': deal.get('Deal ID', 'Unknown'),
                            'amount': deal['Deal Amount'],
                            'days_stuck': days_since_activity,
                            'stage': deal.get('Stage', 'Unknown')
                        })
            
            # Pipeline health score
            health_score = 100
            if len(stuck_deals) > 0:
                health_score -= min(len(stuck_deals) * 5, 40)
            if pipeline_count < 10:
                health_score -= 20
            if avg_deal_size < 100000:  # Less than 1L average
                health_score -= 10
            
            health_score = max(0, min(100, health_score))
            
            return {
                "pipeline_value": pipeline_value,
                "pipeline_count": pipeline_count,
                "avg_deal_size": avg_deal_size,
                "stuck_deals_count": len(stuck_deals),
                "stuck_deals": stuck_deals[:5],  # Top 5
                "health_score": health_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating pipeline metrics: {str(e)}")
            return {
                "pipeline_value": 0,
                "pipeline_count": 0,
                "avg_deal_size": 0,
                "stuck_deals_count": 0,
                "stuck_deals": [],
                "health_score": 50
            }
    
    def generate_forecast(self) -> Dict[str, Any]:
        """Main method to generate complete forecast analysis."""
        try:
            # Load and preprocess data
            deals_df, stage_df = self.load_data()
            processed_data = self.preprocess_data(deals_df, stage_df)
            
            # Generate forecasts
            prophet_forecast = self.create_prophet_forecast(processed_data)
            baseline_forecast = self.create_baseline_forecast(processed_data)
            
            # Calculate pipeline metrics
            pipeline_metrics = self.calculate_pipeline_metrics(deals_df, stage_df)
            
            # Determine which model to use
            if prophet_forecast.get('confidence', 0) > baseline_forecast.get('confidence', 0):
                selected_forecast = prophet_forecast
                model_used = "Prophet"
                model_comparison = f"Prophet is {prophet_forecast.get('confidence', 0) - baseline_forecast.get('confidence', 0)}% more confident than baseline"
            else:
                selected_forecast = baseline_forecast
                model_used = "Statistical Baseline"
                model_comparison = f"Baseline model selected due to insufficient data for Prophet"
            
            # Calculate historical performance
            won_deals_recent = deals_df[
                (deals_df['Deal_Closing_Date'] >= datetime.now() - timedelta(days=90)) &
                (deals_df['Stage'].str.contains('Won', case=False, na=False))
            ]
            
            recent_revenue = won_deals_recent['Deal Amount'].sum()
            recent_deals_count = len(won_deals_recent)
            
            return {
                "forecast_summary": {
                    "next_3_months": selected_forecast.get('next_3_months', 0),
                    "next_6_months": selected_forecast.get('next_6_months', 0),
                    "next_12_months": selected_forecast.get('next_12_months', 0),
                    "confidence": selected_forecast.get('confidence', 0),
                    "model_used": model_used,
                    "baseline_comparison": model_comparison
                },
                "pipeline_metrics": pipeline_metrics,
                "historical_performance": {
                    "recent_revenue_90_days": recent_revenue,
                    "recent_deals_count": recent_deals_count,
                    "avg_deal_size_recent": recent_revenue / max(recent_deals_count, 1)
                },
                "data_summary": {
                    "total_deals_analyzed": len(processed_data),
                    "date_range": {
                        "earliest": processed_data['ds'].min().strftime('%Y-%m-%d'),
                        "latest": processed_data['ds'].max().strftime('%Y-%m-%d')
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}")
            raise Exception(f"Forecast generation failed: {str(e)}")
