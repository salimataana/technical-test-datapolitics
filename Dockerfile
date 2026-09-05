FROM python:3.12-slim

# Install Tesseract OCR, then create the application user
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin appuser \
    && python -m venv /opt/venv \
    && chown -R appuser:appuser /opt/venv /home/appuser

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml uv.lock ./
COPY src ./src

RUN chown -R appuser:appuser /app

USER appuser

RUN pip install --no-cache-dir "uv==0.11.3"
RUN UV_PROJECT_ENVIRONMENT=/opt/venv uv sync --locked --no-dev

# Create the storage directory
RUN mkdir -p /app/storage

# Start FastAPI
CMD ["uvicorn", "pdf_search.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
