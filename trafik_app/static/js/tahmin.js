document.addEventListener("DOMContentLoaded", function () {
  // Kütüphanelerin yüklendiğini kontrol et
  if (typeof L === 'undefined') {
    console.error('Leaflet kütüphanesi yüklenemedi!');
    return;
  }

  if (typeof L.Routing === 'undefined') {
    console.error('Leaflet Routing Machine kütüphanesi yüklenemedi!');
    // Kütüphaneyi dinamik olarak yüklemeyi dene
    loadScript('https://unpkg.com/leaflet-routing-machine@3.2.12/dist/leaflet-routing-machine.min.js', initializeApp);
    return;
  }

  // Tüm kütüphaneler yüklendiyse uygulamayı başlat
  initializeApp();
});

// JavaScript kütüphanesini dinamik olarak yükleme fonksiyonu
function loadScript(url, callback) {
  console.log('Kütüphaneyi dinamik olarak yükleme başladı:', url);
  var script = document.createElement('script');
  script.type = 'text/javascript';
  script.src = url;
  script.onload = function() {
    console.log('Kütüphane başarıyla yüklendi:', url);
    if (callback) callback();
  };
  script.onerror = function() {
    console.error('Kütüphane yüklenemedi:', url);
  };
  document.head.appendChild(script);
}

function initializeApp() {
  // Bugünün tarihini varsayılan olarak ayarla
  const today = new Date();
  const dateStr = today.toISOString().slice(0, 10);
  document.getElementById("dateInput").value = dateStr;

  // Şu anki saati varsayılan olarak ayarla
  const hours = String(today.getHours()).padStart(2, "0");
  const minutes = String(today.getMinutes()).padStart(2, "0");
  document.getElementById("timeInput").value = `${hours}:${minutes}`;

  // Haritayı başlat
  initMap();
}

let map, marker, routingControl;
let routeType = "single";

function initMap() {
  // İstanbul merkezi
  const istanbul = [41.0082, 28.9784];

  // Haritayı oluştur
  map = L.map("map").setView(istanbul, 11);

  // Harita katmanını ekle
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  // Tek nokta modu için işaretçi
  marker = L.marker(istanbul, { draggable: true }).addTo(map);
  updateMarkerPosition(istanbul);

  // İşaretçi sürüklendiğinde
  marker.on("dragend", function (e) {
    const position = marker.getLatLng();
    updateMarkerPosition([position.lat, position.lng]);
  });

  // Haritaya tıklandığında
  map.on("click", function (e) {
    if (routeType === "single") {
      marker.setLatLng(e.latlng);
      updateMarkerPosition([e.latlng.lat, e.latlng.lng]);
    }
  });
}

function updateMarkerPosition(position) {
  const lat = typeof position[0] === 'number' ? position[0].toFixed(6) : position.lat.toFixed(6);
  const lng = typeof position[1] === 'number' ? position[1].toFixed(6) : position.lng.toFixed(6);

  document.getElementById("latInput").value = lat;
  document.getElementById("lngInput").value = lng;
  document.getElementById(
    "selectedPointInfo"
  ).innerHTML = `<i class="fas fa-map-marker-alt"></i> ${lat}, ${lng}`;
}

function toggleRouteType(type) {
  if (type === routeType) return; // Zaten seçili ise bir şey yapma

  routeType = type;
  document.getElementById("routeTypeInput").value = type;

  // UI güncelleme - animasyon ile
  if (type === "single") {
    // Card güncelleme
    document.getElementById("singlePointCard").classList.add("active");
    document.getElementById("routeCard").classList.remove("active");

    // Talimatları güncelle
    document.getElementById("singlePointInstructions").style.display =
      "block";
    document.getElementById("routeInstructions").style.display = "none";

    // Rota bilgisini gizle
    document.getElementById("routeInfo").style.display = "none";

    // Alanları değiştir (animasyonlu)
    document.getElementById("routeFields").classList.add("fade-out");

    setTimeout(() => {
      document.getElementById("routeFields").style.display = "none";
      document.getElementById("singlePointFields").style.display = "block";
      setTimeout(() => {
        document
          .getElementById("singlePointFields")
          .classList.remove("fade-out");
      }, 50);
    }, 300);

    // Yönlendirme kontrolünü kaldır
    if (routingControl) {
      map.removeControl(routingControl);
      routingControl = null;
    }

    // İşaretçiyi göster
    marker.addTo(map);

    // Harita merkezini güncelle
    const position = marker.getLatLng();
    map.setView([position.lat, position.lng], 13);
  } else {
    // Card güncelleme
    document.getElementById("routeCard").classList.add("active");
    document.getElementById("singlePointCard").classList.remove("active");

    // Talimatları güncelle
    document.getElementById("singlePointInstructions").style.display = "none";
    document.getElementById("routeInstructions").style.display = "block";

    // Rota bilgisini göster
    document.getElementById("routeInfo").style.display = "block";

    // Alanları değiştir (animasyonlu)
    document.getElementById("singlePointFields").classList.add("fade-out");

    setTimeout(() => {
      document.getElementById("singlePointFields").style.display = "none";
      document.getElementById("routeFields").style.display = "block";
      setTimeout(() => {
        document.getElementById("routeFields").classList.remove("fade-out");
      }, 50);
    }, 300);

    // İşaretçiyi kaldır
    map.removeLayer(marker);

    // Yönlendirme kontrolünü ekle
    initRouting();
  }
}

