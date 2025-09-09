#!/bin/bash

echo "=== FAQ Studio Debian Package Builder ==="

# Temizlik
echo "Temizlik yapılıyor..."
rm -f faq-studio_*.deb 2>/dev/null

# İzinleri düzelt
echo "İzinleri ayarlıyor..."
find debian -type d -exec chmod 755 {} \; 2>/dev/null
find debian -type f -exec chmod 644 {} \; 2>/dev/null
chmod 755 debian/DEBIAN/postinst 2>/dev/null || true
chmod 755 debian/DEBIAN/prerm 2>/dev/null || true
chmod 755 debian/DEBIAN/postrm 2>/dev/null || true

# Paket oluşturma
echo "Debian paketi oluşturuluyor..."
if dpkg-deb --build debian; then
    mv debian.deb faq-studio_1.0.0_amd64.deb
    echo "✅ Paket oluşturuldu: faq-studio_1.0.0_amd64.deb"
    
    # Otomatik kurulum
    echo ""
    echo "Kurulum yapılıyor..."
    sudo dpkg -i faq-studio_1.0.0_amd64.deb
    
    # Bağımlılık hatası olursa onar
    if [ $? -ne 0 ]; then
        echo "Bağımlılık hata onarımı yapılıyor..."
        sudo apt-get install -f
        echo "✅ Onarım tamamlandı!"
    fi
    
    echo "✅ Kurulum tamamlandı!"
    echo ""
    echo "Servis durumunu kontrol etmek için:"
    echo "sudo systemctl status faq-studio"
else
    echo "❌ Paket oluşturulamadı!"
    exit 1
fi