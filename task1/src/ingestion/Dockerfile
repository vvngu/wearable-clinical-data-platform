FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    cron \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

RUN mkdir -p /app/data /app/logs

# Set up cron job for daily ingestion
RUN echo "0 1 * * * cd /app && python main.py >> /app/logs/cron.log 2>&1" > /etc/cron.d/fitbit-ingestion
RUN chmod 0644 /etc/cron.d/fitbit-ingestion
RUN crontab /etc/cron.d/fitbit-ingestion

# Create startup script
RUN echo '#!/bin/bash\n\
# Start cron in background\n\
service cron start\n\
# Run initial ingestion\n\
echo "Running initial ingestion..."\n\
python main.py\n\
# Show cron status and keep container running\n\
tail -f /app/logs/ingestion.log' > /aecho "Cron scheduled for daily runs at 01:00 UTC (0 1 * * *)"\n\
echo "Container will continue running..."\n\
tail -f /app/logs/ingestion.log /app/logs/cron.log' > /app/start.shpp/start.sh

RUN chmod +x /app/start.sh

EXPOSE 8080

CMD ["/app/start.sh"]