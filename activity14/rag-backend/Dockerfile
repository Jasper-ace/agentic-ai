# Use the official Python 3.12 slim image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app/agentic-ai/activity13

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements from both levels
COPY rag-backend/requirements.txt ./rag-backend/requirements.txt
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r rag-backend/requirements.txt -r requirements.txt

# Copy all the activity13 files
COPY . .

# Expose backend port
EXPOSE 5000

# Set working directory to the backend directory for executing gunicorn
WORKDIR /app/agentic-ai/activity13/rag-backend

# Run the app with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.main:app", "--workers", "2", "--threads", "4", "--timeout", "600"]
