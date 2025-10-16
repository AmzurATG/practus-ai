from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif pd.isna(obj):
        return None
    else:
        return obj

# Class-level cache for shared analysis across instances
_global_funnel_cache = None

def clear_funnel_cache():
    """Clear the global funnel cache to force regeneration."""
    global _global_funnel_cache
_global_funnel_cache = None

class FunnelAnalysisService:
    """Service for analyzing deal funnel performance and conversion rates."""
    
    def __init__(self):
        # Use data/ directory instead of root directory
        self.data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')
        self.stage_file = os.path.join(self.data_path, "Stage History Archive.csv")
        self.deals_file = os.path.join(self.data_path, "Deals Archive.csv")
        self.stage_df = None
        self.deals_df = None
        self._cached_analysis = None
        self._load_data()
    
    def _load_data(self):
        """Load stage history and deals data from CSV files."""
        try:
            self.stage_df, self.deals_df = self.load_stage_data()
            if self.stage_df is not None and not self.stage_df.empty:
                logger.info(f"Loaded {len(self.stage_df)} stage records and {len(self.deals_df) if self.deals_df is not None else 0} deal records")
            else:
                logger.warning("Stage data is empty or not loaded")
        except Exception as e:
            logger.error(f"Error during initial data load: {e}")
    
    def load_stage_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load stage history and deals data from data directory CSV files."""
        stage_df = None
        deals_df = None
        
        # Use the configured data paths
        stage_path = self.stage_file
        deals_path = self.deals_file
        
        try:
            stage_df = pd.read_csv(stage_path)
            logger.info(f"Loaded Stage History Archive from: {stage_path}")
        except FileNotFoundError:
            logger.error(f"Stage History Archive not found at {stage_path}")
        except Exception as e:
            logger.error(f"Error loading Stage History Archive: {e}")
        
        try:
            deals_df = pd.read_csv(deals_path)
            logger.info(f"Loaded Deals Archive from: {deals_path}")
        except FileNotFoundError:
            logger.error(f"Deals Archive not found at {deals_path}")
        except Exception as e:
            logger.error(f"Error loading Deals Archive: {e}")
        
        return stage_df, deals_df
    
    def generate_funnel_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive funnel analysis with conversion metrics."""
        global _global_funnel_cache
        
        # Return global cached analysis if available
        if _global_funnel_cache is not None:
            logger.info("Returning global cached funnel analysis")
            return _global_funnel_cache
        
        # Return instance cached analysis if available
        if self._cached_analysis is not None:
            logger.info("Returning instance cached funnel analysis")
            return self._cached_analysis
        
        if self.stage_df is None or self.stage_df.empty:
            return self._get_empty_funnel_data()
        
        try:
            logger.info("Generating new funnel analysis (will be cached globally)")
            
            # Calculate core funnel metrics
            funnel_metrics = self.calculate_funnel_metrics()
            duration_analysis = self.analyze_stage_duration()
            stuck_deals = self.find_stuck_deals()
            segment_analysis = self.segment_analysis()
            early_stage_metrics = self.calculate_early_stage_metrics()
            
            # Generate summary for LLM context
            summary = self.generate_funnel_summary(funnel_metrics, duration_analysis, stuck_deals)
            
            # Create analysis result
            analysis_result = {
                "summary": summary,
                "conversions": funnel_metrics,
                "durations": duration_analysis,
                "stuck_deals": stuck_deals,
                "segments": segment_analysis,
                "early_stage_metrics": early_stage_metrics
            }
            
            # Convert numpy types to native Python types for JSON serialization
            analysis_result = convert_numpy_types(analysis_result)
            
            # Cache at both instance and global level
            self._cached_analysis = analysis_result
            _global_funnel_cache = analysis_result
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error generating funnel analysis: {e}")
            return self._get_empty_funnel_data()
    
    @classmethod
    def clear_cache(cls):
        """Clear the global funnel analysis cache."""
        global _global_funnel_cache
        _global_funnel_cache = None
        logger.info("Global funnel analysis cache cleared")
    
    def calculate_funnel_metrics(self) -> Dict[str, Any]:
        """Calculate stage-by-stage conversion rates and funnel metrics."""
        if self.stage_df is None or self.stage_df.empty:
            return {}
        
        df = self.stage_df.copy()
        
        # Clean and prepare data
        df['Modified_Time'] = pd.to_datetime(df['Modified_Time'], errors='coerce')
        df['Stage Duration Days'] = pd.to_numeric(df['Stage Duration Days'], errors='coerce')
        df['Deal Amount'] = pd.to_numeric(df['Deal Amount'], errors='coerce')
        
        # Sort by Deal ID and Modified_Time to track progression
        df = df.sort_values(['Deal ID', 'Modified_Time'])
        
        # Calculate overall conversion rate (Lead to Won) based on unique deals
        # Get the latest stage for each unique deal
        latest_stages = df.sort_values(['Deal ID', 'Modified_Time']).groupby('Deal ID').tail(1)
        
        # Count unique deals in each category
        total_leads = len(latest_stages[latest_stages['Stage'].str.contains('Lead', case=False, na=False)])
        total_won = len(latest_stages[latest_stages['Stage'].str.contains('Client Won', case=False, na=False)])
        total_lost = len(latest_stages[latest_stages['Stage'].str.contains('Client Lost', case=False, na=False)])
        
        # Overall conversion rate: Won deals / Total leads
        overall_conversion = (total_won / total_leads * 100) if total_leads > 0 else 0
        
        # Track stage transitions
        stage_transitions = self._track_stage_transitions(df)
        
        # Calculate funnel groups
        funnel_groups = self._calculate_funnel_groups(df)
        
        result = {
            "overall_conversion_rate": round(overall_conversion, 1),
            "total_leads": total_leads,
            "total_won": total_won,
            "total_lost": total_lost,
            "stage_conversions": stage_transitions,
            "funnel_groups": funnel_groups
        }
        
        # Convert numpy types to native Python types
        return convert_numpy_types(result)
    
    def _track_stage_transitions(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Track actual stage transitions for each deal."""
        transitions = []
        
        # Define stage progression order
        stage_order = {
            'Lead': 1,
            'Proposal': 2,
            'Negotiation': 3,
            'Client Won': 4,
            'Client Lost': 4
        }
        
        # Group by Deal ID and track progression
        for deal_id, group in df.groupby('Deal ID'):
            group = group.sort_values('Modified_Time')
            stages = group['Stage'].tolist()
            
            # Track transitions
            for i in range(len(stages) - 1):
                from_stage = stages[i]
                to_stage = stages[i + 1]
                
                # Only track forward progressions
                if (stage_order.get(from_stage, 0) < stage_order.get(to_stage, 0)):
                    transitions.append({
                        'from': from_stage,
                        'to': to_stage,
                        'deal_id': deal_id
                    })
        
        # Calculate conversion rates for each transition
        transition_summary = []
        transition_counts = {}
        
        for trans in transitions:
            key = f"{trans['from']} → {trans['to']}"
            if key not in transition_counts:
                transition_counts[key] = {'moved': 0, 'total': 0}
            transition_counts[key]['moved'] += 1
        
        # Count total deals in each starting stage
        for stage in df['Stage'].unique():
            stage_deals = len(df[df['Stage'] == stage])
            for key in transition_counts:
                if key.startswith(stage):
                    transition_counts[key]['total'] = stage_deals
        
        # Calculate conversion rates
        for key, counts in transition_counts.items():
            if counts['total'] > 0:
                rate = (counts['moved'] / counts['total']) * 100
                transition_summary.append({
                    'transition': key,
                    'rate': round(rate, 1),
                    'deals_moved': counts['moved'],
                    'deals_total': counts['total'],
                    'deals_dropped': counts['total'] - counts['moved']
                })
        
        # Convert numpy types to native Python types
        return convert_numpy_types(transition_summary)
    
    def calculate_early_stage_metrics(self) -> Dict[str, Any]:
        """Calculate metrics specific to leads stuck in early stages."""
        
        try:
            df = self.stage_df.copy()
            
            # Check if required columns exist
            required_columns = ['Stage', 'Modified_Time', 'Deal Amount', 'Deal ID']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                logger.info(f"Available columns: {list(df.columns)}")
                return self._get_empty_early_stage_metrics()
            
            # 1. Lead Contact Success Rate
            attempt_count = len(df[df['Stage'].str.contains('Attempt to Contact', na=False)])
            able_count = len(df[df['Stage'].str.contains('Able to Contact', na=False)])
            contact_success_rate = (able_count / attempt_count * 100) if attempt_count > 0 else 0
            
            # 2. Lead Aging Distribution
            df['Modified_Time'] = pd.to_datetime(df['Modified_Time'], errors='coerce')
            current_date = datetime.now()
            df['Lead_Age_Days'] = (current_date - df['Modified_Time']).dt.days
            
            aging_buckets = {
                'fresh_0_7_days': len(df[df['Lead_Age_Days'] <= 7]),
                'warm_8_30_days': len(df[(df['Lead_Age_Days'] > 7) & (df['Lead_Age_Days'] <= 30)]),
                'cold_31_90_days': len(df[(df['Lead_Age_Days'] > 30) & (df['Lead_Age_Days'] <= 90)]),
                'stale_91_180_days': len(df[(df['Lead_Age_Days'] > 90) & (df['Lead_Age_Days'] <= 180)]),
                'dead_180_plus_days': len(df[df['Lead_Age_Days'] > 180])
            }
            
            # 3. Revenue at Risk by Aging Bucket
            df['Deal Amount'] = pd.to_numeric(df['Deal Amount'], errors='coerce')
            revenue_by_age = {
                'fresh_revenue': df[df['Lead_Age_Days'] <= 7]['Deal Amount'].sum(),
                'warm_revenue': df[(df['Lead_Age_Days'] > 7) & (df['Lead_Age_Days'] <= 30)]['Deal Amount'].sum(),
                'cold_revenue': df[(df['Lead_Age_Days'] > 30) & (df['Lead_Age_Days'] <= 90)]['Deal Amount'].sum(),
                'stale_revenue': df[(df['Lead_Age_Days'] > 90) & (df['Lead_Age_Days'] <= 180)]['Deal Amount'].sum(),
                'dead_revenue': df[df['Lead_Age_Days'] > 180]['Deal Amount'].sum()
            }
            
            # 4. Top Value Leads by Contact Status
            contactable_leads = df[df['Stage'].str.contains('Able to Contact', na=False)].nlargest(20, 'Deal Amount')
            stuck_leads = df[df['Stage'].str.contains('Attempt to Contact', na=False)].nlargest(20, 'Deal Amount')
            
            result = {
                'contact_success_rate': round(contact_success_rate, 1),
                'attempt_count': attempt_count,
                'able_count': able_count,
                'aging_distribution': aging_buckets,
                'revenue_by_age': revenue_by_age,
                'total_revenue_at_risk': df['Deal Amount'].sum(),
                'average_lead_age': round(df['Lead_Age_Days'].mean(), 0),
                'top_contactable_leads': contactable_leads[['Deal ID', 'Deal Amount', 'Lead_Age_Days']].to_dict('records'),
                'top_stuck_leads': stuck_leads[['Deal ID', 'Deal Amount', 'Lead_Age_Days']].to_dict('records')
            }
            
            # Convert numpy types to native Python types
            return convert_numpy_types(result)
            
        except Exception as e:
            logger.error(f"Error in calculate_early_stage_metrics: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._get_empty_early_stage_metrics()
    
    def _get_empty_early_stage_metrics(self) -> Dict[str, Any]:
        """Return empty early stage metrics when data is not available."""
        return {
            'contact_success_rate': 0,
            'attempt_count': 0,
            'able_count': 0,
            'aging_distribution': {
                'fresh_0_7_days': 0,
                'warm_8_30_days': 0,
                'cold_31_90_days': 0,
                'stale_91_180_days': 0,
                'dead_180_plus_days': 0
            },
            'revenue_by_age': {
                'fresh_revenue': 0,
                'warm_revenue': 0,
                'cold_revenue': 0,
                'stale_revenue': 0,
                'dead_revenue': 0
            },
            'total_revenue_at_risk': 0,
            'average_lead_age': 0,
            'top_contactable_leads': [],
            'top_stuck_leads': []
        }
    
    def _calculate_funnel_groups(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate conversion rates for funnel groups based on unique deals."""
        # Get the latest stage for each unique deal
        latest_stages = df.sort_values(['Deal ID', 'Modified_Time']).groupby('Deal ID').tail(1)
        
        # Count unique deals currently in each stage category
        early_count = len(latest_stages[latest_stages['Stage'].str.contains('Lead', case=False, na=False)])
        mid_count = len(latest_stages[latest_stages['Stage'].str.contains('Proposal|Negotiation|Qualified|Prospect', case=False, na=False)])
        late_count = len(latest_stages[latest_stages['Stage'].str.contains('Client Won|Client Lost', case=False, na=False)])
        
        # Calculate average duration for each group (from all records, not just latest)
        early_duration = df[df['Stage'].str.contains('Lead', case=False, na=False)]['Stage Duration Days'].mean() if early_count > 0 else 0
        mid_duration = df[df['Stage'].str.contains('Proposal|Negotiation|Qualified|Prospect', case=False, na=False)]['Stage Duration Days'].mean() if mid_count > 0 else 0
        late_duration = df[df['Stage'].str.contains('Client Won|Client Lost', case=False, na=False)]['Stage Duration Days'].mean() if late_count > 0 else 0
        
        # Calculate conversion rates based on current stage distribution
        # This shows the current state of the funnel, not historical progression
        total_deals = early_count + mid_count + late_count
        
        # Early to Mid: Percentage of deals that have progressed beyond early stages
        early_to_mid_conversion = round(((mid_count + late_count) / total_deals * 100) if total_deals > 0 else 0, 1)
        
        # Mid to Late: Percentage of non-early deals that have reached late stages
        mid_to_late_conversion = round((late_count / (mid_count + late_count) * 100) if (mid_count + late_count) > 0 else 0, 1)
        
        # Late stage: All deals that reach late stage are "converted" (either won or lost)
        late_conversion = 100.0 if late_count > 0 else 0
        
        result = {
            "early_funnel": {
                "conversion": early_to_mid_conversion,
                "count": int(early_count),
                "avg_duration": round(early_duration, 1)
            },
            "mid_funnel": {
                "conversion": mid_to_late_conversion,
                "count": int(mid_count),
                "avg_duration": round(mid_duration, 1)
            },
            "late_funnel": {
                "conversion": late_conversion,
                "count": int(late_count),
                "avg_duration": round(late_duration, 1)
            }
        }
        
        # Convert numpy types to native Python types
        return convert_numpy_types(result)
    
    def analyze_stage_duration(self) -> Dict[str, Any]:
        """Analyze average, median, and max duration for each stage."""
        if self.stage_df is None or self.stage_df.empty:
            return {}
        
        df = self.stage_df.copy()
        df['Stage Duration Days'] = pd.to_numeric(df['Stage Duration Days'], errors='coerce')
        
        duration_stats = {}
        
        for stage in df['Stage'].unique():
            stage_data = df[df['Stage'] == stage]['Stage Duration Days'].dropna()
            if len(stage_data) > 0:
                duration_stats[stage] = {
                    "avg": round(stage_data.mean(), 1),
                    "median": round(stage_data.median(), 1),
                    "max": round(stage_data.max(), 1),
                    "count": len(stage_data)
                }
        
        # Convert numpy types to native Python types
        return convert_numpy_types(duration_stats)
    
    def find_stuck_deals(self) -> List[Dict[str, Any]]:
        """Find deals that haven't moved for 30+ days."""
        if self.stage_df is None or self.stage_df.empty:
            return []
        
        df = self.stage_df.copy()
        df['Modified_Time'] = pd.to_datetime(df['Modified_Time'], errors='coerce')
        df['Deal Amount'] = pd.to_numeric(df['Deal Amount'], errors='coerce')
        
        current_time = datetime.now()
        stuck_deals = []
        
        # Group by Deal ID and find the latest stage for each deal
        for deal_id, group in df.groupby('Deal ID'):
            latest_stage = group.loc[group['Modified_Time'].idxmax()]
            
            # Check if deal is stuck (not moved for 30+ days)
            days_since_update = (current_time - latest_stage['Modified_Time']).days
            
            if days_since_update > 30:
                # Skip if it's already won or lost
                stage_name = str(latest_stage['Stage']).lower()
                if 'client won' not in stage_name and 'client lost' not in stage_name:
                    stuck_deals.append({
                        "deal_id": str(deal_id),
                        "stage": latest_stage['Stage'],
                        "days_stuck": days_since_update,
                        "amount": float(latest_stage['Deal Amount']) if pd.notna(latest_stage['Deal Amount']) else 0,
                        "last_activity": latest_stage['Modified_Time'].strftime('%Y-%m-%d')
                    })
        
        # Sort by amount descending
        stuck_deals.sort(key=lambda x: x["amount"], reverse=True)
        
        # Convert numpy types to native Python types and return top 20 stuck deals
        return convert_numpy_types(stuck_deals[:20])
    
    def segment_analysis(self) -> Dict[str, Any]:
        """Analyze drop-off patterns by deal size, industry, etc."""
        if self.stage_df is None or self.stage_df.empty or self.deals_df is None or self.deals_df.empty:
            return {}
        
        try:
            # Check if required columns exist in deals data
            required_deals_columns = ['Deal ID', 'Deal Amount', 'Industry_Type', 'Client_Type']
            missing_deals_columns = [col for col in required_deals_columns if col not in self.deals_df.columns]
            if missing_deals_columns:
                logger.error(f"Missing required columns in deals data: {missing_deals_columns}")
                logger.info(f"Available columns in deals data: {list(self.deals_df.columns)}")
                return {}
            
            # Merge stage and deals data
            merged_df = pd.merge(
                self.stage_df, 
                self.deals_df[['Deal ID', 'Deal Amount', 'Industry_Type', 'Client_Type']], 
                on='Deal ID', 
                how='left'
            )
            
            merged_df['Deal Amount'] = pd.to_numeric(merged_df['Deal Amount'], errors='coerce')
            
            segments = {}
            
            # Analyze by deal size
            large_deals = merged_df[merged_df['Deal Amount'] > 1000000]  # > ₹1M
            small_deals = merged_df[merged_df['Deal Amount'] <= 1000000]
            
            if len(large_deals) > 0:
                large_won = len(large_deals[large_deals['Stage'].str.contains('Client Won', case=False, na=False)])
                segments['large_deals'] = {
                    "conversion": round((large_won / len(large_deals) * 100), 1),
                    "count": len(large_deals),
                    "avg_amount": round(large_deals['Deal Amount'].mean(), 0)
                }
            
            if len(small_deals) > 0:
                small_won = len(small_deals[small_deals['Stage'].str.contains('Client Won', case=False, na=False)])
                segments['small_deals'] = {
                    "conversion": round((small_won / len(small_deals) * 100), 1),
                    "count": len(small_deals),
                    "avg_amount": round(small_deals['Deal Amount'].mean(), 0)
                }
            
            # Analyze by industry
            if 'Industry_Type' in merged_df.columns:
                industry_analysis = {}
                for industry in merged_df['Industry_Type'].value_counts().head(5).index:
                    if pd.notna(industry):
                        industry_deals = merged_df[merged_df['Industry_Type'] == industry]
                        industry_won = len(industry_deals[industry_deals['Stage'].str.contains('Client Won', case=False, na=False)])
                        industry_analysis[industry] = {
                            "conversion": round((industry_won / len(industry_deals) * 100), 1),
                            "count": len(industry_deals)
                        }
                segments['by_industry'] = industry_analysis
            
            # Convert numpy types to native Python types
            return convert_numpy_types(segments)
            
        except Exception as e:
            logger.error(f"Error in segment_analysis merge: {e}")
            return {}
    
    def generate_funnel_summary(self, funnel_metrics: Dict, duration_analysis: Dict, stuck_deals: List) -> Dict[str, Any]:
        """Generate executive summary for LLM context."""
        # Find biggest bottleneck
        biggest_dropoff = ""
        lowest_conversion = 100
        
        for conversion in funnel_metrics.get('stage_conversions', []):
            if conversion['rate'] < lowest_conversion:
                lowest_conversion = conversion['rate']
                biggest_dropoff = conversion['transition']
        
        # Calculate average sales cycle
        total_duration = 0
        total_count = 0
        for stage, stats in duration_analysis.items():
            if 'avg' in stats:
                total_duration += stats['avg'] * stats['count']
                total_count += stats['count']
        
        avg_sales_cycle = round(total_duration / total_count, 1) if total_count > 0 else 0
        
        # Get total active deals from stage data if funnel metrics shows 0
        total_active_deals = funnel_metrics.get('total_leads', 0)
        if total_active_deals == 0 and self.stage_df is not None and not self.stage_df.empty:
            # Count unique deals in the stage data
            total_active_deals = self.stage_df['Deal ID'].nunique()
        
        result = {
            "overall_conversion_rate": funnel_metrics.get('overall_conversion_rate', 0),
            "total_active_deals": total_active_deals,
            "avg_sales_cycle_days": avg_sales_cycle,
            "top_bottleneck": f"{biggest_dropoff} ({lowest_conversion}% conversion)" if biggest_dropoff else "Lead Stage Stagnation",
            "stuck_deals_count": len(stuck_deals),
            "total_stuck_value": sum(deal['amount'] for deal in stuck_deals),
            "analysis_methods": {
                "conversion_analysis": "Statistical Funnel Analysis",
                "duration_analysis": "Time Series Analysis with Percentiles",
                "bottleneck_detection": "Rule-based Risk Scoring",
                "stuck_deal_identification": "Time-based Threshold Analysis",
                "segmentation_analysis": "Multi-dimensional Data Grouping",
                "ai_insights": "Google Gemini LLM with Business Context"
            }
        }
        
        # Convert numpy types to native Python types
        return convert_numpy_types(result)
    
    def _get_empty_funnel_data(self) -> Dict[str, Any]:
        """Return empty funnel data structure."""
        return {
            "summary": {
                "overall_conversion_rate": 0,
                "total_active_deals": 0,
                "avg_sales_cycle_days": 0,
                "top_bottleneck": "No data available",
                "stuck_deals_count": 0,
                "total_stuck_value": 0,
                "analysis_methods": {
                    "conversion_analysis": "Statistical Funnel Analysis",
                    "duration_analysis": "Time Series Analysis with Percentiles",
                    "bottleneck_detection": "Rule-based Risk Scoring",
                    "stuck_deal_identification": "Time-based Threshold Analysis",
                    "segmentation_analysis": "Multi-dimensional Data Grouping",
                    "ai_insights": "Google Gemini LLM with Business Context"
                }
            },
            "conversions": {
                "overall_conversion_rate": 0,
                "total_leads": 0,
                "total_won": 0,
                "stage_conversions": [],
                "funnel_groups": {
                    "early_funnel": {"conversion": 0, "count": 0, "avg_duration": 0},
                    "mid_funnel": {"conversion": 0, "count": 0, "avg_duration": 0},
                    "late_funnel": {"conversion": 0, "count": 0, "avg_duration": 0}
                }
            },
            "durations": {},
            "stuck_deals": [],
            "segments": {}
        }
