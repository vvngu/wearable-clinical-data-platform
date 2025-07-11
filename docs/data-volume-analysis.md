# Data Volume Estimation for Clinical Trials

## Overview
This document provides back-of-the-envelope calculations for data volume estimation in a clinical trial system supporting up to 1,000 participants with Fitbit wearable devices.

### 1. Data Point Calculations
Assumptions:
- Metrics:  4 primary metircs (heart_rate, steps, distance, spo2)
- Resolution: 1 second intervals
- Duration: 1 year baseline

Calculations
- Seconds per year: 365 days * 24 hours a day * 3,600 seconds an hour =31,536,000 
- Data points per participant per year: 31,536,000 * 4 metrics = 126,144,000 data points

| Participants    | 1 year  | 2 years | 5 years |
| :---------------| :------:| -------:| -------:|
| n = 1           | 126.144M| 252.288M| 630.72M |
| n = 1,000       | 126.144B| 252.288B| 630.72B |
| n = 10,000      | 1.261T  | 2.52288T| 6.3072T |

### 2. Storage Requirements

Data Structure per Point
{
  timestamp: 8 bytes (Unix timestamp)
  participant_id: 4 bytes (integer ID)
  metric_type: 1 byte (enum)
  value: 4 bytes (float32)
  total: ~17 bytes per data point
}

Storage Calculations:
Assume: n = 1,000, 2 years, 3 metrics at 1-second resolution
- Data points: 1,000 * 2 * 31,536,00 * 3 = 189.22B data points
- Uncompressed: 189.22B * 20 bytes = 3.78 TB
- Compressed at 80%: 3.78 TB *.20 = 756 GB

Time Series Compression Analysis:

Cases where time-series data would not be compressed by very much:
- Highly variable data points
- Time intervals between data points fluctuates significantly
- Random data without patterns or redundencies
- Already compressed data using another method

Compression is highly effective for health data (heart rate, sleep, physical activity data, etc):
- Delta Encoding: heart rate changes are typically small +-5BPM
- Run-length Encoding: Many zero values during sleep periods
- Timestamp predictability: Regular 1-second intervals compress well
- Value patterns: Gradual changes in physiological metrics

### 3. Fitbit API Metrics
Useful metrics for physical activity affecting sleep
study

| Metric         |Resolution| Relevance  |
| :---------------| :------:| -------:|
| Sleep Stages    | 30 seconds| sleep stage quality|  
| Heart Rate   | 1 second during exercise/ 15 seconds during rest|Measures recovery, exercise inensity, sleep quality | 
| Heart Rate Variability| 1 minute  | measures stress recovery and management |
| Steps     | 1 minute  | activity level|
| SpO2    |1-min / 5 minutes (during sleep)| Sleep quality and respiratory health |
| Active Zone Minutes  | 1 minute  | activity intensity and duration |

Data Volume Calculations
- Participants n=1,000, 1 year
Basic calulations:
- Seconds per year: 365 × 24 × 3600 = 31,536,000 seconds
- Minutes per year: 365 × 24 × 60 = 525,600 minutes
- Bytes per data point: 20 bytes (timestamp: 8, participant_id: 4, metric_type: 1, value: 4, overhead: 3)

| Metric         |Data Points/year| Storage Volume  |
| :---------------| :------:| -------:|
| Sleep Stages    | 1,051,200,000| 21.02GB|  
| Heart Rate   | 31,536,000,000| 630.72GB |
| Heart Rate Variability| 525,600,000 | 10.51GB |
| Steps     |525,600,000 | 10.51GB |
| SpO2    |175,200,000| 3.5GB |
| Active Zone Minutes  | 525,600,000 | 10.51GB |
| Total Volume  | | 686.77GB |
| Total Volume Compressed (80%)  |   | 137.35GB |

### 4. Query Optimization 
Possible Solutions to Expesnive Fine-Resolution Querying
- Multi-Resolution Storage: instead of storing only 1-second raw data, pre-compute and store multiple aggregation levels:
  - raw_data_1s      -- 1-second resolution
  - aggregated_1m    -- 1-minute averages
  - aggregated_5m    -- 5-minute averages
  - aggregated_1h    -- Hourly summaries
  - aggregated_1d    -- Daily summaries
  
  Benefits: fast dashboard queries, trends and detailed analysis
  
  Trade-offs: 5x more storage, must maintain multiple tables, must ensure consistency with aggregations remaining in sync
- Partioning: time-based particioning vs. participant-based particioning
  Benefits: each partiion can be queried indipendently, faster queries - database only scans relevant partition
- Index Optimization: Use composite indexes such as participant-based index or metric-based, etc. OR partial indexes such as specifc time frame (last 30 days) or specifc data (sleep stages data only)

### 5. Scaling Analysis

**Vertical scaling limits**
| Resource    | Practical Limit |Cost/Conisderations |
| :---------------| :------:|------:|
| CPU          | 64-128 cores| $15K-40K, diminishing returns|
| Memory      | 1-6 TB RAM | $30K-50K, bandwith becomes bottelneck |
| Storage      | 100-200 TB | $50K-200K |

**Horizontal scaling strategy**

Data Distribution:
- Participant-based sharding: 250 participants per machine
- Time-based sharding: distribute by date ranges
- Hybrid approach: combine both for optimal performance

Query Resolution:
- Query Coordinator: Central machine that distributes queries and aggregates results
- Sharding: Participant-based + time-based hybrid approach
- Replication: 2x replication across machines for fault tolerance