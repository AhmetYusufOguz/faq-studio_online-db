FROM python:3.11-slim

# Sistem paketlerini güncelle ve sadece gerekli olanları yükle
RUN apt-get update && apt-get install -y \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Virtual environment oluştur
RUN python3 -m venv /app/venv

# Virtual environment'ı aktive et ve pip'i güncelle
RUN /app/venv/bin/pip install --upgrade pip

# Requirements dosyasını kopyala
COPY requirements.txt .

# Virtual environment içine paketleri yükle
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Data dizini oluştur
RUN mkdir -p /app/data

# Port expose et
EXPOSE 8000

# Virtual environment ile uygulamayı başlat
CMD ["/app/venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]