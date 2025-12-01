FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project structure
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r league_webapp/requirements.txt

# Set Python path to include the app directory
ENV PYTHONPATH=/app

WORKDIR /app/league_webapp

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "run.py"]
