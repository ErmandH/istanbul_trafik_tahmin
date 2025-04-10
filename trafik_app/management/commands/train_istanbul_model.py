from django.core.management.base import BaseCommand
from trafik_app.model_utils import train_model_command

class Command(BaseCommand):
    help = 'İstanbul trafik veri seti kullanarak yeni bir model eğitir'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('İstanbul trafik modeli eğitimi başlatılıyor...'))
        
        try:
            result = train_model_command()
            
            if result:
                self.stdout.write(self.style.SUCCESS('Model eğitimi başarıyla tamamlandı!'))
                self.stdout.write(f"Model dosyası: {result['model_file']}")
                self.stdout.write(f"Veri sayısı: {result['sample_count']}")
                self.stdout.write(f"Hız modeli R² skoru: {result['speed_score']:.4f}")
                self.stdout.write(f"Süre modeli R² skoru: {result['time_score']:.4f}")
            else:
                self.stdout.write(self.style.ERROR('Model eğitimi başarısız oldu.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Model eğitimi sırasında hata oluştu: {str(e)}')) 