function initRouting() {
  // L.Routing'in yüklü olduğunu kontrol et
  if (typeof L.Routing === 'undefined') {
    console.error('L.Routing tanımlanmamış! Routing Machine kütüphanesi yüklenemedi.');
    alert('Rota oluşturma özelliği yüklenemedi. Sayfayı yenilemeyi deneyin.');
    return;
  }

  // İstanbul'da iki yaygın nokta (Taksim ve Üsküdar)
  const defaultStart = L.latLng(41.0082, 28.9784);
  const defaultEnd = L.latLng(41.0255, 29.0097);

  // Önceki routing control varsa kaldır
  if (routingControl) {
    map.removeControl(routingControl);
  }

  // Yönlendirme kontrolünü oluştur - Leaflet Routing Machine API'sine göre
  try {
    routingControl = L.Routing.control({
      waypoints: [
        defaultStart,
        defaultEnd
      ],
      routeWhileDragging: true,
      showAlternatives: false,
      fitSelectedRoutes: true,
      show: false, // UI panelini gösterme
      collapsible: false,
      lineOptions: {
        styles: [{ color: "#007bff", opacity: 0.7, weight: 6 }],
      },
      altLineOptions: {
        styles: [{ color: "#00a8ff", opacity: 0.4, weight: 4 }]
      },
      router: L.Routing.osrmv1({
        serviceUrl: 'https://router.project-osrm.org/route/v1',
        profile: 'driving'
      }),
      containerClassName: 'custom-routing-container',
      createMarker: function(i, wp, n) {
        // A ve B harfli marker'lar oluştur
        const markerContent = `
          <div style="background-color: ${i === 0 ? '#4285F4' : '#DB4437'}; 
                      color: white; 
                      font-weight: bold; 
                      text-align: center; 
                      border-radius: 50%; 
                      width: 28px; 
                      height: 28px; 
                      line-height: 28px; 
                      box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
            ${i === 0 ? 'A' : 'B'}
          </div>`;
        
        const icon = L.divIcon({
          className: 'custom-div-icon',
          html: markerContent,
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        });
        
        // Marker oluştur
        const marker = L.marker(wp.latLng, {
          icon: icon,
          draggable: true,
          title: i === 0 ? 'Başlangıç Noktası (A)' : 'Varış Noktası (B)'
        });
        
        // Markerlar sürüklendiğinde bilgileri güncelle
        marker.on('dragend', function() {
          updateRouteWaypoints();
        });
        
        return marker;
      }
    }).addTo(map);

    // Haritaya tıklandığında rota modunda yeni noktalar ekle
    map.on('click', function(e) {
      if (routeType === 'route') {
        const waypoints = routingControl.getWaypoints();
        // Eğer başlangıç noktası boşsa onu ekle
        if (!waypoints[0].latLng) {
          routingControl.spliceWaypoints(0, 1, e.latlng);
        } 
        // Eğer varış noktası boşsa onu ekle
        else if (!waypoints[1].latLng) {
          routingControl.spliceWaypoints(1, 1, e.latlng);
        }
        // İkisi de doluysa varış noktasını güncelle
        else {
          routingControl.spliceWaypoints(1, 1, e.latlng);
        }
      }
    });

    // Rota güncellendiğinde
    routingControl.on('routesfound', function(e) {
      updateRouteInfo(e.routes[0]);
    });

    // İlk yükleme için rota bilgilerini güncelle
    setTimeout(function() {
      const waypoints = routingControl.getWaypoints();
      if (waypoints[0].latLng && waypoints[1].latLng) {
        updateWaypointFields(waypoints[0].latLng, waypoints[1].latLng);
      }
    }, 1000);
  } catch (error) {
    console.error('Routing Control oluşturulurken hata:', error);
    alert('Rota oluşturma özelliği başlatılamadı: ' + error.message);
  }
}

// Rota waypoint'lerini güncelleme
function updateRouteWaypoints() {
  if (!routingControl) return;
  
  const waypoints = routingControl.getWaypoints();
  if (waypoints.length >= 2 && waypoints[0].latLng && waypoints[1].latLng) {
    updateWaypointFields(waypoints[0].latLng, waypoints[1].latLng);
  }
}

// Kullanıcı arayüzündeki waypoint bilgilerini güncelle
function updateWaypointFields(start, end) {
  // Form alanlarını güncelle
  document.getElementById("startPointInput").value = `${start.lat.toFixed(6)},${start.lng.toFixed(6)}`;
  document.getElementById("endPointInput").value = `${end.lat.toFixed(6)},${end.lng.toFixed(6)}`;
  
  // Kullanıcı arayüzündeki etiketleri güncelle
  document.getElementById("startPointInfo").innerHTML = 
    `<i class="fas fa-flag-checkered"></i> ${start.lat.toFixed(6)}, ${start.lng.toFixed(6)}`;
  document.getElementById("endPointInfo").innerHTML = 
    `<i class="fas fa-flag"></i> ${end.lat.toFixed(6)}, ${end.lng.toFixed(6)}`;
}

// Rota bilgilerini güncelle
function updateRouteInfo(route) {
  const distance = (route.summary.totalDistance / 1000).toFixed(2);
  const duration = (route.summary.totalTime / 60).toFixed(0);
  
  // Mesafe ve süre bilgilerini güncelle
  document.getElementById("routeDistance").textContent = distance;
  document.getElementById("routeDuration").textContent = duration;
  document.getElementById("distanceInput").value = distance;
  
  // Rota koordinatlarını kaydet
  const routeCoordinates = [];
  for (let i = 0; i < route.coordinates.length; i++) {
    routeCoordinates.push([
      route.coordinates[i].lat,
      route.coordinates[i].lng
    ]);
  }
  document.getElementById("routeCoordinatesInput").value = JSON.stringify(routeCoordinates);
  
  // Waypoint bilgilerini güncelle
  updateRouteWaypoints();
} 