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

def predict_traffic(model, date, time, lat, lng):
    hour = get_hour_of_day(time)
    day_type = get_day_type(date)
    
    # Modelin eğitildiği veri setine bakarak, eksik özellikler için varsayılan değerler ekliyoruz
    speed_limit = 50  # Varsayılan hız limiti
    distance = 1.0    # Varsayılan mesafe (km)
    sample_size = 10000  # Varsayılan örnek sayısı
    traffic_density = sample_size / distance  # Varsayılan yoğunluk
    
    # Tahmin için özellikleri hazırla - modelin eğitildiği ile aynı sırada olmalı
    X = np.array([[speed_limit, distance, sample_size, traffic_density, lat, lng]])
    
    # Model bir sözlük ise
    if isinstance(model, dict) and 'speed_model' in model:
        # Eğer scaler varsa ölçeklendirme yap
        scaler_path = os.path.join(settings.BASE_DIR, 'models', 'istanbul_scaler.joblib')
        if os.path.exists(scaler_path):
            try:
                scaler = joblib.load(scaler_path)
                X_scaled = scaler.transform(X)
                prediction = model['speed_model'].predict(X_scaled)[0]
            except Exception as e:
                print(f"Ölçeklendirme hatası: {e}")
                # Hata durumunda ölçeklendirme yapmadan dene
                prediction = model['speed_model'].predict(X)[0]
        else:
            # Scaler yoksa direkt tahmin yap
            prediction = model['speed_model'].predict(X)[0]
    else:
        # Tek model durumu için
        try:
            prediction = model.predict(X)[0]
        except AttributeError as e:
            print(f"Model tahmin hatası: {e}")
            prediction = 0.5
    
    return prediction

def get_traffic_level(prediction, speed_limit=50):
    """
    Tahmin değerine göre trafik seviyesini belirler.
    
    Args:
        prediction: Modelin ürettiği tahmin değeri (0-1 arasında)
                  Düşük değerler iyi trafik koşullarını,
                  Yüksek değerler kötü trafik koşullarını gösterir
        speed_limit: Eğer prediction bir hız değeri ise, bu parametreyi kullan
    
    Returns:
        int: 0 (Çok Düşük) ile 4 (Çok Yüksek) arasında trafik seviyesi
    """
    # Eğer prediction 1'den büyükse, hız değeri olarak işle
    if prediction > 1:
        # Hız değeri için oran hesapla
        ratio = prediction / speed_limit if speed_limit > 0 else 0
        
        if ratio >= 0.9:
            return 0  # Çok Düşük (hız yüksek = trafik az)
        elif ratio >= 0.75:
            return 1  # Düşük
        elif ratio >= 0.5:
            return 2  # Orta
        elif ratio >= 0.3:
            return 3  # Yüksek
        else:
            return 4  # Çok Yüksek (hız düşük = trafik yoğun)
    else:
        # 0-1 arası bir prediction değeri için
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

def get_traffic_color(traffic_level):
    """
    Trafik seviyesine göre renk kodu döndürür.
    
    Args:
        traffic_level (int): 0-4 arasında trafik seviyesi
            0: Çok Düşük, 1: Düşük, 2: Orta, 3: Yüksek, 4: Çok Yüksek
            
    Returns:
        str: Hex renk kodu
    """
    colors = {
        0: "#00FF00",  # Yeşil (Çok Düşük)
        1: "#80FF00",  # Açık Yeşil (Düşük)
        2: "#FFFF00",  # Sarı (Orta)
        3: "#FF8000",  # Turuncu (Yüksek)
        4: "#FF0000",  # Kırmızı (Çok Yüksek)
    }
    return colors.get(traffic_level, "#CCCCCC")  # Varsayılan gri renk

def get_traffic_heatmap():
    """Trafik yoğunluğu haritası için verileri hazırlar"""
    df = load_and_process_data(ACTIVE_DATA_FILE)
    
    if df.empty:
        # Boş veri durumunda örnek veri döndür
        return []
    
    # Trafik yoğunluğunu hesapla
    # Düşük hız = yüksek trafik yoğunluğu
    # Hız limiti 50 km/sa ise ve ortalama hız 10 km/sa ise, trafik yoğunluğu 0.8 olmalı
    # Formula: 1 - (ortalama_hız / hız_limiti)
    df['traffic_intensity'] = 1 - (df['average_speed'] / df['speed_limit'])
    
    # 0-1 aralığına normalizasyon
    df.loc[df['traffic_intensity'] < 0, 'traffic_intensity'] = 0
    df.loc[df['traffic_intensity'] > 1, 'traffic_intensity'] = 1
    
    # Harita için verileri hazırla - Maksimum nokta sayısını sınırla
    max_points = 5000  # Maksimum nokta sayısı
    
    if len(df) > max_points:
        # Veriyi örnekle - ağırlıklı örnekleme (yüksek yoğunluklu noktaları daha fazla seç)
        weights = df['traffic_intensity'] * 2 + 0.1  # Yüksek yoğunluklu noktalar daha fazla seçilsin
        df_sample = df.sample(max_points, weights=weights, random_state=42)
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
    model_path = os.path.join(settings.BASE_DIR, 'models', 'istanbul_trafik_model.joblib')
    
    # Eğer model bulunamazsa, modeli eğit ve oluştur
    if not os.path.exists(model_path):
        print(f"Model bulunamadı: {model_path}")
        print("Model eğitiliyor...")
        train_istanbul_model()
    
    # Modeli yükle
    try:
        return joblib.load(model_path)
    except Exception as e:
        print(f"Model yükleme hatası: {e}")
        # Yedek yol - ilk modeli eğit ve döndür
        print("Model yeniden eğitiliyor...")
        train_istanbul_model()
        return joblib.load(model_path)

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