import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
from django.conf import settings
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
import pickle

# Veri ve model dosya yolları
ISTANBUL_DATA_FILE = os.path.join(settings.BASE_DIR, 'datasets', 'results_istanbul_trafik.json')
AVCILAR_DATA_FILE = os.path.join(settings.BASE_DIR, 'results_avcilar_trafik2.json')

# Model dosya yolları
ISTANBUL_MODEL_FILE = os.path.join(settings.BASE_DIR, 'models', 'istanbul_trafik_model.joblib')
ISTANBUL_SCALER_FILE = os.path.join(settings.BASE_DIR, 'models', 'istanbul_scaler.joblib')

# Mevcut Avcılar model dosyaları - geriye dönük uyumluluk için
MODEL_FILE = os.path.join(settings.BASE_DIR, 'trafik_model.joblib')
SCALER_FILE = os.path.join(settings.BASE_DIR, 'scaler.joblib')

# Aktif model ve veri seçimi (varsayılan olarak İstanbul)
ACTIVE_MODEL_FILE = ISTANBUL_MODEL_FILE
ACTIVE_SCALER_FILE = ISTANBUL_SCALER_FILE
ACTIVE_DATA_FILE = ISTANBUL_DATA_FILE

def load_and_process_data(data_file=ACTIVE_DATA_FILE):
    """JSON verilerini yükleyip DataFrame'e dönüştürür"""
    print(f"Veriler yükleniyor: {data_file}")
    
    try:
        with open(data_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Segment verilerini çıkar
        segments = []
        for segment in data["network"]["segmentResults"]:
            segment_id = segment["segmentId"]
            street_name = segment.get("streetName", "Bilinmeyen Cadde")
            speed_limit = segment.get("speedLimit", 0)
            distance = segment.get("distance", 0)
            
            # Şekil bilgisinden orta nokta hesapla
            if "shape" in segment and len(segment["shape"]) > 0:
                lat_sum = sum(point["latitude"] for point in segment["shape"])
                lng_sum = sum(point["longitude"] for point in segment["shape"])
                lat = lat_sum / len(segment["shape"])
                lng = lng_sum / len(segment["shape"])
            else:
                lat, lng = 0, 0
            
            # Zaman sonuçlarını çıkar
            for time_result in segment.get("segmentTimeResults", []):
                segments.append({
                    "segment_id": segment_id,
                    "street_name": street_name,
                    "speed_limit": speed_limit,
                    "distance": distance,
                    "latitude": lat,
                    "longitude": lng,
                    "harmonic_avg_speed": time_result.get("harmonicAverageSpeed", 0),
                    "median_speed": time_result.get("medianSpeed", 0),
                    "average_speed": time_result.get("averageSpeed", 0),
                    "std_dev_speed": time_result.get("standardDeviationSpeed", 0),
                    "travel_time": time_result.get("averageTravelTime", 0),
                    "sample_size": time_result.get("sampleSize", 0),
                })
        
        # DataFrame oluştur
        df = pd.DataFrame(segments)
        
        # Yeni özellikler oluştur
        df['congestion_ratio'] = df['speed_limit'] / df['average_speed']
        df['traffic_density'] = df['sample_size'] / df['distance']
        df['travel_time_per_km'] = (df['travel_time'] / df['distance']) * 1000
        
        print(f"Yüklenen veri sayısı: {len(df)}")
        return df
        
    except Exception as e:
        print(f"Veri yükleme hatası: {e}")
        return pd.DataFrame()

def train_istanbul_model():
    """İstanbul trafik tahmin modelini eğitir"""
    print("İstanbul trafik modeli eğitiliyor...")
    df = load_and_process_data(ISTANBUL_DATA_FILE)
    
    if df.empty:
        print("Veri yüklenemedi, model eğitimi başarısız.")
        return None
    
    # Eksik verileri doldur
    df = df.fillna(0)
    
    # Veri özeti
    print(f"Toplam veri sayısı: {len(df)}")
    print("İlk birkaç satır:")
    print(df.head())
    print("\nSütunlar:", df.columns.tolist())
    print("\nVeri türleri:")
    print(df.dtypes)
    print("\nÖzet istatistikler:")
    print(df.describe())
    
    # Bağımsız ve bağımlı değişkenleri ayır
    X = df[['speed_limit', 'distance', 'sample_size', 'traffic_density', 'latitude', 'longitude']]
    y_speed = df['average_speed']
    y_time = df['travel_time_per_km']
    
    # Veriyi eğitim ve test olarak böl
    X_train, X_test, y_speed_train, y_speed_test = train_test_split(X, y_speed, test_size=0.2, random_state=42)
    _, _, y_time_train, y_time_test = train_test_split(X, y_time, test_size=0.2, random_state=42)
    
    # Verileri ölçeklendir
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Ortalama hız tahmin modeli
    speed_model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    speed_model.fit(X_train_scaled, y_speed_train)
    
    # Seyahat süresi tahmin modeli
    time_model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    time_model.fit(X_train_scaled, y_time_train)
    
    # Modelleri birleştir
    models = {
        'speed_model': speed_model,
        'time_model': time_model
    }
    
    # Modeli kaydet
    print(f"Modeller kaydediliyor: {ISTANBUL_MODEL_FILE}")
    joblib.dump(models, ISTANBUL_MODEL_FILE)
    joblib.dump(scaler, ISTANBUL_SCALER_FILE)
    
    # Varsayılan modeli de güncelle
    global ACTIVE_MODEL_FILE, ACTIVE_SCALER_FILE
    ACTIVE_MODEL_FILE = ISTANBUL_MODEL_FILE
    ACTIVE_SCALER_FILE = ISTANBUL_SCALER_FILE
    
    # Model performansını değerlendir
    speed_score = speed_model.score(X_test_scaled, y_speed_test)
    time_score = time_model.score(X_test_scaled, y_time_test)
    
    print(f"Hız tahmin modeli R² skoru: {speed_score:.4f}")
    print(f"Süre tahmin modeli R² skoru: {time_score:.4f}")
    
    return {
        'speed_score': speed_score,
        'time_score': time_score,
        'model_file': ISTANBUL_MODEL_FILE,
        'scaler_file': ISTANBUL_SCALER_FILE,
        'data_file': ISTANBUL_DATA_FILE,
        'sample_count': len(df)
    }

def predict_traffic(time_of_day, day_of_week, lat, lng, distance):
    """Belirli bir saat, gün ve konum için trafik durumunu tahmin eder"""
    # Saat bilgisini işle
    try:
        if isinstance(time_of_day, str):
            # String formatındaysa saati ayır
            hour = int(time_of_day.split(':')[0])
            minute = int(time_of_day.split(':')[1])
        elif hasattr(time_of_day, 'hour') and hasattr(time_of_day, 'minute'):
            # datetime.time veya datetime.datetime nesnesi ise
            hour = time_of_day.hour
            minute = time_of_day.minute
        else:
            # Bilinmeyen format - varsayılan değerleri kullan
            print(f"Bilinmeyen zaman formatı: {time_of_day}, tipi: {type(time_of_day)}")
            hour = 12
            minute = 0
    except (ValueError, IndexError, AttributeError, TypeError) as e:
        print(f"Zaman dönüştürme hatası: {e}")
        hour = 12
        minute = 0
    
    print(f"Saat ve dakika: {hour}:{minute}")
    
    # Koordinat değerlerini doğru şekilde işle
    try:
        # Ondalık ayırıcı kontrolü
        if isinstance(lat, str):
            lat = lat.replace(',', '.')
        if isinstance(lng, str):
            lng = lng.replace(',', '.')
            
        # Float'a dönüştür
        lat = float(lat)
        lng = float(lng)
        
        # İstanbul için geçerli koordinat aralığı
        if not (40.7 <= lat <= 41.5) or not (28.3 <= lng <= 29.5):
            print(f"Uyarı: Koordinatlar İstanbul bölgesi dışında olabilir: {lat}, {lng}")
    except (ValueError, TypeError) as e:
        print(f"Hata: Koordinat dönüşümünde sorun: {e}")
        # Varsayılan değerler (İstanbul merkez)
        lat = 41.013
        lng = 28.955
    
    # Mesafe kontrolü
    try:
        distance = float(distance)
        if distance <= 0:
            distance = 1.0
    except (ValueError, TypeError):
        distance = 1.0
    
    # Gün değerini dönüştür
    if isinstance(day_of_week, int) and 0 <= day_of_week <= 6:
        day_num = day_of_week
    else:
        day_map = {
            'pazartesi': 0, 'salı': 1, 'çarşamba': 2, 'perşembe': 3, 
            'cuma': 4, 'cumartesi': 5, 'pazar': 6
        }
        
        if isinstance(day_of_week, str) and day_of_week.lower() in day_map:
            day_num = day_map[day_of_week.lower()]
        else:
            try:
                day_num = int(day_of_week) % 7
            except (ValueError, TypeError):
                day_num = 0  # Varsayılan olarak Pazartesi
    
    # Model ve scaler'ı yükle
    if os.path.exists(ACTIVE_MODEL_FILE) and os.path.exists(ACTIVE_SCALER_FILE):
        models = joblib.load(ACTIVE_MODEL_FILE)
        scaler = joblib.load(ACTIVE_SCALER_FILE)
    else:
        # İstanbul modeli yoksa eğit
        if not os.path.exists(ISTANBUL_MODEL_FILE):
            print("İstanbul modeli bulunamadı. Model eğitiliyor...")
            metrics = train_istanbul_model()
            models = joblib.load(ISTANBUL_MODEL_FILE)
            scaler = joblib.load(ISTANBUL_SCALER_FILE)
        # Eski model varsa onu kullan
        elif os.path.exists(MODEL_FILE) and os.path.exists(SCALER_FILE):
            print("Eski Avcılar modeli kullanılıyor...")
            models = joblib.load(MODEL_FILE)
            scaler = joblib.load(SCALER_FILE)
        else:
            # Son çare yeni model eğit
            print("Hiçbir model bulunamadı. Yeni model eğitiliyor...")
            metrics = train_istanbul_model()
            models = joblib.load(ISTANBUL_MODEL_FILE)
            scaler = joblib.load(ISTANBUL_SCALER_FILE)
    
    # Tahmin için girdi verisi hazırla
    # Örnek bir trafik yoğunluğu ve hız limiti ata
    speed_limit = 50
    sample_size = 10000
    traffic_density = sample_size / distance if distance > 0 else 0
    
    input_data = np.array([[speed_limit, distance, sample_size, traffic_density, lat, lng]])
    input_scaled = scaler.transform(input_data)
    
    # Tahmin yap
    predicted_speed = models['speed_model'].predict(input_scaled)[0]
    predicted_time_per_km = models['time_model'].predict(input_scaled)[0]
    
    # Saat faktörü (trafiğin yoğun olduğu saatlerde düzeltme)
    hour_factor = 1.0
    if (hour >= 7 and hour <= 9) or (hour >= 17 and hour <= 19):  # Sabah ve akşam rush saatleri
        hour_factor = 1.5
    elif hour >= 22 or hour <= 5:  # Gece saatleri
        hour_factor = 0.7
    
    # Gün faktörü (hafta içi/sonu faktörü)
    day_factor = 1.0
    if day_num >= 5:  # Hafta sonu
        day_factor = 0.8
    
    # Faktörleri uygula
    adjusted_speed = predicted_speed / (hour_factor * day_factor)
    adjusted_time = predicted_time_per_km * hour_factor * day_factor
    
    # Trafik seviyesini belirle
    traffic_level = get_traffic_level(adjusted_speed, speed_limit)
    
    return {
        'predicted_speed': adjusted_speed,
        'predicted_time_per_km': adjusted_time,
        'total_time': (adjusted_time * distance) / 1000 if distance > 0 else 0,
        'traffic_level': traffic_level  # Artık bir string değeri
    }

def get_traffic_level(speed, speed_limit=50):
    """Hıza göre trafik yoğunluğu seviyesini belirler"""
    if speed_limit == 0:
        speed_limit = 50  # Varsayılan değer
    
    # Hız limitine göre oran hesapla
    ratio = speed / speed_limit if speed_limit > 0 else 0
    
    if ratio >= 0.9:
        return "Açık"
    elif ratio >= 0.75:
        return "Hafif"
    elif ratio >= 0.5:
        return "Yoğun"
    elif ratio >= 0.3:
        return "Çok Yoğun"
    else:
        return "Durma Noktasında"

def get_traffic_color(traffic_level):
    """Trafik seviyesine göre renk döndürür - Bootstrap renk sınıflarıyla uyumlu"""
    colors = {
        "Açık": "success",     # yeşil
        "Hafif": "warning",    # sarı
        "Yoğun": "warning",    # sarı (Bootstrap'ta direkt "orange" yok)
        "Çok Yoğun": "danger", # kırmızı
        "Durma Noktasında": "dark"  # koyu renk (Bootstrap'ta "darkred" yok)
    }
    return colors.get(traffic_level, "secondary")  # varsayılan gri

def get_traffic_heatmap():
    """Trafik yoğunluğu haritası için verileri hazırlar"""
    df = load_and_process_data(ACTIVE_DATA_FILE)
    
    if df.empty:
        # Boş veri durumunda örnek veri döndür
        return []
    
    # Trafik yoğunluğunu hesapla
    df['traffic_intensity'] = 1 - (df['average_speed'] / df['speed_limit'])
    df.loc[df['traffic_intensity'] < 0, 'traffic_intensity'] = 0
    df.loc[df['traffic_intensity'] > 1, 'traffic_intensity'] = 1
    
    # Harita için verileri hazırla - Maksimum nokta sayısını sınırla
    max_points = 5000  # Maksimum nokta sayısı
    
    if len(df) > max_points:
        # Veriyi örnekle
        df_sample = df.sample(max_points, random_state=42)
        heatmap_data = df_sample[['latitude', 'longitude', 'traffic_intensity']].copy()
    else:
        heatmap_data = df[['latitude', 'longitude', 'traffic_intensity']].copy()
    
    return heatmap_data.to_dict('records')

def generate_speed_histogram():
    """Hız dağılımı histogramı oluşturur"""
    df = load_and_process_data(ACTIVE_DATA_FILE)
    
    if df.empty:
        # Boş veri durumunda boş grafik döndür
        plt.figure(figsize=(10, 6))
        plt.title('Veri Bulunamadı')
        plt.xlabel('Hız (km/saat)')
        plt.ylabel('Frekans')
        
        # Grafik görüntüsünü base64'e dönüştür
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(image_png).decode('utf-8')
    
    plt.figure(figsize=(10, 6))
    
    # Aykırı değerleri filtrele
    speed_data = df['average_speed']
    Q1 = speed_data.quantile(0.25)
    Q3 = speed_data.quantile(0.75)
    IQR = Q3 - Q1
    filtered_data = speed_data[(speed_data >= Q1 - 1.5 * IQR) & (speed_data <= Q3 + 1.5 * IQR)]
    
    plt.hist(filtered_data, bins=30, alpha=0.7, color='blue')
    plt.title('İstanbul Ortalama Hız Dağılımı')
    plt.xlabel('Hız (km/saat)')
    plt.ylabel('Frekans')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Grafik görüntüsünü base64'e dönüştür
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    return base64.b64encode(image_png).decode('utf-8')
    
# İstanbul modeli eğitme fonksiyonu - doğrudan çağrılabilir
def train_model_command():
    """Komut satırından çağrılabilecek model eğitim fonksiyonu"""
    print("İstanbul trafik veri seti ile model eğitiliyor...")
    
    # Klasörleri kontrol et
    os.makedirs(os.path.dirname(ISTANBUL_MODEL_FILE), exist_ok=True)
    
    # Modeli eğit
    result = train_istanbul_model()
    
    if result:
        print("\nModel eğitimi tamamlandı!")
        print(f"Model dosyası: {result['model_file']}")
        print(f"Scaler dosyası: {result['scaler_file']}")
        print(f"Veri dosyası: {result['data_file']}")
        print(f"Veri sayısı: {result['sample_count']}")
        print(f"Hız model başarısı: {result['speed_score']:.4f}")
        print(f"Süre model başarısı: {result['time_score']:.4f}")
    else:
        print("Model eğitimi başarısız oldu.")
    
    return result

# Model yükleme fonksiyonu
def load_model():
    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'traffic_model.pkl')
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

