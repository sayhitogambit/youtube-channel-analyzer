FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files (including shared utilities)
COPY . /app/

# Create output directory
RUN mkdir -p /app/output

# Environment
ENV PYTHONUNBUFFERED=1
ENV OUTPUT_DIR=/app/output
ENV CACHE_ENABLED=true

# Run
CMD ["python", "main.py"]
