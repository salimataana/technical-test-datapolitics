FROM python:3.12-slim

# Installation de Tesseract OCR et de la langue française
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installation des dépendances Python
COPY pyproject.toml .
COPY src ./src

RUN pip install --no-cache-dir .

# Création du dossier de stockage
RUN mkdir -p /app/storage

# Lancement de FastAPI
CMD ["uvicorn", "pdf_search.api.main:app", "--host", "0.0.0.0", "--port", "8000"]