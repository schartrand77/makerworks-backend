FROM python:3.11-slim

# Set working dir
WORKDIR /app
COPY . .
ENV PYTHONPATH="/app:/app/app"

# Install system deps
RUN apt-get update && apt-get install -y \
  build-essential gcc libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Expose port
EXPOSE 8000

# Run app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]