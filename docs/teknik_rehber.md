# İstanbul Trafik Tahmin Sistemi - Teknik Rehber

Bu doküman, İstanbul Trafik Tahmin Sistemi'nin teknik detaylarını, kod yapısını ve geliştirme süreçlerini içermektedir. Bu rehber, projeyi geliştirmek veya genişletmek isteyen geliştiriciler için hazırlanmıştır.

## Teknoloji Yığını

Proje aşağıdaki teknolojileri kullanmaktadır:

- **Backend**: Django 3.2+
- **Veritabanı**: SQLite (Geliştirme), PostgreSQL (Üretim için önerilir)
- **Makine Öğrenimi**: scikit-learn 1.0+
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Harita**: Leaflet.js
- **Veri Analizi**: pandas, numpy
- **Veri Görselleştirme**: matplotlib

## Proje Yapısı

```
trafik_tahmin/         # Ana Django projesi
│
├── trafik_app/        # Trafik tahmin uygulaması
│   ├── migrations/    # Veritabanı migrasyon dosyaları
│   ├── static/        # Statik dosyalar (CSS, JS, resimler)
│   │   └── trafik_app/
│   │       ├── css/   # CSS dosyaları
│   │       ├── js/    # JavaScript dosyaları
│   │       └── img/   # Görsel dosyalar
│   ├── templates/     # HTML şablonları
│   │   └── trafik_app/
│   │       ├── index.html     # Ana sayfa
│   │       ├── sonuc.html     # Tahmin sonuçları sayfası
│   │       └── base.html      # Temel şablon
│   ├── __init__.py
│   ├── admin.py       # Django admin yapılandırması
│   ├── apps.py        # Uygulama yapılandırması
│   ├── forms.py       # Form tanımları
│   ├── models.py      # Veritabanı modelleri
│   ├── urls.py        # URL yönlendirmeleri
│   ├── views.py       # Görünümler (Controller)
│   └── model_utils.py # Makine öğrenimi modeli yardımcıları
│
├── datasets/          # Trafik veri setleri
│   ├── results_istanbul_trafik.json
│   └── results_avcilar_trafik2.json
│
├── models/            # Eğitilmiş modeller
│   ├── istanbul_trafik_model.joblib
│   └── istanbul_scaler.joblib
│
├── docs/              # Dokümantasyon
│
├── venv/              # Sanal ortam
├── manage.py          # Django yönetim scripti
├── requirements.txt   # Bağımlılıklar
└── README.md          # Proje açıklaması
```

## Modüllerin Detaylı Açıklaması

### models.py

Django ORM modellerini içerir:

1. **TrafikSegment**: Yol segmentlerini tanımlar

   - Birincil anahtar özellikler: segment_id
   - Konum ve mesafe bilgilerini içerir

2. **TrafikVeri**: Segmentlere ait trafik ölçümlerini saklar

   - Her bir ölçüm, belirli bir segment ve zaman için hız ve seyahat süresi bilgilerini içerir
   - TrafikSegment'e ForeignKey ile bağlıdır

3. **TrafikTahmin**: Kullanıcıların tahmin isteklerini ve sonuçlarını saklar
   - Tahmin edilen hız ve seyahat süresi değerlerini içerir

### model_utils.py

Makine öğrenimi modellerinin eğitimi, değerlendirilmesi ve tahminlerin yapılması için fonksiyonları içerir:

1. **load_and_process_data**: JSON formatındaki trafik verilerini yükler ve DataFrame'e dönüştürür

   - Eksik değerleri doldurur
   - Trafik yoğunluğu gibi türetilmiş özellikler oluşturur

2. **train_istanbul_model**: İstanbul trafik tahmin modelini eğitir

   - RandomForestRegressor modelleri oluşturur
   - Modelleri ve ölçeklendiriciyi kaydeder
   - Model performansını rapor eder

3. **predict_traffic**: Belirli bir konum ve zaman için trafik durumunu tahmin eder

   - Modeli ve gerekli ölçeklendiriciyi yükler
   - Tahmin yapacak X verisini hazırlar
   - Tahmini döndürür

