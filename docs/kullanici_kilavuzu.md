# İstanbul Trafik Tahmin Sistemi - Kullanıcı Kılavuzu

Bu kılavuz, İstanbul Trafik Tahmin Sistemi'ni kullanarak trafik durumunu tahmin etmek ve optimum rotaları bulmak için yapmanız gerekenleri açıklamaktadır.

## İçindekiler

1. [Giriş](#giriş)
2. [Sisteme Erişim](#sisteme-erişim)
3. [Ana Sayfa](#ana-sayfa)
4. [Trafik Tahmini Yapma](#trafik-tahmini-yapma)
5. [Rota Tahmini Yapma](#rota-tahmini-yapma)
6. [Sonuçları Yorumlama](#sonuçları-yorumlama)
7. [Isı Haritasını Kullanma](#ısı-haritasını-kullanma)
8. [Sık Sorulan Sorular](#sık-sorulan-sorular)

## Giriş

İstanbul Trafik Tahmin Sistemi, İstanbul şehri genelinde trafik durumunu tahmin etmek için geliştirilen bir web uygulamasıdır. Sistem, geçmiş trafik verilerini kullanarak makine öğrenimi modelleri ile belirli bir zaman ve konumdaki muhtemel trafik durumunu tahmin etmektedir.

Bu uygulama ile şunları yapabilirsiniz:

- Belirli bir konumdaki trafik yoğunluğunu tahmin etme
- Başlangıç ve varış noktaları arasındaki en uygun rotayı bulma
- Şehir genelindeki trafik yoğunluğunu ısı haritası üzerinde görme
- Seyahat süresi ve hız tahminleri alma

## Sisteme Erişim

Sisteme erişmek için:

1. Web tarayıcınızı açın
2. Adres çubuğuna şu adresi yazın: `http://127.0.0.1:8000`
3. Eğer sistem başka bir adrese kurulmuşsa, sistem yöneticinizden doğru URL bilgisini alın

## Ana Sayfa

Ana sayfa iki temel bölümden oluşur:

1. **Trafik Isı Haritası**: Şehir genelindeki trafik yoğunluğunu gösteren interaktif harita
2. **Trafik Tahmin Formu**: Belirli bir konum veya rota için trafik tahmini yapabileceğiniz form

![Ana Sayfa](../static/trafik_app/img/ana_sayfa.png)

### Haritada Gezinme

- **Yakınlaştırma/Uzaklaştırma**: Haritadaki + ve - düğmelerini veya farenizin tekerleğini kullanın
- **Haritayı Kaydırma**: Fare ile haritayı tutup sürükleyin
- **Konum Seçme**: Haritada herhangi bir noktaya tıklayın

## Trafik Tahmini Yapma

Belirli bir konumda trafik durumunu tahmin etmek için:

1. Ana sayfadaki haritada tahmin yapmak istediğiniz noktaya tıklayın veya koordinatları manuel olarak girin
2. "Tahmin Türü" alanından "Tek Nokta" seçeneğini işaretleyin
3. Tarih ve saat seçin
4. "Tahmin Yap" düğmesine tıklayın

![Tek Nokta Tahmini](../static/trafik_app/img/tek_nokta_tahmin.png)

Sistem, seçilen konum ve zamandaki tahmini trafik durumunu gösterecektir.

## Rota Tahmini Yapma

İki nokta arasındaki rota için trafik tahmini yapmak için:

1. "Tahmin Türü" alanından "Rota" seçeneğini işaretleyin
2. Haritada başlangıç noktasını seçmek için tıklayın
3. "Başlangıç Noktası" olarak işaretleyin
4. Haritada varış noktasını seçmek için tıklayın
5. "Varış Noktası" olarak işaretleyin
6. Tarih ve saat seçin
7. "Tahmin Yap" düğmesine tıklayın

![Rota Tahmini](../static/trafik_app/img/rota_tahmin.png)

Sistem, seçilen rota üzerindeki trafik tahminlerini gösterecek ve tahmini seyahat süresini hesaplayacaktır.

### Alternatif Rota Seçenekleri

Sistem, bazı durumlarda alternatif rota seçenekleri sunabilir:

1. "Alternatif Rotaları Göster" düğmesine tıklayın
2. Sunulan farklı rotalar arasından seçim yapın
3. Her rota için tahmini seyahat süresi ve trafik durumunu karşılaştırın

## Sonuçları Yorumlama

Tahmin sonuçları, renk kodları ve göstergelerle görselleştirilir:

- **Yeşil**: Akıcı trafik (30 km/sa üzeri)
- **Sarı**: Yoğun trafik (15-30 km/sa)
- **Kırmızı**: Sıkışık trafik (5-15 km/sa)
- **Siyah**: Durağan trafik (5 km/sa altı)

![Sonuç Sayfası](../static/trafik_app/img/sonuc_sayfasi.png)

Sonuç sayfasında şu bilgiler yer alır:

- Seçilen konum/rota bilgisi
- Tahmini trafik seviyesi
- Tahmini ortalama hız
- Tahmini seyahat süresi (rota tahmini için)
- Tarih ve saat bilgisi

## Isı Haritasını Kullanma

Ana sayfadaki ısı haritası, şehir genelindeki trafik yoğunluğunu gösterir:

- **Mavi**: Düşük trafik yoğunluğu
- **Yeşil/Sarı**: Orta düzeyde trafik yoğunluğu
- **Turuncu/Kırmızı**: Yüksek trafik yoğunluğu

![Isı Haritası](../static/trafik_app/img/isi_haritasi.png)

Isı haritasını kullanarak:

- Genel trafik durumunu değerlendirebilirsiniz
- Yoğun bölgeleri tespit edebilirsiniz
- Alternatif güzergahlar planlayabilirsiniz

### Hız Histogramı

Ana sayfada ayrıca bir hız histogramı bulunur. Bu histogram, şehir genelindeki hız dağılımını gösterir ve genel trafik durumunu anlamanıza yardımcı olur.

## Sık Sorulan Sorular

### Tahminler ne kadar doğrudur?

Sistem, geçmiş trafik verilerini kullanarak tahmin yapar. Doğruluk oranı, kullanılan veri miktarına ve trafik akışındaki değişkenlere bağlıdır. Genel olarak %70-85 arasında bir doğruluk oranı sağlanmaktadır.

### Hangi zaman aralığı için tahmin yapabilirim?

Sistem, gelecekteki herhangi bir tarih ve saat için tahmin yapabilir. Ancak, tahminler günün saati ve haftanın günü gibi zaman özelliklerine dayanır. Çok uzak gelecek için yapılan tahminlerin doğruluğu azalabilir.

### Sistem trafik kazalarını veya yol çalışmalarını hesaba katıyor mu?

Mevcut sistemde anlık trafik kazaları veya yol çalışmaları doğrudan hesaba katılmamaktadır. Tahminler, geçmiş trafik verileri ve zaman özelliklerine dayanmaktadır.

### Cep telefonum için bir uygulama var mı?

Şu anda sadece web uygulaması mevcuttur. Mobil uygulama geliştirme çalışmaları devam etmektedir.

### Verdiğim konum bilgileri saklanıyor mu?

Evet, yapılan tahminler ve konum bilgileri, sistem performansını değerlendirmek ve gelecekteki tahminleri iyileştirmek için anonim olarak saklanmaktadır.

### Hata veya öneri bildiriminde nasıl bulunabilirim?

Uygulama hakkında geri bildirimde bulunmak için ana sayfadaki "İletişim" bağlantısını kullanabilir veya doğrudan trafik.tahmin@ornek.com adresine e-posta gönderebilirsiniz.

---

Bu kılavuzla ilgili sorularınız varsa, lütfen sistem yöneticinizle iletişime geçin.
