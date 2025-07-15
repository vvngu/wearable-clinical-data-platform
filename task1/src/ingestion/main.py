#!/usr/bin/env python3
"""
Fitbit Data Ingestion Script
Handles structured clinical trial data ingestion into TimescaleDB
"""

import os
import json
import logging
import psycopg2
from datetime import datetime
from typing import List, Dict, Any
import time
from dataclasses import dataclass
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FitbitConfig:
    """Configuration for Fitbit API access"""
    client_id: str
    client_secret: str
    access_token: str
    refresh_token: str
    
    @classmethod
    def from_env(cls) -> 'FitbitConfig':
        """Load configuration from environment variables"""
        return cls(
            client_id=os.getenv('FITBIT_CLIENT_ID', ''),
            client_secret=os.getenv('FITBIT_CLIENT_SECRET', ''),
            access_token=os.getenv('FITBIT_ACCESS_TOKEN', ''),
            refresh_token=os.getenv('FITBIT_REFRESH_TOKEN', '')
        )
    
@dataclass
class DatabaseConfig:
    """Configuration for database connection"""
    host: str
    port: int
    database: str
    user: str
    password: str
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Load configuration from environment variables"""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'fitbit_data'),
            user=os.getenv('DB_USER', 'fitbit_user'),
            password=os.getenv('DB_PASSWORD', 'fitbit_password')
        )
class FitbitClient:
    """Client for interacting with Fitbit API"""
    
    def __init__(self, config: FitbitConfig):
        self.config = config
        self.base_url = "https://api.fitbit.com/1"
        
    def get_heart_rate_data(self, date: str, user_id: str = "-") -> Optional[Dict[str, Any]]:
        """Get heart rate data for a specific date"""
        try:
            url = f"{self.base_url}/user/{user_id}/activities/heart/date/{date}/1d/1sec.json"
            headers = {'Authorization': f'Bearer {self.config.access_token}'}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get heart rate data for {date}: {str(e)}")
            return None
        
class DatabaseManager:
    """Manager for database operations"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None
        
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
            logger.info("Successfully connected to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def insert_raw_data(self, data: List[Dict[str, Any]]) -> bool:
        """Insert raw data into the database"""
        if not data:
            logger.info("No data to insert")
            return True
            
        try:
            with self.connection.cursor() as cursor:
                # Prepare data for insertion
                values = [
                    (
                        record['timestamp'],
                        record['user_id'],
                        record['metric_type'],
                        record['value'],
                        json.dumps(record.get('metadata', {}))
                    )
                    for record in data
                ]
                
                # Use execute_values for efficient bulk insertion
                execute_values(
                    cursor,
                    """
                    INSERT INTO raw_data (timestamp, user_id, metric_type, value, metadata)
                    VALUES %s
                    ON CONFLICT DO NOTHING
                    """,
                    values,
                    template=None,
                    page_size=1000
                )
                
                self.connection.commit()
                logger.info(f"Successfully inserted {len(data)} records")
                return True
                
        except Exception as e:
            logger.error(f"Failed to insert raw data: {str(e)}")
            self.connection.rollback()
            return False
    
    def log_ingestion(self, user_id: str, records_processed: int, errors: int, duration: float):
        """Log ingestion metadata"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO ingestion_log (user_id, last_ingestion_time, records_processed, errors_encountered, ingestion_duration_seconds)
                    VALUES (%s, NOW(), %s, %s, %s)
                    """,
                    (user_id, records_processed, errors, duration)
                )
                self.connection.commit()
                
        except Exception as e:
            logger.error(f"Failed to log ingestion: {str(e)}")

