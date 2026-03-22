FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies before copying source code for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a non-root user and hand over ownership
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

RUN chmod +x /app/django.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/django.sh"]
