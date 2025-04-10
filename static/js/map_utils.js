/**
 * Trafik haritası işlemleri için JavaScript fonksiyonları
 */

// Konum haritası başlatma fonksiyonu
function initLocationMap(mapElementId, latitude, longitude, distance = 5, trafficLevel = null) {
    console.log('initLocationMap başladı:', mapElementId, latitude, longitude, 'trafik seviyesi:', trafficLevel);
    
    // DOM elementinin varlığını kontrol et
    const mapElement = document.getElementById(mapElementId);
    if (!mapElement) {
        console.error('Harita elementi bulunamadı:', mapElementId);
        return null;
    }
    
    // Konum değerlerini doğru formata dönüştür
    latitude = parseFloat(latitude);
    longitude = parseFloat(longitude);
    
    // Geçersiz konum değerleri kontrolü
    if (isNaN(latitude) || isNaN(longitude)) {
        console.error('Geçersiz konum değerleri:', latitude, longitude);
        mapElement.innerHTML = '<div class="alert alert-danger m-3">Geçersiz konum bilgileri.</div>';
        return null;
    }
    
    // İstanbul bölgesinde mantıklı değer aralığı kontrolü
    if (latitude < 40.7 || latitude > 41.5 || longitude < 28.3 || longitude > 29.5) {
        console.warn('Konum değerleri İstanbul bölgesi dışında olabilir:', latitude, longitude);
    }
    
    try {
        // Haritayı başlat
        const map = L.map(mapElementId).setView([latitude, longitude], 15);
        console.log('Harita oluşturuldu');
        
        // Harita katmanı ekle
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        console.log('Harita katmanı eklendi');
        
        // Tam konum bilgisi oluştur (virgülden sonra maksimum 6 basamak)
        const latFormatted = parseFloat(latitude.toFixed(6));
        const lngFormatted = parseFloat(longitude.toFixed(6));
        const locationText = "Seçilen Konum: " + latFormatted + ", " + lngFormatted;
        
        // İşaretleyici ekle
        const marker = L.marker([latitude, longitude]).addTo(map);
        marker.bindPopup(locationText).openPopup();
        console.log('İşaretleyici eklendi:', locationText);
        
        // Trafik durumuna göre işaretleyici rengi
        if (trafficLevel) {
            // Trafik seviyesine göre renk
            let circleColor;
            
            // HEX renk kodunu doğrudan kullanabiliriz
            if (trafficLevel.startsWith('#')) {
                circleColor = trafficLevel;
            } else {
                // Renk sınıfları için alternatif
                switch(trafficLevel) {
                    case 'success':
                    case 0:
                        circleColor = '#00FF00'; // Yeşil (Çok Düşük)
                        break;
                    case 'warning':
                    case 1:
                    case 2:
                        circleColor = '#FFFF00'; // Sarı (Orta)
                        break;
                    case 'danger':
                    case 3:
                    case 4:
                        circleColor = '#FF0000'; // Kırmızı (Çok Yüksek)
                        break;
                    default:
                        circleColor = '#007bff'; // Varsayılan mavi
                }
            }
            
            // Trafik durumu göstergesi
            L.circle([latitude, longitude], {
                color: circleColor,
                fillColor: circleColor,
                fillOpacity: 0.2,
                radius: distance * 100 // Mesafenin görsel temsili
            }).addTo(map);
            console.log('Trafik durumu göstergesi eklendi:', trafficLevel);
        }
        
        // Haritayı yeniden boyutlandır
        map.invalidateSize();
        console.log('Harita boyutlandırması yapıldı');
        
        // Haritayı döndür
        return map;
    } catch (error) {
        console.error('Harita oluşturma hatası:', error);
        return null;
    }
}

// Sayfa yüklendiğinde veya pencere boyutu değiştiğinde haritayı yeniden boyutlandır
function resizeMap(map) {
    if (map) {
        setTimeout(function() {
            map.invalidateSize();
            console.log('Harita yeniden boyutlandırıldı');
        }, 200);
    }
}

// Heatmap (ısı haritası) başlatma fonksiyonu
function initHeatmap(mapElementId, heatmapData, center = [41.0082, 28.9784]) {
    console.log('initHeatmap başladı:', mapElementId);
    
    // DOM elementinin varlığını kontrol et
    const mapElement = document.getElementById(mapElementId);
    if (!mapElement) {
        console.error('Harita elementi bulunamadı:', mapElementId);
        return null;
    }
    
    try {
        // Haritayı başlat - İstanbul merkezinde
        const map = L.map(mapElementId).setView(center, 12);
        console.log('Isı haritası oluşturuldu');
        
        // Harita katmanı ekle
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        // Veriyi Leaflet.heat formatına dönüştür
        const heatPoints = heatmapData.map(function(p) {
            // Konum değerlerini doğru formata dönüştür
            const lat = parseFloat(p.latitude);
            const lng = parseFloat(p.longitude);
            const intensity = parseFloat(p.traffic_intensity);
            
            // Geçersiz değer kontrolü
            if (isNaN(lat) || isNaN(lng) || isNaN(intensity)) {
                console.warn('Geçersiz ısı haritası noktası:', p);
                return null;
            }
            
            // Yoğunluğa göre renk ağırlığı
            return [lat, lng, intensity];
        }).filter(point => point !== null); // Null değerleri filtrele
        
        // Isı haritasını ekle
        if (heatPoints.length > 0) {
            L.heatLayer(heatPoints, {
                radius: 20,
                blur: 15,
                maxZoom: 17,
                gradient: {
                    0.2: 'blue',
                    0.4: 'lime',
                    0.6: 'yellow',
                    0.8: 'orange',
                    1.0: 'red'
                }
            }).addTo(map);
            console.log('Isı haritası verileri eklendi:', heatPoints.length, 'nokta');
        } else {
            console.warn('Isı haritası için geçerli veri yok');
            mapElement.innerHTML = '<div class="alert alert-warning m-3">Isı haritası için yeterli veri bulunamadı.</div>';
        }
        
        // Haritayı yeniden boyutlandır
        map.invalidateSize();
        
        // Haritayı döndür
        return map;
    } catch (error) {
        console.error('Isı haritası oluşturma hatası:', error);
        return null;
    }
} 