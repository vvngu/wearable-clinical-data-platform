# Task 1 Ingestion Service Dockerfile
# File: task1/src/ingestion/Dockerfile

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create directories
RUN mkdir -p /app/data /app/logs

# Set up cron job for daily ingestion
RUN echo "0 1 * * * cd /app && python main.py >> /app/logs/cron.log 2>&1" > /etc/cron.d/fitbit-ingestion
RUN chmod 0644 /etc/cron.d/fitbit-ingestion
RUN crontab /etc/cron.d/fitbit-ingestion

# Create startup script
RUN echo '#!/bin/bash\n\
# Start cron in background\n\
cron\n\
# Run initial ingestion\n\
python main.py\n\
# Keep container running\n\
tail -f /app/logs/ingestion.log' > /app/start.sh

RUN chmod +x /app/start.sh

# Expose port for health checks
EXPOSE 8080

# Start the application
CMD ["/app/start.sh"]