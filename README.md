# wearable-clinical-data-platform

Stanford Snyderlab Challenge - Fitbit Data Pipeline

A comprehensive data engineering solution for processing, storing, and analyzing Fitbit wearable data for clinical trials. This project implements a complete pipeline from data ingestion to visualization and monitoring.

Project Overview

This repository contains solutions for the Snyderlab Challenge tasks:
## Task Progress

- [x] **Task 1**: Daily data ingestion pipeline with **TimescaleDB** ✅
- [x] **Task 2**: API and dashboard for data access/visualization ✅
- [x] **Task 3**: Multi-user/multi-year query optimization ✅
- [ ] Task 4: Advanced dashboard with clinical trial features
- [ ] Task 5: Monitoring and alerting system
- [ ] Task 6 (Optional): Horizontal Scaling

Data Source

The pipeline processes synthetic Fitbit Charge 6 data generated using the Wearipedia framework, including:

- **Heart Rate**: 1-second resolution intraday data
- **Breathing Rate**: Sleep-based measurements  
- **Active Zone Minutes**: Per-minute activity data
- **Heart Rate Variability**: 5-minute intervals during sleep
- **SpO2**: Per-minute measurements during sleep


Quick Start
Prerequisites

- **Docker** and **Docker Compose**
- Git
- At least 4GB RAM (8GB recommended)

Task 1: Data Ingestion Pipeline

    cd task1

    Add your data files:
    # Copy your exported JSON files to the data directory
    cp ~/Downloads/complete_clinical_trial.json data/
    cp ~/Downloads/*.json data/

    Start the pipeline:
    docker-compose up -d

    Monitor ingestion:
    # Check logs
    docker-compose logs -f fitbit_ingestion

    # Check database
    docker-compose exec timescaledb psql -U fitbit_user -d fitbit_data -c "SELECT COUNT(*) FROM raw_data;"

Task 2: API & Dashboard
Prerequisites

- `Task 1` **TimescaleDB** with data loaded
- **Docker** and **Docker Compose**
- **Node.js** for **React** development
    
Quick Start
    
    cd task2
    docker-compose up -d fitbit_api

    cd src/frontend
    npm install
    npm start

Access the dashboard at `http://localhost:3000`

Access API docs at `http://localhost:8000/docs`

## Task 1: Data Ingestion Pipeline 
### What Was Built 
- Daily delta-load pipeline using **TimescaleDB**
- **Docker** Compose orchestration
- Structured data ingestion from clinical trial exports
- Comprehensive error handling and logging
  
## Technical Decisions
Why TimescaleDB?
- Time-series optimization: Built for time-series data with automatic partitioning
- **PostgreSQL** compatibility: Full **SQL** support with familiar interface
- Continuous aggregates: Pre-computed summaries for fast queries
- Scalability: Handles multi-user, multi-year clinical trial data

Data Processing Strategy
- Structured ingestion: Pre-processed clinical trial data format
- Batch processing: Efficient bulk insertions with error handling
- Multi-metric support: Handles all Fitbit data types with proper normalization
- Metadata tracking: Maintains data lineage and quality information

## Task 2: API & Dashboard Implementation
<img width="540" height="388" alt="Screenshot 2025-07-15 at 11 39 02 AM" src="https://github.com/user-attachments/assets/8d0cc2be-27cd-4386-9d34-a55a3f7eb0a9" />

### What Was Built
- **FastAPI** backend with REST endpoints for time-series data access
- **React** frontend with interactive data visualization
- Hybrid deployment approach for development efficiency
- Direct **TimescaleDB** queries with proper error handling

#### Database Connection
- **Technology**: `psycopg2` **PostgreSQL** client for **Python**
- **Connection**: Direct queries to **TimescaleDB** `raw_data` hypertable
- **Query optimization**: Leverages time-series indexing for efficient data retrieval

User Interface
- Form-based querying: Select `user_id`, `metric_type`, date range, and limit
- Real-time visualization: **Recharts** line charts with responsive design
- Error handling: User-friendly error messages and loading states

Chart Features 
- Time-series line charts with proper time formatting
- Real-time updates when parameters change
## Technical Decisions
Why FastAPI?
- Type validation with Pydantic models for data integrity
- Async capabilities for concurrent requests
- Auto-generated interactive docs at /docs & automatic API documentation

Why React + Recharts?
- Component-based architecture for maintainable UI
- **Recharts**: Lightweight, declarative charting library
- **React** hooks for clean data flow
- Hot reload and modern tooling

Deployment Strategy
- API in **Docker** and **React** local development
Reasoning:
- API containerization: Consistent deployment environment
- React: Fast development cycle with hot reload
- Database integration: Reuses `Task 1` **TimescaleDB** instance

## Task 3: Query Optimization Implementation

### What Was Built
- Intelligent query router for automatic table selection based on time range
- Memory-efficient query execution using **TimescaleDB** continuous aggregates
- Transparent optimization with response metadata showing performance decisions
- Multi-user scalability preparation for clinical trials (n>100 participants)

## Technical Decisions
Aggregation Strategy
- `raw_data` hypertable: Full resolution intraday data
- `data_1m` continuous aggregate: 1-minute summaries
- `data_1h` continuous aggregate: 1-hour summaries
- `data_1d` continuous aggregate: 1-day summaries

## Query Router Logic
   	```def get_optimal_table(start_date, end_date):
    time_diff = end_date - start_date 
    if time_diff > timedelta(days=7):
        return "data_1d"  
    elif time_diff > timedelta(hours=6): 
        return "data_1h"
    else:
        return "raw_data"```

License

This project is part of the Snyderlab Challenge and is intended for educational and research purposes.

### Data Source License
The synthetic Fitbit data is generated using the [Wearipedia](https://github.com/Stanford-Health/wearipedia) framework, which is licensed under the MIT License.

### Project Code
The pipeline implementation code in this repository is developed for the Snyderlab Challenge evaluation.
