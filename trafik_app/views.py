from django.shortcuts import render, redirect
from django.http import JsonResponse
from . import model_utils
from .model_utils import predict_traffic, get_traffic_heatmap, generate_speed_histogram, get_traffic_level, get_traffic_color
from .forms import TrafikForm
import json
from datetime import datetime
import numpy as np
import os
import joblib
from django.conf import settings


def get_turkish_day_name(day_of_week):
    """Haftanın gün numarasına göre Türkçe gün adını döndürür"""
    days = {
        0: "Pazartesi",
        1: "Salı",
        2: "Çarşamba",
        3: "Perşembe",
        4: "Cuma",
        5: "Cumartesi",
        6: "Pazar"
    }
    return days.get(day_of_week, "Bilinmeyen Gün")

def index(request):
    """Ana sayfa görünümü"""
    try:
        # Force refresh parametresini al
        force_refresh = request.GET.get('refresh', '0') == '1'
        
        # Admin kullanıcısıysa ve refresh isteniyorsa yenile
        if force_refresh and request.user.is_superuser:
            heatmap_data = model_utils.get_traffic_heatmap(force_refresh=False)
            refresh_message = "Isı haritası ve histogram yenilendi! Nokta sayısı: " + str(len(heatmap_data))
        else:
            # Normal durumda önbellekten al
            heatmap_data = model_utils.get_traffic_heatmap(force_refresh=False)
            refresh_message = None
        
        context = {
            'heatmap_data': json.dumps(heatmap_data),
            'refresh_message': refresh_message,
            'is_admin': request.user.is_superuser,
            'points_count': len(heatmap_data)
        }
        return render(request, 'trafik_app/index.html', context)
    except Exception as e:
        # Hata durumunda boş bir sayfa göster
        print(f"Hata: {str(e)}")
        return render(request, 'trafik_app/index.html', {'error': str(e)})