4. **get_traffic_level/get_traffic_color**: Tahmin edilen hıza göre trafik seviyesini ve görselleştirme rengini belirler

   - Akıcı (yeşil), Yoğun (sarı), Sıkışık (kırmızı), Durağan (siyah)

5. **get_traffic_heatmap**: Isı haritası için trafik yoğunluğu verilerini hazırlar

6. **generate_speed_histogram**: Hız dağılımını gösteren histogram oluşturur

### views.py

Django görünüm fonksiyonlarını içerir:

1. **index**: Ana sayfa görünümü

   - Isı haritası verilerini ve hız histogramını hazırlar

2. **tahmin**: Tahmin formunu işler ve tahmin yapar

   - Tek nokta veya rota tahmini yapabilir
   - Tahmin sonuçlarını veritabanına kaydeder
   - Sonuçları görselleştirmek için gerekli verileri hazırlar

3. **sonuc**: Tahmin sonuçlarını görüntüler

4. **trafik_verisi**: API benzeri bir görünüm, JSON formatında trafik verilerini döndürür

### map_utils.js

Harita işlemlerini yöneten JavaScript fonksiyonlarını içerir:

1. **initLocationMap**: Tek bir konum için harita başlatır

   - Konum değerlerini kontrol eder
   - Harita katmanı ve işaretleyici ekler
   - Trafik durumuna göre renkli gösterge oluşturur

2. **initHeatmap**: Trafik yoğunluğunu gösteren ısı haritası oluşturur

   - Leaflet.heat eklentisini kullanır
   - Trafik verilerini ısı noktalarına dönüştürür

3. **resizeMap**: Haritayı pencere boyutuna göre yeniden boyutlandırır

## API Referansı

### Tahmin API'si

Aşağıdaki parametrelerle bir POST isteği yapılarak kullanılır:

- **route_type**: 'single' veya 'route'
- **date**: YYYY-MM-DD formatında tarih
- **time**: HH:MM formatında saat
- **lat/lng**: Konum koordinatları (tek nokta tahmini için)
- **start_point/end_point**: Başlangıç ve bitiş koordinatları (rota tahmini için)
- **route_coordinates**: Rota üzerindeki koordinatlar dizisi (JSON formatında)
- **distance**: Mesafe (km)

### Trafik Verisi API'si

GET isteği ile trafik verilerine erişim sağlar. Aşağıdaki parametreleri destekler:

- **segment_id**: Belirli bir segment için filtreleme
- **date**: Belirli bir tarih için filtreleme
- **limit**: Maksimum sonuç sayısı

## Model Eğitimi

Makine öğrenimi modellerini yeniden eğitmek için aşağıdaki adımları izleyin:

1. En güncel veri setlerini `datasets/` dizinine yerleştirin
2. Django shell'i başlatın:
   ```
   python manage.py shell
   ```
3. Model eğitim fonksiyonlarını çağırın:
   ```python
   from trafik_app.model_utils import train_istanbul_model
   results = train_istanbul_model()
   print(results)  # Model performans metrikleri
   ```

### Model Performansı İyileştirme

Model performansını artırmak için şu stratejileri uygulayabilirsiniz:

1. **Özellik Mühendisliği**:

   - Günün saati, hafta içi/sonu gibi zaman özellikleri ekleyin
   - Trafik yoğunluğu için yeni metrikler oluşturun

2. **Hiperparametre Optimizasyonu**:

   ```python
   from sklearn.model_selection import GridSearchCV
   param_grid = {
       'n_estimators': [100, 200, 300],
       'max_depth': [None, 10, 20, 30],
       'min_samples_split': [2, 5, 10]
   }
   grid_search = GridSearchCV(RandomForestRegressor(), param_grid, cv=5)
   grid_search.fit(X_train_scaled, y_speed_train)
   best_params = grid_search.best_params_
   ```

3. **Farklı Algoritmalar Deneme**:
   - GradientBoostingRegressor
   - XGBoost
   - LightGBM

## Harita Özelleştirme

Leaflet.js haritalarını özelleştirmek için:

1. **Harita Katmanı Değiştirme**:

   ```javascript
   // map_utils.js - Farklı bir harita katmanı kullanma
   L.tileLayer("https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png", {
     attribution:
       '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/" target="_blank">HOT</a>',
   }).addTo(map);
   ```

2. **Isı Haritası Renk Paletini Değiştirme**:

   ```javascript
   // map_utils.js - Isı haritası renklerini değiştirme
   L.heatLayer(heatPoints, {
     radius: 20,
     blur: 15,
     maxZoom: 17,
     gradient: {
       0.2: "#00FFFF",
       0.4: "#00FF00",
       0.6: "#FFFF00",
       0.8: "#FF7F00",
       1.0: "#FF0000",
     },
   }).addTo(map);
   ```

3. **Harita Kontrolleri Ekleme**:

   ```javascript
   // Yakınlaştırma/uzaklaştırma kontrolünü özelleştirme
   map.zoomControl.setPosition("topright");

   // Ölçek kontrolü ekleme
   L.control.scale().addTo(map);
   ```

## Frontend Geliştirme

Kullanıcı arayüzü geliştirmeleri için Bootstrap ve JavaScript kullanılarak yapılabilecek özelleştirmeler:

1. **Formları Geliştirme**:

   - Bootstrap Form Validation ile form doğrulama ekleyin
   - AJAX ile formları gönderin (sayfa yenilemeden)

2. **Harita Etkileşimini Artırma**:

   - Sağ tıklama ile konum seçme
   - Rota çizme araçları ekleme
   - Harita katmanlarını açıp kapatabilme

3. **Gösterge Paneli Ekleme**:
   - Trafik istatistiklerini gösterecek grafikler
   - Gerçek zamanlı trafik güncellemeleri için WebSocket entegrasyonu

## Güvenlik Hususları

1. **Django Güvenlik Ayarları**:

   - `SECRET_KEY` değerini çevresel değişkenlerden okuma
   - HTTPS kullanımı
   - CSRF korumasını etkinleştirme

2. **API Güvenliği**:

   - İstek limitleme (throttling)
   - Kullanıcı kimlik doğrulama ve yetkilendirme

3. **Model ve Veri Dosyaları**:
   - Hassas veri dosyalarını .gitignore'a ekleme
   - Veri şifreleme (gerektiğinde)

## Hata Yakalama ve Günlük Tutma

Model eğitimi ve tahmin süreçlerinde hata yakalaması için örnek kod:

```python
try:
    model = load_model()
    prediction = model.predict(X)
except FileNotFoundError:
    logger.error("Model dosyası bulunamadı")
    # Yedek bir model kullan veya varsayılan değer döndür
except Exception as e:
    logger.error(f"Tahmin hatası: {str(e)}")
    # Hata durumunda güvenli bir varsayılan değer döndür
```

## Performans İzleme

Model performansını ve sistem kaynak kullanımını izlemek için:

1. **Model Performansı**:

   - Belirli aralıklarla test verileri üzerinde değerlendirme
   - Tahmin hatalarını kaydetme ve analiz etme

2. **Sistem Performansı**:
   - Django Debug Toolbar kullanma
   - Veritabanı sorgu optimizasyonu
   - Memcached veya Redis ile önbelleğe alma

## Kaynaklar ve Referanslar

- [Django Dokümantasyonu](https://docs.djangoproject.com/)
- [scikit-learn Dokümantasyonu](https://scikit-learn.org/stable/documentation.html)
- [Leaflet.js Dokümantasyonu](https://leafletjs.com/reference.html)
- [Bootstrap Dokümantasyonu](https://getbootstrap.com/docs/)
- [Trafik Veri Seti Kaynağı](https://data.ibb.gov.tr/)

---

Bu teknik rehber, İstanbul Trafik Tahmin Sistemi'nin temel bileşenlerini, geliştirme süreçlerini ve özelleştirme seçeneklerini açıklamaktadır. Daha fazla yardım veya sorularınız için proje yöneticileriyle iletişime geçebilirsiniz.