# Hafta içi/sonu kontrolü
def is_weekend(date):
    # date string formatı: YYYY-MM-DD
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    # Hafta içi (0: Pazartesi, 1: Salı, ..., 4: Cuma)
    # Hafta sonu (5: Cumartesi, 6: Pazar)
    return 1 if date_obj.weekday() >= 5 else 0

# Saatin sayısal temsili (0-23)
def get_hour_of_day(time_str):
    # time string formatı: HH:MM
    hour = int(time_str.split(':')[0])
    return hour

# Gün tipi (0: hafta içi, 1: hafta sonu, 2: tatil)
def get_day_type(date):
    # Şu an sadece hafta içi ve hafta sonu destekleniyor
    # TODO: Resmi tatil desteği eklenebilir
    return 1 if is_weekend(date) else 0

# Trafik tahmini yapma fonksiyonu
def predict_traffic(model, date, time, lat, lng):
    hour = get_hour_of_day(time)
    day_type = get_day_type(date)
    
    # Tahmin için özellikleri hazırla
    X = np.array([[lat, lng, hour, day_type]])
    
    # Tahmin yap
    prediction = model.predict(X)[0]
    
    return prediction

# Trafik seviyesini belirle (0: Çok Düşük, 1: Düşük, 2: Orta, 3: Yüksek, 4: Çok Yüksek)
def get_traffic_level(prediction):
    if prediction < 0.2:
        return 0  # Çok Düşük
    elif prediction < 0.4:
        return 1  # Düşük
    elif prediction < 0.6:
        return 2  # Orta
    elif prediction < 0.8:
        return 3  # Yüksek
    else:
        return 4  # Çok Yüksek