class FitbitDataProcessor:
    """Processor for converting structured clinical trial data to database format"""
    
    @staticmethod
    def process_structured_data(structured_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process structured clinical trial data for database insertion"""
        processed_data = []
        
        try:
            # Process heart rate intraday data (highest priority)
            hr_data = structured_data.get('heart_rate', {}).get('intraday_data', [])
            for record in hr_data:
                processed_data.append({
                    'timestamp': record['timestamp'],
                    'user_id': record['participant_id'],
                    'metric_type': record['metric_type'],
                    'value': float(record['value']),
                    'metadata': {
                        'resolution': record.get('resolution', '1_second'),
                        'priority': record.get('priority', 'high'),
                        'source': 'wearipedia_clinical_trial'
                    }
                })
            
            # Process breathing rate data
            br_data = structured_data.get('breathing_rate', {}).get('sleep_summaries', [])
            for record in br_data:
                # Create separate records for each breathing rate type
                br_types = ['deep_sleep_br', 'rem_sleep_br', 'light_sleep_br', 'full_sleep_br']
                for br_type in br_types:
                    if br_type in record:
                        processed_data.append({
                            'timestamp': f"{record['date']} 00:00:00",
                            'user_id': record['participant_id'],
                            'metric_type': f"breathing_rate_{br_type}",
                            'value': float(record[br_type]),
                            'metadata': {
                                'resolution': 'per_sleep',
                                'priority': 'medium',
                                'source': 'wearipedia_clinical_trial'
                            }
                        })
            
            # Process active zone minutes
            azm_data = structured_data.get('active_zone_minutes', {}).get('intraday_data', [])
            for record in azm_data:
                azm_types = ['fat_burn_minutes', 'cardio_minutes', 'peak_minutes', 'total_minutes']
                for azm_type in azm_types:
                    if azm_type in record:
                        processed_data.append({
                            'timestamp': record['timestamp'],
                            'user_id': record['participant_id'],
                            'metric_type': f"active_zone_{azm_type}",
                            'value': float(record[azm_type]),
                            'metadata': {
                                'resolution': 'per_minute',
                                'priority': 'medium',
                                'source': 'wearipedia_clinical_trial'
                            }
                        })
            
            # Process HRV data
            hrv_data = structured_data.get('heart_rate_variability', {}).get('sleep_data', [])
            for record in hrv_data:
                hrv_types = ['rmssd', 'lf', 'hf']
                for hrv_type in hrv_types:
                    if hrv_type in record:
                        processed_data.append({
                            'timestamp': record['timestamp'],
                            'user_id': record['participant_id'],
                            'metric_type': f"hrv_{hrv_type}",
                            'value': float(record[hrv_type]),
                            'metadata': {
                                'resolution': '5_min_during_sleep',
                                'priority': 'medium',
                                'source': 'wearipedia_clinical_trial'
                            }
                        })
            
            # Process SpO2 data
            spo2_data = structured_data.get('spo2', {}).get('sleep_data', [])
            for record in spo2_data:
                processed_data.append({
                    'timestamp': record['timestamp'],
                    'user_id': record['participant_id'],
                    'metric_type': 'spo2',
                    'value': float(record['spo2_value']),
                    'metadata': {
                        'resolution': 'per_minute_during_sleep',
                        'priority': 'medium',
                        'source': 'wearipedia_clinical_trial'
                    }
                })
                
        except Exception as e:
            logger.error(f"Error processing structured data: {str(e)}")
            
        return processed_data

class FitbitIngestionPipeline:
    """Main ingestion pipeline for structured clinical trial data"""
    
    def __init__(self):
        self.db_config = DatabaseConfig.from_env()
        self.db_manager = DatabaseManager(self.db_config)
        self.processor = FitbitDataProcessor()
        
    def run_structured_data_ingestion(self, data_file_path: str = "/app/data/complete_clinical_trial.json"):
        """Run ingestion for structured clinical trial data"""
        start_time = time.time()
        total_records = 0
        total_errors = 0
        
        logger.info(f"Starting structured data ingestion from: {data_file_path}")
        
        try:
            # Connect to database
            if not self.db_manager.connect():
                logger.error("Failed to connect to database")
                return False
            
            # Load structured data from file
            with open(data_file_path, 'r') as f:
                structured_data = json.load(f)
            
            logger.info(f"Loaded structured data with keys: {list(structured_data.keys())}")
            
            # Process the structured data
            processed_data = self.processor.process_structured_data(structured_data)
            
            if processed_data:
                logger.info(f"Processing {len(processed_data)} total records")
                
                # Split into batches for efficient insertion
                batch_size = 1000
                for i in range(0, len(processed_data), batch_size):
                    batch = processed_data[i:i + batch_size]
                    
                    if self.db_manager.insert_raw_data(batch):
                        total_records += len(batch)
                        logger.info(f"Successfully inserted batch {i//batch_size + 1}: {len(batch)} records")
                    else:
                        total_errors += 1
                        logger.error(f"Failed to insert batch {i//batch_size + 1}")
                
                # Log ingestion results
                duration = time.time() - start_time
                user_id = structured_data.get('participant_info', {}).get('participant_id', 'synthetic_user_001')
                self.db_manager.log_ingestion(user_id, total_records, total_errors, duration)
                
                logger.info(f"Ingestion completed. Records: {total_records}, Errors: {total_errors}, Duration: {duration:.2f}s")
                
            else:
                logger.warning("No processed data to insert")
                return False
                
        except Exception as e:
            logger.error(f"Structured data ingestion failed: {str(e)}")
            return False
            
        finally:
            self.db_manager.disconnect()
            
        return True

def main():
    """Main entry point for structured data ingestion"""
    logger.info("Starting structured Fitbit data ingestion")
    
    pipeline = FitbitIngestionPipeline()
    
    # Check if we have a specific data file path
    data_file = os.getenv('DATA_FILE_PATH', '/app/data/complete_clinical_trial.json')
    
    success = pipeline.run_structured_data_ingestion(data_file)
    
    if success:
        logger.info("Structured data ingestion completed successfully")
        exit(0)
    else:
        logger.error("Structured data ingestion failed")
        exit(1)

if __name__ == "__main__":
    main()
