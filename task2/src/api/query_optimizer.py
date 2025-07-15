"""
Query Optimizer for Multi-User, Multi-Year Scenarios
Automatically selects optimal table based on query time range
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Query optimizer that selects the best table based on time range"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_optimal_table(self, start_date: datetime, end_date: datetime) -> str:
        """
        Select optimal table based on time range
        Task 3 requirement: automatic table selection
        """
        time_diff = end_date - start_date
        logger.info(f"Time difference: {time_diff}")
        
        if time_diff > timedelta(days=7):
            logger.info("Using data_1d")
            return "data_1d"
        elif time_diff > timedelta(hours=6):
            logger.info("Using data_1h") 
            return "data_1h"
        elif time_diff > timedelta(hours=1):
            logger.info("Using data_1m")
            return "data_1m"
        else:
            logger.info("Using raw_data")
            return "raw_data"
        
    def build_optimized_query(self, start_date: datetime, end_date: datetime,
                            user_id: str, metric_type: str, limit: int) -> Tuple[str, tuple, str]:
        """
        Build query using optimal table selection
        Returns: (query, params, table_name)
        """
        table_name = self.get_optimal_table(start_date, end_date)
        
        logger.info(f"Using table: {table_name} for {end_date - start_date} time range")
        
        if table_name == "raw_data":
            # Raw data query (unchanged)
            query = """
            SELECT timestamp, value, metadata
            FROM raw_data
            WHERE user_id = %s 
            AND metric_type = %s
            AND timestamp >= %s
            AND timestamp <= %s
            ORDER BY timestamp ASC
            LIMIT %s
            """
        else:
            # Aggregated data query
            query = f"""
            SELECT bucket as timestamp, avg_value as value, 
                   json_build_object('min', min_value, 'max', max_value, 'count', count) as metadata
            FROM {table_name}
            WHERE user_id = %s 
            AND metric_type = %s
            AND bucket >= %s
            AND bucket <= %s
            ORDER BY bucket ASC
            LIMIT %s
            """
        
        params = (user_id, metric_type, start_date, end_date, limit)
        return query, params, table_name