def tahmin(request):
    if request.method == 'POST':
        # Form verilerini al
        route_type = request.POST.get('route_type', 'single')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        
        # Tarih ve saat bilgisini işle
        try:
            date_obj = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            hour = date_obj.hour
            minute = date_obj.minute
            day_of_week = date_obj.weekday()  # 0-6 arası (Pazartesi-Pazar)
            
            # Tarih ve saat formatını hazırla - model fonksiyonları için
            formatted_date = date_obj.strftime('%Y-%m-%d')
            formatted_time = date_obj.strftime('%H:%M')
        except ValueError as e:
            # Tarih/saat biçimi hatalıysa varsayılan değerler kullan
            print(f"Tarih/saat biçimi hatalı: {e}")
            hour = 8
            minute = 0
            day_of_week = 0
            formatted_date = "2023-01-01"  # Pazartesi varsayılan
            formatted_time = "08:00" 
        
        # Tek nokta mı yoksa rota mı olduğuna göre işlem yap
        if route_type == 'single':
            # Tek nokta tahmini
            try:
                lat = float(request.POST.get('lat', 0))
                lng = float(request.POST.get('lng', 0))
            except ValueError:
                lat = 41.0082  # İstanbul varsayılan
                lng = 28.9784
            
            # Tahmin yapmak için model yükle
            model = model_utils.load_model()
            
            # Tahmin yap - model bir sözlük olduğunda doğru model seçiliyor
            if isinstance(model, dict) and 'speed_model' in model:
                # X verisini hazırla - modelin beklediği gibi 6 özellik içermeli
                speed_limit = 50  # Varsayılan hız limiti
                distance = 1.0    # Varsayılan mesafe (km)
                sample_size = 10000  # Varsayılan örnek sayısı
                traffic_density = sample_size / distance  # Varsayılan yoğunluk
                
                # Eğer scaler varsa ölçeklendirme yap
                scaler_path = os.path.join(settings.BASE_DIR, 'models', 'istanbul_scaler.joblib')
                
                X = np.array([[speed_limit, distance, sample_size, traffic_density, lat, lng]])
                
                if os.path.exists(scaler_path):
                    try:
                        scaler = joblib.load(scaler_path)
                        X_scaled = scaler.transform(X)
                        prediction = model['speed_model'].predict(X_scaled)[0]
                    except Exception as e:
                        print(f"Ölçeklendirme hatası: {e}")
                        prediction = model['speed_model'].predict(X)[0]
                else:
                    prediction = model['speed_model'].predict(X)[0]
            else:
                # model_utils üzerinden tahmin yap
                prediction = model_utils.predict_traffic(model, formatted_date, formatted_time, lat, lng)
            
            # Trafik seviyesini ve rengini al
            print("Prediction: ", prediction)
            traffic_level = model_utils.get_traffic_level(prediction)
            traffic_color = model_utils.get_traffic_color(traffic_level)
            
            # Sonuç nesnesini oluştur
            result = {
                'lat': lat,
                'lng': lng,
                'traffic_level': traffic_level,
                'traffic_color': traffic_color,
                'prediction': prediction,
                'route_type': 'single',
                'date': date_obj.strftime('%d.%m.%Y'),
                'time': date_obj.strftime('%H:%M')
            }
            
            # Sonuç sayfasını göster
            return render(request, 'trafik_app/sonuc.html', {'result': result})
        else:
            # Rota tahmini
            start_point = request.POST.get('start_point', '')
            end_point = request.POST.get('end_point', '')
            route_coordinates_str = request.POST.get('route_coordinates', '[]')
            distance = float(request.POST.get('distance', 1.0))
            
            # Koordinatları parse et
            try:
                route_coordinates = json.loads(route_coordinates_str)
                # Start ve end point'leri ayır
                start_lat, start_lng = map(float, start_point.split(','))
                end_lat, end_lng = map(float, end_point.split(','))
            except:
                # Parse hatası durumunda boş liste
                route_coordinates = []
                start_lat, start_lng = 41.0082, 28.9784
                end_lat, end_lng = 41.0255, 29.0097
            
            # Tahmin yapmak için model yükle
            model = model_utils.load_model()
            
            # Tarih ve saat formatını hazırla
            formatted_date = date_obj.strftime('%Y-%m-%d')
            formatted_time = date_obj.strftime('%H:%M')
            
            # Rota tahmini yap
            if route_coordinates:
                # Model yapısına göre rota tahmini yap
                if isinstance(model, dict) and 'speed_model' in model:
                    # Her nokta için tahmin yap
                    route_predictions = []
                    for point in route_coordinates:
                        lat, lng = point
                        # X verisini hazırla - modelin beklediği gibi 6 özellik içermeli
                        speed_limit = 50  # Varsayılan hız limiti
                        distance_segment = 1.0  # Varsayılan mesafe (km) - segment başına
                        sample_size = 10000  # Varsayılan örnek sayısı
                        traffic_density = sample_size / distance_segment  # Varsayılan yoğunluk
                        
                        X = np.array([[speed_limit, distance_segment, sample_size, traffic_density, lat, lng]])
                        
                        # Eğer scaler varsa ölçeklendirme yap
                        scaler_path = os.path.join(settings.BASE_DIR, 'models', 'istanbul_scaler.joblib')
                        
                        if os.path.exists(scaler_path):
                            try:
                                scaler = joblib.load(scaler_path)
                                X_scaled = scaler.transform(X)
                                prediction = model['speed_model'].predict(X_scaled)[0]
                            except Exception as e:
                                print(f"Rota ölçeklendirme hatası: {e}")
                                prediction = model['speed_model'].predict(X)[0]
                        else:
                            prediction = model['speed_model'].predict(X)[0]
                        
                        # Trafik seviyesi ve renk
                        traffic_level = model_utils.get_traffic_level(prediction)
                        traffic_color = model_utils.get_traffic_color(traffic_level)
                        
                        route_predictions.append({
                            'lat': lat,
                            'lng': lng,
                            'prediction': prediction,
                            'traffic_level': traffic_level,
                            'traffic_color': traffic_color
                        })
                else:
                    # model_utils üzerinden rota tahmini yap
                    route_predictions = model_utils.predict_route(model, formatted_date, formatted_time, route_coordinates)
                
                avg_traffic_level, avg_traffic_color = model_utils.calculate_average_traffic(route_predictions)
                estimated_speed = model_utils.estimate_speed(avg_traffic_level)
                estimated_duration = model_utils.estimate_duration(distance, avg_traffic_level)
            else:
                route_predictions = []
                avg_traffic_level = 0
                avg_traffic_color = model_utils.get_traffic_color(avg_traffic_level)
                estimated_speed = model_utils.estimate_speed(avg_traffic_level)
                estimated_duration = model_utils.estimate_duration(distance, avg_traffic_level)
            
            # Sonuç nesnesini oluştur
            result = {
                'route_type': 'route',
                'start_point': {'lat': start_lat, 'lng': start_lng},
                'end_point': {'lat': end_lat, 'lng': end_lng},
                'route_coordinates': route_coordinates,
                'route_predictions': route_predictions,
                'avg_traffic_level': avg_traffic_level,
                'avg_traffic_color': avg_traffic_color,
                'distance': distance,
                'estimated_speed': estimated_speed,
                'estimated_duration': estimated_duration,
                'date': date_obj.strftime('%d.%m.%Y'),
                'time': date_obj.strftime('%H:%M')
            }
            
            # Sonuç sayfasını göster
            return render(request, 'trafik_app/sonuc.html', {'result': result})
    
    # GET isteği durumunda tahmin formunu göster
    return render(request, 'trafik_app/tahmin.html')

