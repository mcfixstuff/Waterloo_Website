# Use a lightweight Debian-based Python image
FROM python:3.10-slim-buster

# Install system dependencies for Python & PostgreSQL
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the project files into the container
COPY . .

# Create and activate a virtual environment
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose port 8000 for the Django application
EXPOSE 8000

# Start the application inside the virtual environment
CMD ["sh", "-c", ". venv/bin/activate && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
