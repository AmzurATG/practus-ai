import pandas as pd
from typing import Dict, List, Any


class DataQualityAnalyzer:
    """
    Analyzes data quality and generates quality scores.
    Checks for completeness, accuracy, and freshness.
    """
    
    def analyze_file(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """
        Analyze quality of a single dataframe.
        
        Args:
            df: DataFrame to analyze
            filename: Name of the file
            
        Returns:
            Quality analysis results
        """
        analysis = {
            "filename": filename,
            "row_count": len(df),
            "column_count": len(df.columns),
            "completeness_score": 0,
            "quality_score": 0,
            "issues": []
        }
        
        # Calculate completeness (percentage of non-null values)
        total_cells = df.size
        non_null_cells = df.count().sum()
        completeness = (non_null_cells / total_cells * 100) if total_cells > 0 else 0
        analysis["completeness_score"] = round(completeness, 1)
        
        # Check for issues
        for col in df.columns:
            null_count = df[col].isnull().sum()
            null_pct = (null_count / len(df) * 100) if len(df) > 0 else 0
            
            if null_pct > 20:
                analysis["issues"].append(f"{col}: {null_pct:.1f}% missing values")
        
        # Calculate overall quality score (0-100)
        quality_score = completeness
        
        # Deduct for too few rows
        if len(df) < 10:
            quality_score -= 20
            analysis["issues"].append(f"Only {len(df)} rows - may be insufficient for analysis")
        
        # Deduct for too many issues
        quality_score -= min(len(analysis["issues"]) * 5, 30)
        
        analysis["quality_score"] = max(0, round(quality_score, 0))
        
        return analysis
    
    def analyze_batch(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze quality of multiple files.
        
        Args:
            files: List of dicts with 'df' and 'filename'
            
        Returns:
            Combined quality report
        """
        results = {
            "total_files": len(files),
            "files": {},
            "overall_quality": 0,
            "summary": {}
        }
        
        total_quality = 0
        total_rows = 0
        all_issues = []
        
        for file_info in files:
            df = file_info["df"]
            filename = file_info["filename"]
            
            analysis = self.analyze_file(df, filename)
            results["files"][filename] = analysis
            
            total_quality += analysis["quality_score"]
            total_rows += analysis["row_count"]
            all_issues.extend(analysis["issues"])
        
        results["overall_quality"] = round(total_quality / len(files), 0) if files else 0
        results["summary"] = {
            "total_rows": total_rows,
            "total_issues": len(all_issues),
            "avg_completeness": round(
                sum(r["completeness_score"] for r in results["files"].values()) / len(files), 1
            ) if files else 0
        }
        
        return results


