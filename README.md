# FAQ Studio

Modern, **AI destekli** bir Soru-Cevap yönetim sistemi.  
FastAPI, PostgreSQL (pgvector) ve Ollama embedding'leri kullanarak soru ekleme, çoğaltma tespiti ve verimli depolama sağlar.

---

## 🚀 Özellikler

### 🤖 AI Destekli
- **Ollama Entegrasyonu:** bge-m3 ve diğer embedding modelleriyle çalışır  
- **Akıllı Çoğaltma Tespiti:** Benzer soruları yapay zeka ile tespit eder  
- **Vektör Arama:** Cosine similarity ile hızlı ve doğru sonuçlar  

### 💾 Veri Yönetimi
- **PostgreSQL + pgvector:** Vektör verileri için optimize edilmiş veritabanı  
- **ChromaDB Entegrasyonu:** Yerel vektör depolama ve arama  
- **JSON Yedekleme:** Verilerin otomatik yedeklenmesi  
- **Kategori Yönetimi:** Esnek kategori sistemi  

### 🎨 Kullanıcı Arayüzü
- **Modern Arayüz:** Koyu tema ve responsive tasarım  
- **Gerçek Zamanlı Arama:** Anında sonuçlar ve filtreleme  
- **İstatistik Paneli:** Kategori bazlı analiz ve grafikler  
- **Detaylı Görüntüleme:** Soru detayları ve düzenleme imkanı  

### ⚙️ Teknik Altyapı
- **FastAPI:** Yüksek performanslı REST API  
- **Docker Hazır:** Container desteği  
- **Debian Paketi:** Kolay kurulum için `.deb` paketi  
- **SystemD Servis:** Otomatik başlatma ve yönetim  

---

## 🔧 Kurulum

### Hızlı Kurulum (Debian/Ubuntu)
```bash
# Debian paketi ile kurulum
chmod +x build-deb.sh
./build-deb.sh
```

### Manuel Kurulum
1. **Gereksinimler:**
```bash
# Python ve bağımlılıkların kurulumu (Debian/Ubuntu)
sudo apt install python3.11 python3.11-venv python3-pip

# Python ve diğer bağımlılıklar
sudo apt install python3.11 python3.11-venv python3-pip
```
2. **Veritabanı Ayarları:**
```bash
# PostgreSQL kullanıcı ve veritabanı oluştur
# Bu proje Aiven PostgreSQL üzerinde çalışacak şekilde ayarlanmıştır.
# Aiven hesabınızda yeni bir PostgreSQL servisi oluşturun.
# Servis oluşturulduğunda size bir connection string (ör: postgres://user:pass@host:port/dbname) verilir.
# Bu bilgiyi .env dosyasında DATABASE_URL olarak ayarlayın.

# Örnek .env
# DATABASE_URL=postgres://faqstudio:your_password@your_aiven_host:your_port/faqdb
# OLLAMA_BASE_URL=http://localhost:11434

# Not: Lokal PostgreSQL kullanacaksanız aşağıdaki adımları uygulayın:
# sudo -u postgres psql -c "CREATE USER faqstudio WITH PASSWORD 'your_password';"
# sudo -u postgres psql -c "CREATE DATABASE faqdb OWNER faqstudio;"
# sudo -u postgres psql -d faqdb -c "CREATE EXTENSION IF NOT EXISTS vector;"
```
3. **Ollama Kurulumu:**
```bash
# Ollama indirme ve kurma
curl -fsSL https://ollama.ai/install.sh | sh

# Model indirme
ollama pull bge-m3
```
4. **Uygulama Kurulumu:**
```bash
# Sanal ortam oluşturma
python3 -m venv venv
source venv/bin/activate

# Bağımlılıkları yükleme
pip install -r requirements.txt

# Ortam değişkenlerini ayarlama
cp config.env.example .env
# .env dosyasını düzenle: DATABASE_URL, OLLAMA_BASE_URL, vb.
```
5. **Veritabanı İnisializasyonu:**
```bash
# (Sadece lokal PostgreSQL için)
python -c "from app.db import init_db; init_db()"
```
6. **Servisleri Başlatma:**
```bash
# Ollama servisi
sudo systemctl start ollama
# FAQ Studio servisi
sudo systemctl start faq-studio
```

---

## 🌐 API Endpoint'leri
| Method | Endpoint            | Açıklama                |
| ------ | ------------------- | ----------------------- |
| GET    | `/`                 | Ana sayfa (HTML arayüz) |
| POST   | `/add`              | Yeni soru ekle          |
| POST   | `/check-duplicate`  | Benzerlik kontrolü      |
| GET    | `/questions/{id}`   | Tekil soru detayı       |
| PUT    | `/questions/{id}`   | Soru güncelleme         |
| DELETE | `/questions/{id}`   | Soru silme              |
| GET    | `/all-questions`    | Tüm soruları listele    |
| GET    | `/stats/categories` | Kategori istatistikleri |
| GET    | `/health`           | Sistem durumu           |

---

## 📖 Kullanım

### Soru Ekleme
1. Ana sayfaya gidin (`http://localhost:8000`)  
2. Soru, cevap ve anahtar kelimeleri girin  
3. Kategori seçin veya yeni kategori ekleyin  
4. **"Benzer Soru Var mı?"** butonu ile kontrol edin  
5. **"Kaydet"** butonu ile ekleyin  

### İstatistikleri Görüntüleme
- **"İstatistikler"** butonuna tıklayın  
- Kategori dağılımını pasta grafikte görün  
- Toplam soru sayısı ve ortalamaları inceleyin  
- Grafiği **PNG** olarak dışa aktarın  

### Son Kayıtları Görüntüleme
- **"Son Kayıtlar"** butonuna tıklayın  
- Arama kutusu ile filtreleme yapın  
- Soruları görüntüleyin veya düzenleyin  
- İstenmeyen kayıtları silin  

---

## 📜 Lisans
Bu proje **MIT lisansı** altında lisanslanmıştır.  
Detaylar için [LICENSE](LICENSE) dosyasına bakın.
