
FROM python:3.9-slim

WORKDIR /app

# Install dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn flask

# Install Playwright browsers
RUN playwright install chromium

# Copy the application code
COPY . .

# Create a directory for output
RUN mkdir -p /app/data

# Make port 8080 available (standard for GCP)
EXPOSE 8080

# Define environment variable for port (used by GCP)
ENV PORT=8080

# Run app using gunicorn when container launches
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app