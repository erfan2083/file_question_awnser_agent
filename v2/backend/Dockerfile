# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV HF_HOME=/root/.cache/huggingface

# Install system dependencies
# - tesseract-ocr: Required for pytesseract (OCR)
# - poppler-utils: Required for pypdf (handling PDFs, especially with images)
# - git: Required by some pip packages
# - build-essential: For compiling C extensions (e.g., in faiss-cpu)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    git \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
# This layer is cached to speed up builds if requirements don't change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create the data directories
# These will be mounted over by docker-compose, but it's good practice
RUN mkdir -p /app/data/uploads && mkdir -p /app/data/vectorstore

# Copy the application code into the container
COPY ./app /app/app

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]