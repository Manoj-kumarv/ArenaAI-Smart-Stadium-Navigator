# ─── Build Stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies to a local folder for copying
RUN pip install --no-cache-dir --user -r requirements.txt

# ─── Final Runtime Stage ──────────────────────────────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /sbin/nologin appuser

# Copy installed dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY app /app/app
COPY scripts /app/scripts

# Adjust paths
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
