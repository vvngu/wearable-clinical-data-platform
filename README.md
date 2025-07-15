# Snyderlab-Challenge

Stanford Snyderlab Challenge - Fitbit Data Pipeline

A comprehensive data engineering solution for processing, storing, and analyzing Fitbit wearable data for clinical trials. This project implements a complete pipeline from data ingestion to visualization and monitoring.

Project Overview

This repository contains solutions for all 5 tasks of the Snyderlab Challenge:

    Task 1: Daily data ingestion pipeline with **TimescaleDB**✅
    Task 2: API and dashboard for data access/visualization
    Task 3: Multi-user/multi-year query optimization
    Task 4: Advanced dashboard with clinical trial features
    Task 5: Monitoring and alerting system

Data Source

The pipeline processes synthetic Fitbit Charge 6 data generated using the Wearipedia framework, including:

- **Heart Rate**: 1-second resolution intraday data
- **Breathing Rate**: Sleep-based measurements  
- **Active Zone Minutes**: Per-minute activity data
- **Heart Rate Variability**: 5-minute intervals during sleep
- **SpO2**: Per-minute measurements during sleep


Quick Start
Prerequisites

    Docker and Docker Compose
    Git
    At least 4GB RAM (8GB recommended)

Task 1: Data Ingestion Pipeline

    Navigate to Task 1:
    bash

    cd task1

    Add your data files:
    bash

    # Copy your exported JSON files to the data directory
    cp ~/Downloads/complete_clinical_trial.json data/
    cp ~/Downloads/*.json data/

    Start the pipeline:
    bash

    docker-compose up -d

    Monitor ingestion:
    bash

    # Check logs
    docker-compose logs -f fitbit_ingestion

    # Check database
    docker-compose exec timescaledb psql -U fitbit_user -d fitbit_data -c "SELECT COUNT(*) FROM raw_data;"


Technical Decisions
## Task 1: Implementation Details

### What Was Built
- **Daily delta-load pipeline** using structured clinical trial data
- **TimescaleDB** with hypertables and continuous aggregates
- **Docker Compose** orchestration for local development
- **Cron scheduling** for automated daily ingestion at 01:00 UTC
- **Comprehensive error handling** and logging

### Schema Design
```sql
-- Raw data hypertable partitioned by timestamp
CREATE TABLE raw_data (
    timestamp TIMESTAMPTZ NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    value DECIMAL(10,2) NOT NULL,
    metadata JSONB
);

-- Continuous aggregates for performance
CREATE MATERIALIZED VIEW data_1m, data_1h, data_1d;

Delta-Load Logic
The pipeline implements delta-load capability by tracking the last ingestion time:

Initial run: Processes full synthetic dataset
Subsequent runs: Checks ingestion_log table for last run time
Cron scheduling: Daily execution at 01:00 UTC (0 1 * * *)


Why TimescaleDB?

    Time-series optimization: Built for time-series data with automatic partitioning
    PostgreSQL compatibility: Full SQL support with familiar interface
    Continuous aggregates: Pre-computed summaries for fast queries
    Scalability: Handles multi-user, multi-year clinical trial data

Data Processing Strategy

    Structured ingestion: Pre-processed clinical trial data format
    Batch processing: Efficient bulk insertions with error handling
    Multi-metric support: Handles all Fitbit data types with proper normalization
    Metadata tracking: Maintains data lineage and quality information
    
    **Synthetic Data Processing** realible for evalutation without API credentials, batch ETL processing pattern, Focuses on pipeline architecture over API integration complexity


License

This project is part of the Snyderlab Challenge and is intended for educational and research purposes.

### Data Source License
The synthetic Fitbit data is generated using the [Wearipedia](https://github.com/Stanford-Health/wearipedia) framework, which is licensed under the MIT License.

### Project Code
The pipeline implementation code in this repository is developed for the Snyderlab Challenge evaluation.