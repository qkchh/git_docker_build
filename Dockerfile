# ============================================================
# Git Docker Build — Application Image
# ============================================================
# NOTE: This container needs access to the host Docker daemon
#       to build images. Mount the socket at runtime:
#         -v /var/run/docker.sock:/var/run/docker.sock
# ============================================================

FROM python:3.12-slim

# Install git (GitPython) and Docker CLI (python-on-whales)
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
    && curl -fsSL https://get.docker.com | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY main.py database.py models.py ./
COPY routers/ routers/
COPY services/ services/
COPY static/ static/

# Persistent directories (override with volumes)
RUN mkdir -p workspace data

EXPOSE 3002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3002"]
