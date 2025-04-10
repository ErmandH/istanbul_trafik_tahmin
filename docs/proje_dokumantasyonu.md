# İstanbul Trafik Tahmin Sistemi

Bu doküman, İstanbul trafik tahmin sistemi projesinin yapısını, işleyişini ve kullanımını açıklamaktadır.

## Proje Özeti

İstanbul Trafik Tahmin Sistemi, makine öğrenimi modelleri kullanarak İstanbul'daki trafik durumunu tahmin eden ve görselleştiren bir web uygulamasıdır. Proje, özellikle Avcılar bölgesindeki trafik verilerini analiz ederek, kullanıcılara belirli bir zaman ve konumdaki trafik durumu hakkında bilgi sağlar.



### 1. Veri Toplama ve İşleme

- Proje, İstanbul bölgelerindeki trafik verilerini kullanır
- Veriler, yol segmentleri, hız bilgileri, seyahat süreleri ve trafik yoğunluğu gibi bilgileri içerir

### 2. Model Eğitimi

- Uygun bir makine öğrenmesi algoritması kullanılarak iki farklı model eğitilir:
  - Ortalama hız tahmin modeli
  - Seyahat süresi tahmin modeli
- Modeller, trafik yoğunluğunu ve seyahat süresini tahmin etmek için kullanılır


### 3. Tahmin Sistemi

- Kullanıcılar, belirli bir konum ve zaman için trafik tahmini alabilirler
- Tek nokta tahmini veya rota tahmini yapılabilir
- Tahminler, renkli göstergeler ve ısı haritaları ile görselleştirilir


## Makine Öğrenimi Öznitelikleri

- Hız limiti
- Mesafe
- Örnek boyutu
- Trafik yoğunluğu
- Enlem
- Boylam



## Kullanım Senaryoları

### 1. Tek Nokta Trafik Tahmini

1. Kullanıcı, ana sayfada bir konum seçer
2. Tarih ve saat bilgisini girer
3. Sistem, seçilen konum ve zamandaki tahmini trafik seviyesini gösterir
4. Sonuç, renkli bir gösterge ile harita üzerinde görselleştirilir

### 2. Rota Tahmini

1. Kullanıcı, başlangıç ve bitiş noktalarını seçer
2. Tarih ve saat bilgisini girer
3. Sistem, rota boyunca trafik tahminleri yapar
4. Sonuç, rota üzerindeki her segment için renkli göstergeler ile görselleştirilir
5. Toplam seyahat süresi ve ortalama hız hesaplanır



## Sonuç

İstanbul Trafik Tahmin Sistemi, makine öğrenimi ve web teknolojilerini birleştirerek şehir içi ulaşımı optimize etmeyi amaçlayan bir projedir. Kullanıcılar, sistem sayesinde trafik durumunu önceden tahmin edebilir ve seyahatlerini buna göre planlayabilirler.

