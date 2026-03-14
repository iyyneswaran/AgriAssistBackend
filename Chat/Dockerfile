FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for some python packages (e.g., soundfile, psycopg2)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port (optional on Railway as it handles it dynamically)
EXPOSE 8001

# Start the FastAPI application (Use shell form to read $PORT from Railway, fallback to 8001)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}