# Trafik seviyesine göre renk kodu döndür
def get_traffic_color(traffic_level):
    colors = {
        0: "#00FF00",  # Yeşil (Çok Düşük)
        1: "#80FF00",  # Açık Yeşil (Düşük)
        2: "#FFFF00",  # Sarı (Orta)
        3: "#FF8000",  # Turuncu (Yüksek)
        4: "#FF0000",  # Kırmızı (Çok Yüksek)
    }
    return colors.get(traffic_level, "#CCCCCC")  # Varsayılan gri renk

# Route için tahmin
def predict_route(model, date, time, route_coordinates):
    predictions = []
    
    for point in route_coordinates:
        lat, lng = point
        prediction = predict_traffic(model, date, time, lat, lng)
        traffic_level = get_traffic_level(prediction)
        traffic_color = get_traffic_color(traffic_level)
        
        predictions.append({
            'lat': lat,
            'lng': lng,
            'prediction': prediction,
            'traffic_level': traffic_level,
            'traffic_color': traffic_color
        })
    
    return predictions

# Rota üzerindeki ortalama trafik seviyesi
def calculate_average_traffic(predictions):
    if not predictions:
        return 0, "#00FF00"  # Varsayılan değer
    
    avg_prediction = sum(p['prediction'] for p in predictions) / len(predictions)
    avg_traffic_level = get_traffic_level(avg_prediction)
    avg_traffic_color = get_traffic_color(avg_traffic_level)
    
    return avg_traffic_level, avg_traffic_color

# Tahmini hız hesaplama (km/sa)
def estimate_speed(traffic_level):
    # Trafik seviyesine göre tahmini hız
    speeds = {
        0: 70,  # Çok düşük trafik: ~70 km/sa
        1: 55,  # Düşük trafik: ~55 km/sa
        2: 40,  # Orta trafik: ~40 km/sa
        3: 25,  # Yüksek trafik: ~25 km/sa
        4: 10,  # Çok yüksek trafik: ~10 km/sa
    }
    return speeds.get(traffic_level, 30)  # Varsayılan 30 km/sa

# Tahmini süre hesaplama (dakika)
def estimate_duration(distance, traffic_level):
    speed = estimate_speed(traffic_level)  # km/sa
    
    # Mesafe (km) / Hız (km/sa) * 60 = Süre (dakika)
    duration = (distance / speed) * 60
    
    return round(duration) 