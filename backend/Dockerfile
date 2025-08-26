FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıklarını yükle
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# ChromaDB için gerekli environment değişkeni
ENV CHROMA_DB_PATH=/app/chroma_db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]