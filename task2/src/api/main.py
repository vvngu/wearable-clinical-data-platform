"""
FastAPI Backend for Fitbit Data Dashboard
Provides REST endpoints for time-series data queries
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "fitbit_data"),
    "user": os.getenv("DB_USER", "fitbit_user"),
    "password": os.getenv("DB_PASSWORD", "fitbit_password")
}

app = FastAPI(
    title="Fitbit Data API",
    description="REST API for clinical trial time-series data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MetricData(BaseModel):
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = {}

class MetricsResponse(BaseModel):
    user_id: str
    metric_type: str
    start_date: str
    end_date: str
    data: List[MetricData]
    total_records: int

class DatabaseManager:
    """Simple database connection manager"""
    
    def __init__(self, config: dict):
        self.config = config
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.config)
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query and return results"""
        if not self.connection:
            raise Exception("No database connection")
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

db_manager = DatabaseManager(DB_CONFIG)

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    logger.info("Starting FastAPI application")
    if not db_manager.connect():
        raise Exception("Failed to connect to database")
    logger.info("Database connected successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connection on shutdown"""
    logger.info("Shutting down FastAPI application")
    db_manager.disconnect()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Fitbit Data API is running", "status": "healthy"}

@app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_metrics(
    user_id: str = Query(..., description="User ID to query data for"),
    metric_type: str = Query(..., description="Type of metric (e.g., heart_rate)"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    limit: int = Query(1000, description="Maximum number of records to return")
):
    """
    Get time-series metrics for a user within a date range
    
    This endpoint queries the TimescaleDB raw_data table for the specified
    user, metric type, and date range.
    """
    try:
        # Validate date format
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Validate date range
        if start_dt >= end_dt:
            raise HTTPException(
                status_code=400, 
                detail="start_date must be before end_date"
            )
        
        query = """
        SELECT 
            timestamp,
            value,
            metadata
        FROM raw_data
        WHERE user_id = %s 
        AND metric_type = %s
        AND timestamp >= %s
        AND timestamp <= %s
        ORDER BY timestamp ASC
        LIMIT %s
        """
        
        params = (user_id, metric_type, start_dt, end_dt, limit)
        results = db_manager.execute_query(query, params)
        
        data = []
        for row in results:
            data.append(MetricData(
                timestamp=row["timestamp"],
                value=float(row["value"]),
                metadata=row.get("metadata", {})
            ))
        
        return MetricsResponse(
            user_id=user_id,
            metric_type=metric_type,
            start_date=start_date,
            end_date=end_date,
            data=data,
            total_records=len(data)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format. Use YYYY-MM-DD: {e}"
        )
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/api/v1/users/{user_id}/metrics")
async def get_user_metrics(user_id: str):
    """Get available metric types for a user"""
    try:
        query = """
        SELECT DISTINCT metric_type, COUNT(*) as record_count
        FROM raw_data
        WHERE user_id = %s
        GROUP BY metric_type
        ORDER BY record_count DESC
        """
        
        results = db_manager.execute_query(query, (user_id,))
        return {"user_id": user_id, "available_metrics": results}
        
    except Exception as e:
        logger.error(f"Error fetching user metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/api/v1/health")
async def health_check():
    """Detailed health check including database connectivity"""
    try:
        # Test database connection
        db_manager.execute_query("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
