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

# Veri yolu
DATA_FILE = os.path.join(settings.BASE_DIR, 'results_avcilar_trafik2.json')
MODEL_FILE = os.path.join(settings.BASE_DIR, 'trafik_model.joblib')
SCALER_FILE = os.path.join(settings.BASE_DIR, 'scaler.joblib')

def load_and_process_data():
    """JSON verilerini yükleyip DataFrame'e dönüştürür"""
    with open(DATA_FILE, 'r', encoding='utf-8') as file:
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
    
    return df

def train_model():
    """Trafik tahmin modelini eğitir"""
    df = load_and_process_data()
    
    # Eksik verileri doldur
    df = df.fillna(0)
    
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
    speed_model = RandomForestRegressor(n_estimators=100, random_state=42)
    speed_model.fit(X_train_scaled, y_speed_train)
    
    # Seyahat süresi tahmin modeli
    time_model = RandomForestRegressor(n_estimators=100, random_state=42)
    time_model.fit(X_train_scaled, y_time_train)
    
    # Modelleri birleştir
    models = {
        'speed_model': speed_model,
        'time_model': time_model
    }
    
    # Modeli kaydet
    joblib.dump(models, MODEL_FILE)
    joblib.dump(scaler, SCALER_FILE)
    
    # Model performansını değerlendir
    speed_score = speed_model.score(X_test_scaled, y_speed_test)
    time_score = time_model.score(X_test_scaled, y_time_test)
    
    return {
        'speed_score': speed_score,
        'time_score': time_score
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
        
        # Değerlerin mantıklı aralıkta olup olmadığını kontrol et
        if not (40.9 <= lat <= 41.1) or not (28.6 <= lng <= 28.8):
            print(f"Uyarı: Koordinatlar Avcılar bölgesi dışında olabilir: {lat}, {lng}")
    except (ValueError, TypeError) as e:
        print(f"Hata: Koordinat dönüşümünde sorun: {e}")
        # Varsayılan değerler (Avcılar merkez)
        lat = 41.003
        lng = 28.705
    
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
    if os.path.exists(MODEL_FILE) and os.path.exists(SCALER_FILE):
        models = joblib.load(MODEL_FILE)
        scaler = joblib.load(SCALER_FILE)
    else:
        metrics = train_model()
        models = joblib.load(MODEL_FILE)
        scaler = joblib.load(SCALER_FILE)
    
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
    df = load_and_process_data()
    
    # Trafik yoğunluğunu hesapla
    df['traffic_intensity'] = 1 - (df['average_speed'] / df['speed_limit'])
    df.loc[df['traffic_intensity'] < 0, 'traffic_intensity'] = 0
    df.loc[df['traffic_intensity'] > 1, 'traffic_intensity'] = 1
    
    # Harita için verileri hazırla
    heatmap_data = df[['latitude', 'longitude', 'traffic_intensity']].copy()
    
    return heatmap_data.to_dict('records')

def generate_speed_histogram():
    """Hız dağılımı histogramı oluşturur"""
    df = load_and_process_data()
    
    plt.figure(figsize=(10, 6))
    plt.hist(df['average_speed'], bins=20, alpha=0.7, color='blue')
    plt.title('Ortalama Hız Dağılımı')
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