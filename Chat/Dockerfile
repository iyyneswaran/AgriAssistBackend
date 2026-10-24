FROM python:3.11-slim

# Prevent .pyc files and enable unbuffered logging for Railway
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies required at runtime:
#   libpq-dev   -> asyncpg / psycopg2 native bindings
#   libsndfile1 -> soundfile (pydub / audio processing)
#   build-essential -> needed by some pip packages that compile C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install CPU-only PyTorch first from the official CPU wheel index,
# then install the remaining dependencies using the CPU wheel index as well.
RUN pip install \
    torch==2.5.1+cpu \
    torchvision==0.20.1+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    && pip install \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port (optional on Railway as it handles it dynamically)
EXPOSE 8001

# Start the FastAPI application with a single worker to avoid
# multiple processes each loading their own copy of ML models.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001} --workers 1"]
