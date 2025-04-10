# Isı Haritası Önbellek Güncelleme Ayarları

Bu dokümanda, İstanbul Trafik Tahmin Sistemi'nin ısı haritası önbelleğini otomatik olarak güncelleme işleminin nasıl yapılandırılacağı açıklanmaktadır.

## Sorun ve Çözüm

İstanbul Trafik Tahmin Sistemi'nde, ana sayfada gösterilen ısı haritası için 120 MB civarında veri yüklenmekte ve işlenmektedir. Bu işlem, her sayfa yüklenişinde tekrarlandığında:

1. Yüksek CPU kullanımına
2. Yavaş sayfa yüklenmesine
3. Gereksiz veritabanı/disk erişimine

neden olmaktadır.

Çözüm olarak, ısı haritası verileri önbellekleme (caching) kullanılarak optimize edilmiştir. Bu sayede veriler belirli aralıklarla (örneğin 24 saatte bir) yeniden hesaplanmakta ve ara zamanlarda önbellekteki sürüm kullanılmaktadır.

## Otomatik Güncelleme

Isı haritası önbelleğinin otomatik olarak güncellenmesi için aşağıdaki seçenekler mevcuttur:

### Windows Görev Zamanlayıcısı (Task Scheduler)

1. Windows Görev Zamanlayıcısı'nı açın (Başlat > Görev Zamanlayıcısı)
2. "Temel Görev Oluştur" seçeneğini tıklayın
3. Görev adı ve açıklaması girin (örn. "Trafik Haritası Önbellek Güncelleme")
4. Görevin ne sıklıkla çalışacağını seçin (Günlük)
5. Başlangıç saati olarak sunucuda düşük yoğunluklu bir zaman dilimi seçin (örn. 03:00)
6. Eylem olarak "Program Başlat" seçeneğini belirleyin
7. Program/script alanına `scripts/update_heatmap.bat` dosyasının tam yolunu yazın
8. "Son" düğmesine tıklayın

### Linux/macOS Cron Job

1. Crontab dosyasını düzenlemek için terminali açın:

   ```
   crontab -e
   ```

2. Aşağıdaki satırı ekleyin (her gece saat 3'te çalışacak şekilde):

   ```
   0 3 * * * cd /path/to/project && ./scripts/update_heatmap.sh
   ```

3. Dosyayı kaydedin ve çıkın

### Manuel Güncelleme

Önbelleği manuel olarak yeniden oluşturmak için:

1. Komut satırında projenin kök dizinine gidin
2. Aşağıdaki komutu çalıştırın:
   ```
   python manage.py update_heatmap_cache --force
   ```

## Admin Arayüzü ile Güncelleme

Sistem yöneticileri (admin kullanıcıları) ana sayfada bulunan "Haritayı Yenile" butonunu kullanarak önbelleği manuel olarak güncelleyebilirler.

## Teknik Detaylar

Önbellekleme işlemi iki seviyede gerçekleştirilmektedir:

1. **Veritabanı Önbelleği**: `TrafikHeatmapCache` modeli, ısı haritası verilerini ve meta bilgilerini saklar
2. **Hafıza Önbelleği**: Histogram görüntüsü için Django'nun cache framework'ü kullanılır

Önbellek kayıtları, varsayılan olarak 24 saat boyunca geçerlidir. Bu süre, ihtiyaç durumunda model_utils.py dosyasındaki ilgili parametreler ile değiştirilebilir.

## Önbellek Temizleme

Gerektiğinde tüm önbellekleri temizlemek için:

1. Django yönetim panelinden TrafikHeatmapCache kayıtlarını silin
2. Aşağıdaki komut ile Django önbelleğini temizleyin:
   ```
   python manage.py shell -c "from django.core.cache import cache; cache.clear()"
   ```