def sonuc(request):
    """Tahmin sonuçları görünümü"""
    if request.method == 'POST':
        form = TrafikForm(request.POST)
        if form.is_valid():
            # Form verilerini al
            date_obj = form.cleaned_data['tarih']  # Bu zaten bir datetime.date nesnesi
            time_obj = form.cleaned_data['saat']   # Bu da datetime.time nesnesi
            location = form.cleaned_data['konum']
            distance = form.cleaned_data['mesafe']
            
            # Yeni rota bilgileri
            start_point = request.POST.get('start_point', '')
            end_point = request.POST.get('end_point', '')
            route_coordinates_json = request.POST.get('route_coordinates', '')
            
            # Debug bilgisi
            print(f"Form verileri: tarih={date_obj} ({type(date_obj)}), saat={time_obj} ({type(time_obj)})")
            print(f"Başlangıç: {start_point}, Bitiş: {end_point}, Mesafe: {distance}")
            
            # Rota koordinatlarını işle
            route_points = []
            if route_coordinates_json:
                try:
                    route_points = json.loads(route_coordinates_json)
                    print(f"Rota noktaları yüklendi. Toplam {len(route_points)} nokta.")
                except json.JSONDecodeError:
                    print("Rota koordinatları geçersiz JSON formatında.")
            
            # Haftanın gününü belirle
            day_of_week = date_obj.weekday()
            day_name = get_turkish_day_name(day_of_week)
            
            # Konum bilgisini işle
            if location:
                try:
                    # Konum string formatında geliyorsa (ör: "41.0082,28.6954") işle
                    if isinstance(location, str) and ',' in location:
                        lat, lng = location.split(',')
                    else:
                        lat, lng = location[0], location[1]
                    
                    # Konsola debug bilgisi
                    print(f"Konum bilgisi: {lat}, {lng}, türleri: {type(lat)}, {type(lng)}")
                except (ValueError, IndexError, TypeError) as e:
                    print(f"Konum ayrıştırma hatası: {e}")
                    lat, lng = "41.013", "28.955"  # Varsayılan değerler (İstanbul)
            else:
                lat, lng = "41.013", "28.955"  # Varsayılan değerler (İstanbul)
            
            # Başlangıç ve bitiş noktaları için koordinatları ayır
            start_lat, start_lng = None, None
            end_lat, end_lng = None, None
            
            if start_point and ',' in start_point:
                start_lat, start_lng = start_point.split(',')
            
            if end_point and ',' in end_point:
                end_lat, end_lng = end_point.split(',')
            
            # Rota boyunca trafik tahminleri
            route_predictions = []
            route_colors = []
            overall_speed = 0
            overall_time = 0
            sample_points = []
            
            if len(route_points) > 0:
                # Rota noktalarından bir alt küme seç (uzun rotalarda performans için)
                step = max(1, len(route_points) // 10)  # En fazla 10 nokta
                sample_points = route_points[::step]
                
                # Rota boyunca farklı noktalar için trafik tahminleri yap
                for i, point in enumerate(sample_points):
                    point_lat, point_lng = point
                    
                    # Her nokta için mesafeyi orantılı hesapla
                    point_distance = float(distance) / len(sample_points)
                    
                    # Tahmin yap
                    prediction = predict_traffic(time_obj, day_of_week, point_lat, point_lng, point_distance)
                    traffic_level = prediction['traffic_level']
                    color = get_traffic_color(traffic_level)
                    
                    route_predictions.append(prediction)
                    route_colors.append(color)
                    
                    # Toplam hız ve süre hesapla
                    overall_speed += prediction['predicted_speed']
                    overall_time += prediction['predicted_time_per_km'] * point_distance
                
                # Ortalama değerleri hesapla
                if len(route_predictions) > 0:
                    overall_speed = overall_speed / len(route_predictions)
                    traffic_level = get_traffic_level(overall_speed)
                    main_color = get_traffic_color(traffic_level)
                else:
                    # Rota tahmini yapılamadıysa, merkez konum için tek tahmin yap
                    prediction = predict_traffic(time_obj, day_of_week, lat, lng, distance)
                    traffic_level = prediction['traffic_level']
                    main_color = get_traffic_color(traffic_level)
                    overall_speed = prediction['predicted_speed']
                    overall_time = prediction['predicted_time_per_km'] * float(distance)
            else:
                # Rota yoksa tek bir nokta için tahmin yap
                prediction = predict_traffic(time_obj, day_of_week, lat, lng, distance)
                traffic_level = prediction['traffic_level']
                main_color = get_traffic_color(traffic_level)
                overall_speed = prediction['predicted_speed']
                overall_time = prediction['predicted_time_per_km'] * float(distance)
            
            # Toplam trafik tahmini
            overall_prediction = {
                'predicted_speed': overall_speed,
                'predicted_time_per_km': overall_time / float(distance) if float(distance) > 0 else 0,
                'total_time': overall_time,
                'traffic_level': traffic_level
            }
            
            # Heatmap için veri
            heatmap_data = get_traffic_heatmap()
            
            # Hız histogramı
            speed_data = generate_speed_histogram()
            
            # Verileri template'e gönder
            context = {
                'prediction': overall_prediction,
                'route_predictions': route_predictions,
                'route_colors': route_colors,
                'sample_points': sample_points,
                'color': main_color,
                'date': date_obj,
                'time': time_obj,
                'day': day_name,
                'location': f"{lat},{lng}",
                'start_point': start_point,
                'end_point': end_point,
                'distance': distance,
                'heatmap_data': json.dumps(heatmap_data),
                'speed_data': speed_data,
                'lat': lat,
                'lng': lng,
                'route_coordinates': json.dumps(route_points)
            }
            return render(request, 'trafik_app/sonuc.html', context)
    else:
        # GET isteği ile gelirse ana sayfaya yönlendir
        return redirect('trafik_app:index')

def trafik_verisi(request):
    """API görünümü - trafik verisi JSON olarak döndürür"""
    try:
        # URL parametrelerini al
        lat = float(request.GET.get('lat', 41.013))
        lng = float(request.GET.get('lng', 28.955))
        time_of_day = request.GET.get('time', '08:00')
        day_of_week = request.GET.get('day', 'pazartesi')
        distance = float(request.GET.get('distance', 5.0))
        
        # Konum değerlerini tam hassasiyetle format
        lat_formatted = "{:.6f}".format(lat)
        lng_formatted = "{:.6f}".format(lng)
        
        # Tahmin yap
        prediction = model_utils.predict_traffic(
            time_of_day, day_of_week, lat, lng, distance
        )
        
        # Konum bilgilerini de ekle
        prediction['lat'] = lat_formatted
        prediction['lng'] = lng_formatted
        
        return JsonResponse(prediction)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400) 