from django.shortcuts import render, redirect
from django.http import JsonResponse
from . import model_utils
from .model_utils import predict_traffic, get_traffic_heatmap, generate_speed_histogram, get_traffic_level, get_traffic_color
from .forms import TrafikForm
import json
from datetime import datetime

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
        # Trafik yoğunluğu haritası için veri hazırla
        heatmap_data = model_utils.get_traffic_heatmap()
        # Hız histogramı
        speed_histogram = model_utils.generate_speed_histogram()
        
        context = {
            'heatmap_data': json.dumps(heatmap_data),
            'speed_histogram': speed_histogram
        }
        return render(request, 'trafik_app/index.html', context)
    except Exception as e:
        # Hata durumunda boş bir sayfa göster
        print(f"Hata: {str(e)}")
        return render(request, 'trafik_app/index.html', {'error': str(e)})

def tahmin(request):
    """Trafik tahmini formu görünümü"""
    form = TrafikForm()
    return render(request, 'trafik_app/tahmin.html', {'form': form})

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
            
            # Debug bilgisi
            print(f"Form verileri: tarih={date_obj} ({type(date_obj)}), saat={time_obj} ({type(time_obj)})")
            
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
                    lat, lng = "41.003", "28.705"  # Varsayılan değerler
            else:
                lat, lng = "41.003", "28.705"  # Varsayılan değerler
            
            # Tahmin yap - time_obj ve day_of_week direk olarak geçir
            prediction = predict_traffic(time_obj, day_of_week, lat, lng, distance)
            
            # Trafik seviyesi bilgisini getir
            traffic_level = prediction['traffic_level']
            color = get_traffic_color(traffic_level)
            
            # Heatmap için veri
            heatmap_data = get_traffic_heatmap()
            
            # Hız histogramı
            speed_data = generate_speed_histogram()
            
            # Verileri template'e gönder
            context = {
                'prediction': prediction,
                'color': color,
                'date': date_obj,
                'time': time_obj,
                'day': day_name,
                'location': f"{lat},{lng}",
                'distance': distance,
                'heatmap_data': json.dumps(heatmap_data),
                'speed_data': speed_data,
                'lat': lat,
                'lng': lng
            }
            return render(request, 'trafik_app/sonuc.html', context)
    else:
        # GET isteği ile gelirse ana sayfaya yönlendir
        return redirect('trafik_app:index')

def trafik_verisi(request):
    """API görünümü - trafik verisi JSON olarak döndürür"""
    try:
        # URL parametrelerini al
        lat = float(request.GET.get('lat', 41.003))
        lng = float(request.GET.get('lng', 28.705))
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