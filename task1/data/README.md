# Data Files

The clinical trial data files are too large for GitHub (400+ MB each).

## For Reviewers
Sample data structure is available in the notebook: `notebooks/fitbit_charge_6.ipynb`

## To Run Locally
1. Run the notebook to generate data files
2. Copy the exported JSON files to this directory
3. Run `docker-compose up -d` to start the pipeline

## Data Files Expected
- complete_clinical_trial.json (full dataset)
- hr_clinical_trial.json (heart rate data)
- br_clinical_trial.json (breathing rate data)
- azm_clinical_trial.json (active zone minutes)
- hrv_clinical_trial.json (heart rate variability)
- spo2_clinical_trial.json (SpO2 data)

## Data Structure
Each file contains structured clinical trial data with:

- participant_id: Unique identifier
- timestamp: ISO format datetime
- metric_type: Type of measurement
- value: Numeric measurement value
- metadata: Additional context (resolution, priority)
EOF