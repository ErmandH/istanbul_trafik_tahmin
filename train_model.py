import os
import sys
import django

# Django ayarlarını yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trafik_tahmin.settings')
django.setup()

# Gerekli klasörleri oluştur
models_dir = 'models'
if not os.path.exists(models_dir):
    print(f"{models_dir} klasörü oluşturuluyor...")
    os.makedirs(models_dir)
    print(f"{models_dir} klasörü oluşturuldu.")
else:
    print(f"{models_dir} klasörü zaten var.")

# Model eğitim fonksiyonunu çağır
from trafik_app.model_utils import train_model_command
print("İstanbul trafik modeli eğitimi başlatılıyor...")
result = train_model_command()

if result:
    print("\nModel eğitimi başarıyla tamamlandı!")
    print(f"Model dosyası: {result['model_file']}")
    print(f"Veri sayısı: {result['sample_count']}")
    print(f"Hız modeli R² skoru: {result['speed_score']:.4f}")
    print(f"Süre modeli R² skoru: {result['time_score']:.4f}")
else:
    print("\nModel eğitimi başarısız oldu.")

print("\nİşlem tamamlandı.") 