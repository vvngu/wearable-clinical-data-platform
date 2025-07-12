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

The pipeline processes synthetic Fitbit Charge 6 data generated using the Wearipedia framework, including


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

Task 2: API & Dashboard
bash

cd task2
docker-compose up -d

Access the dashboard at http://localhost:3000

Technical Decisions
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

Performance Optimizations
Database Level (Task 3)

    Hypertable partitioning: Automatic time-based partitioning
    Continuous aggregates: 1-minute, 1-hour, 1-day pre-computed summaries
    Smart query routing: Automatically selects optimal table based on time range
    Compression policies: Automatic compression for older data

Testing
bash

# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Run all tests with coverage
pytest --cov=src tests/

License

This project is part of the Snyderlab Challenge and is intended for educational and research purposes.
Acknowledgments

    Stanford Health: For the Wearipedia framework
    Snyderlab: For the challenge structure