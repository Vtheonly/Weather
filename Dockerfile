# Algeria Renewable Energy Factories — Unified Dockerfile
# ========================================================
# Multi-stage build with C++ DSP module compilation.
# Targets: api (FastAPI) and frontend (Streamlit)

# ─── Stage 1: Build C++ DSP Module ────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies for C++ DSP module
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    pybind11-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python build deps
RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache pybind11

# Copy C++ source and build the DSP module
COPY api/dc_microgrid_dwt/cpp/ ./cpp/
RUN cd cpp && python build.py

# ─── Stage 2: Base Dependencies ──────────────────────────────────────────────
FROM python:3.11-slim AS base-deps

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install base requirements via uv with caching
RUN pip install --no-cache-dir uv
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt

# ─── Stage 3: API Dependencies ───────────────────────────────────────────────
FROM base-deps AS api-deps

# API needs heavy ML libraries
COPY requirements-ml.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements-ml.txt

# ─── Stage 4a: API Service (FastAPI) ─────────────────────────────────────────
FROM api-deps AS api

# Copy built C++ DSP module from builder
COPY --from=builder /build/cpp/build/microgrid_dsp*.so /app/

# Copy core engine source (dc_microgrid_dwt)
COPY api/dc_microgrid_dwt/src/ ./dc_microgrid_dwt/src/
COPY api/dc_microgrid_dwt/config/ ./dc_microgrid_dwt/config/
COPY api/dc_microgrid_dwt/start_system.py ./dc_microgrid_dwt/
COPY api/dc_microgrid_dwt/__init__.py ./dc_microgrid_dwt/

# Copy main application code
COPY api/ ./api/
COPY config/ ./config/
COPY core/ ./core/
COPY ui/ ./ui/
COPY pklh5_NN_engine/ ./pklh5_NN_engine/
COPY main.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ─── Stage 4b: Frontend Service (Streamlit) ──────────────────────────────────
FROM base-deps AS frontend

# Copy built C++ DSP module from builder
COPY --from=builder /build/cpp/build/microgrid_dsp*.so /app/

# Copy core engine source (dc_microgrid_dwt)
COPY api/dc_microgrid_dwt/src/ ./dc_microgrid_dwt/src/
COPY api/dc_microgrid_dwt/config/ ./dc_microgrid_dwt/config/
COPY api/dc_microgrid_dwt/start_system.py ./dc_microgrid_dwt/
COPY api/dc_microgrid_dwt/__init__.py ./dc_microgrid_dwt/

# Copy main application code
COPY api/ ./api/
COPY config/ ./config/
COPY core/ ./core/
COPY ui/ ./ui/
COPY pklh5_NN_engine/ ./pklh5_NN_engine/
COPY main.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["python", "-m", "streamlit", "run", "main.py", \
     "--server.port", "8501", \
     "--server.address", "0.0.0.0", \
     "--server.headless", "true"]