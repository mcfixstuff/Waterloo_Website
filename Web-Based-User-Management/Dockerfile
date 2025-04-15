# Use an official Python runtime as a parent image
FROM python:3.13-slim

RUN apt-get update && apt-get install -y make

# Install build tools, make, and a minimal TeX distribution
RUN apt-get update && \
    apt-get install -y make texlive-latex-base && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


# Prevent Python from writing pyc files to disc and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that Flask runs on
EXPOSE 7070

# Set environment variables for Flask
ENV FLASK_APP=run.py
ENV FLASK_ENV=development

# Start the Flask app
CMD ["flask", "run", "--host=0.0.0.0"]


