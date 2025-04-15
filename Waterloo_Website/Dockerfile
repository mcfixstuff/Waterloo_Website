FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install system-level dependencies including LaTeX (pdflatex)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc python3-dev \
    libjpeg-dev zlib1g-dev libfreetype6-dev \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-xetex \
    lmodern \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Create media and static directories
RUN mkdir -p /app/media/signatures
RUN mkdir -p /app/static
RUN chmod -R 755 /app/media
RUN chmod -R 755 /app/static

# Expose port
EXPOSE 8000

# Start server using a script
RUN echo '#!/bin/bash\n\
    echo "Running collectstatic..."\n\
    python manage.py collectstatic --noinput\n\
    echo "Running migrations..."\n\
    python manage.py migrate\n\
    echo "Starting server..."\n\
    gunicorn --bind 0.0.0.0:8000 Waterloo.wsgi:application\n\
    ' > /app/start.sh

RUN chmod +x /app/start.sh

# Start server
CMD ["/app/start.sh"]
