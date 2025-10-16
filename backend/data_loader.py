import os
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from database import get_db, DataSource

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Service for auto-loading CSV files from data/ directory on startup.
    Validates file structure and stores metadata in database.
    """
    
    def __init__(self):
        # Get the project root directory (practus/)
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.project_root, 'data')
        
        # Expected CSV files
        self.expected_files = [
            'Deals Archive.csv',
            'Stage History Archive.csv', 
            'Whizible data.csv',
            'Plotting tool data.csv',
            'Skill mapping.csv',
            'Metrics.csv'
        ]
        
        logger.info(f"DataLoader initialized with data directory: {self.data_dir}")
    
    def validate_data_directory(self) -> Dict[str, Any]:
        """Validate that data directory exists and contains expected files."""
        result = {
            "data_dir": self.data_dir,
            "exists": os.path.exists(self.data_dir),
            "files": {},
            "valid": True,
            "errors": []
        }
        
        if not result["exists"]:
            result["valid"] = False
            result["errors"].append(f"Data directory does not exist: {self.data_dir}")
            return result
        
        # Check each expected file
        for filename in self.expected_files:
            file_path = os.path.join(self.data_dir, filename)
            file_info = {
                "path": file_path,
                "exists": os.path.exists(file_path),
                "size": 0,
                "rows": 0,
                "columns": [],
                "valid": False
            }
            
            if file_info["exists"]:
                try:
                    # Get file size
                    file_info["size"] = os.path.getsize(file_path)
                    
                    # Read CSV to get basic info
                    df = pd.read_csv(file_path, nrows=5)  # Read only first 5 rows for validation
                    file_info["columns"] = list(df.columns)
                    
                    # Get total row count (excluding header)
                    full_df = pd.read_csv(file_path)
                    file_info["rows"] = len(full_df)
                    
                    file_info["valid"] = True
                    logger.info(f"Validated {filename}: {file_info['rows']} rows, {len(file_info['columns'])} columns")
                    
                except Exception as e:
                    file_info["valid"] = False
                    result["errors"].append(f"Error reading {filename}: {str(e)}")
                    logger.error(f"Error validating {filename}: {e}")
            else:
                result["errors"].append(f"Missing file: {filename}")
                logger.warning(f"Missing expected file: {filename}")
            
            result["files"][filename] = file_info
        
        # Overall validation
        valid_files = sum(1 for f in result["files"].values() if f["valid"])
        result["valid"] = len(result["errors"]) == 0 and valid_files > 0
        
        logger.info(f"Data validation complete: {valid_files}/{len(self.expected_files)} files valid")
        return result
    
    def load_file_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load metadata for a specific CSV file."""
        file_path = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
        
        try:
            # Read CSV to get metadata
            df = pd.read_csv(file_path)
            
            metadata = {
                "name": filename,
                "file_path": file_path,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "file_size": os.path.getsize(file_path),
                "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "status": "loaded"
            }
            
            # Add sample data (first 3 rows)
            metadata["sample_data"] = df.head(3).to_dict('records')
            
            logger.info(f"Loaded metadata for {filename}: {metadata['row_count']} rows")
            return metadata
            
        except Exception as e:
            logger.error(f"Error loading metadata for {filename}: {e}")
            return None
    
    def store_in_database(self, db: Session) -> Dict[str, Any]:
        """Store file metadata in database."""
        result = {
            "stored": [],
            "errors": [],
            "total_files": 0
        }
        
        for filename in self.expected_files:
            metadata = self.load_file_metadata(filename)
            if not metadata:
                result["errors"].append(f"Failed to load metadata for {filename}")
                continue
            
            try:
                # Check if datasource already exists
                existing = db.query(DataSource).filter(DataSource.name == filename).first()
                
                if existing:
                    # Update existing record
                    existing.file_path = metadata["file_path"]
                    existing.row_count = metadata["row_count"]
                    existing.status = metadata["status"]
                    logger.info(f"Updated existing datasource: {filename}")
                else:
                    # Create new record
                    datasource = DataSource(
                        name=filename,
                        file_path=metadata["file_path"],
                        row_count=metadata["row_count"],
                        status=metadata["status"]
                    )
                    db.add(datasource)
                    logger.info(f"Created new datasource: {filename}")
                
                result["stored"].append(filename)
                result["total_files"] += 1
                
            except Exception as e:
                error_msg = f"Error storing {filename} in database: {str(e)}"
                result["errors"].append(error_msg)
                logger.error(error_msg)
        
        try:
            db.commit()
            logger.info(f"Successfully stored {result['total_files']} files in database")
        except Exception as e:
            db.rollback()
            error_msg = f"Database commit failed: {str(e)}"
            result["errors"].append(error_msg)
            logger.error(error_msg)
        
        return result
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of all data files."""
        validation = self.validate_data_directory()
        
        summary = {
            "data_directory": self.data_dir,
            "total_files": len(self.expected_files),
            "valid_files": sum(1 for f in validation["files"].values() if f["valid"]),
            "total_rows": sum(f["rows"] for f in validation["files"].values() if f["valid"]),
            "total_size": sum(f["size"] for f in validation["files"].values() if f["valid"]),
            "files": {}
        }
        
        for filename, file_info in validation["files"].items():
            if file_info["valid"]:
                summary["files"][filename] = {
                    "rows": file_info["rows"],
                    "columns": len(file_info["columns"]),
                    "size_mb": round(file_info["size"] / (1024 * 1024), 2),
                    "column_names": file_info["columns"][:5]  # First 5 columns
                }
        
        return summary
    
    def initialize_data(self) -> Dict[str, Any]:
        """Initialize data loading process."""
        logger.info("Starting data initialization...")
        
        result = {
            "validation": None,
            "database": None,
            "summary": None,
            "success": False,
            "errors": []
        }
        
        try:
            # Step 1: Validate data directory
            logger.info("Step 1: Validating data directory...")
            result["validation"] = self.validate_data_directory()
            
            if not result["validation"]["valid"]:
                result["errors"].extend(result["validation"]["errors"])
                logger.error("Data validation failed")
                return result
            
            # Step 2: Store in database
            logger.info("Step 2: Storing metadata in database...")
            db = next(get_db())
            try:
                result["database"] = self.store_in_database(db)
                if result["database"]["errors"]:
                    result["errors"].extend(result["database"]["errors"])
            finally:
                db.close()
            
            # Step 3: Generate summary
            logger.info("Step 3: Generating data summary...")
            result["summary"] = self.get_data_summary()
            
            # Overall success
            result["success"] = len(result["errors"]) == 0
            
            if result["success"]:
                logger.info("Data initialization completed successfully")
            else:
                logger.error(f"Data initialization completed with {len(result['errors'])} errors")
            
            return result
            
        except Exception as e:
            error_msg = f"Data initialization failed: {str(e)}"
            result["errors"].append(error_msg)
            logger.error(error_msg)
            return result
    
    def get_file_path(self, filename: str) -> Optional[str]:
        """Get full path for a specific file."""
        file_path = os.path.join(self.data_dir, filename)
        return file_path if os.path.exists(file_path) else None
    
    def list_available_files(self) -> List[str]:
        """List all available CSV files in data directory."""
        if not os.path.exists(self.data_dir):
            return []
        
        available_files = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.csv'):
                available_files.append(filename)
        
        return sorted(available_files)
    
    def check_data_freshness(self) -> Dict[str, Any]:
        """Check if data files have been updated recently."""
        result = {
            "files": {},
            "last_modified": None,
            "stale_files": []
        }
        
        if not os.path.exists(self.data_dir):
            return result
        
        latest_time = None
        
        for filename in self.expected_files:
            file_path = os.path.join(self.data_dir, filename)
            if os.path.exists(file_path):
                mod_time = os.path.getmtime(file_path)
                mod_datetime = datetime.fromtimestamp(mod_time)
                
                result["files"][filename] = {
                    "last_modified": mod_datetime.isoformat(),
                    "days_old": (datetime.now() - mod_datetime).days
                }
                
                if latest_time is None or mod_time > latest_time:
                    latest_time = mod_time
                    result["last_modified"] = mod_datetime.isoformat()
                
                # Flag files older than 30 days as stale
                if (datetime.now() - mod_datetime).days > 30:
                    result["stale_files"].append(filename)
        
        return result
