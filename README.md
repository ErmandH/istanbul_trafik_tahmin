# Avcılar Trafik Tahmin Projesi

Bu proje, Avcılar bölgesindeki trafik verilerini kullanarak sıkışıklık tahminleri ve rota optimizasyonu sağlamak amacıyla geliştirilmiştir.

## Proje Özellikleri

- Trafik sıkışıklığı tahmini
- Rota optimizasyonu
- Günün farklı saatleri için trafik durumu analizi
- İnteraktif harita görselleştirmeleri

## Kurulum

1. Python 3.8+ kurulu olduğundan emin olun.
2. Sanal ortam oluşturun ve aktifleştirin:
   ```
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```
3. Gerekli paketleri yükleyin:
   ```
   pip install -r requirements.txt
   ```
4. Veritabanını migrate edin:
   ```
   python manage.py migrate
   ```
5. Geliştirme sunucusunu başlatın:
   ```
   python manage.py runserver
   ```

## Veri Seti

Proje, Avcılar bölgesinde 1-31 Ağustos 2024 tarihleri arasında toplanan trafik verilerini kullanmaktadır. Veri seti, yol segmentleri için hız bilgileri, trafik akış oranları ve seyahat süreleri içermektedir.

## Kullanım

Web tarayıcınızdan `http://127.0.0.1:8000` adresine giderek uygulamayı kullanabilirsiniz.

- Harita üzerinde başlangıç ve varış noktalarını seçin
- Seyahat zamanınızı belirleyin
- Sistem size en uygun rotayı ve tahmini seyahat süresini gösterecektir
