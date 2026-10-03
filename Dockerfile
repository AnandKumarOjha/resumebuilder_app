# Use official Python slim image for a smaller footprint
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py

# Install system dependencies required by WeasyPrint for PDF generation
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application
COPY . /app/

# Create a non-root user and switch to it for security
RUN useradd -m myuser && chown -R myuser:myuser /app
USER myuser

# Expose the port (Render default is 10000)
EXPOSE 10000

# Run gunicorn server, binding to the PORT environment variable provided by Render
CMD gunicorn --bind 0.0.0.0:${PORT:-10000} run:app
