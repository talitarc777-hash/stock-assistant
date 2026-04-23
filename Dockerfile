FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --prefer-binary -r /app/requirements.txt

# Copy only runtime backend code/config.
COPY app /app/app
COPY config /app/config
COPY scripts /app/scripts
COPY .env.example /app/.env.example

# Create runtime directories inside container.
RUN mkdir -p /app/data /app/reports

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "debug"]
