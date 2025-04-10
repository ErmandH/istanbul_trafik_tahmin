from django.core.management.base import BaseCommand
from trafik_app.model_utils import get_traffic_heatmap
from trafik_app.models import TrafikHeatmapCache

class Command(BaseCommand):
    help = 'Isı haritası verilerini hesaplar ve önbelleğe kaydeder'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Mevcut önbelleği yok sayar ve yeniden hesaplar',
        )
    
    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write('Isı haritası önbelleği güncelleme başlatıldı...')
        
        try:
            # Mevcut önbelleği kontrol et
            if not force:
                cache = TrafikHeatmapCache.get_latest_cache()
                if cache:
                    self.stdout.write(self.style.SUCCESS(f'Geçerli önbellek zaten mevcut. Son güncelleme: {cache.updated_at}'))
                    self.stdout.write(f'Nokta sayısı: {cache.point_count}')
                    self.stdout.write('Zorla yenilemek için --force parametresini kullanın')
                    return
            
            # Isı haritası verilerini hesapla ve önbelleğe kaydet
            heatmap_data = get_traffic_heatmap(force_refresh=True)
            
            self.stdout.write(self.style.SUCCESS('Isı haritası önbelleği başarıyla güncellendi!'))
            self.stdout.write(f'Nokta sayısı: {len(heatmap_data)}')
            
            # En son oluşturulan önbelleğin bilgilerini göster
            cache = TrafikHeatmapCache.objects.latest('updated_at')
            self.stdout.write(f'Önbellek ID: {cache.id}')
            self.stdout.write(f'Oluşturulma tarihi: {cache.created_at}')
            self.stdout.write(f'Güncelleme tarihi: {cache.updated_at}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Önbellek güncelleme sırasında hata oluştu: {str(e)}')) 