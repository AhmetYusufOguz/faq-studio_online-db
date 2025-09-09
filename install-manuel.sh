#!/bin/bash

# requirements.txt kontrolü
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt bulunamadı!"
    exit 1
fi

# requirements.txt'i kopyala
echo "requirements.txt kopyalanıyor..."
sudo cp requirements.txt /opt/faq-studio/

# Bağımlılıkları kur
echo "Python bağımlılıkları kuruluyor..."
sudo /opt/faq-studio/venv/bin/pip install -r /opt/faq-studio/requirements.txt

# Timezone düzeltmesi (db.py'de zaten varsa tekrar eklemez)
echo "Timezone ayarı kontrol ediliyor..."
if ! grep -q "SET TIME ZONE" /opt/faq-studio/app/db.py; then
    echo "Timezone ayarı ekleniyor..."
    sudo sed -i '/def get_conn():/a\    # Timezone ayarını yap\n    with conn.cursor() as cur:\n        try:\n            cur.execute("SET TIME ZONE '\''Europe/Istanbul'\''")\n            conn.commit()\n        except Exception as e:\n            print(f"Timezone ayarı yapılamadı: {e}")' /opt/faq-studio/app/db.py
else
    echo "✅ Timezone ayarı zaten mevcut"
fi

# Servisi restart et
echo "Servis restart ediliyor..."
sudo systemctl restart faq-studio

echo "✅ Manuel kurulum tamamlandı!"