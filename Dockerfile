FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy .env (you can also bind-mount in docker-compose)
COPY .env /app/.env

# Set environment variables explicitly if needed
ENV PYTHONUNBUFFERED=1
ENV ENV=production

# Expose port
EXPOSE 8000

# Run app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]