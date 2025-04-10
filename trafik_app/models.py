from django.db import models
import json
from django.utils import timezone

# TrafikSegment modeli - veritabanında trafik segmentlerini temsil eder
class TrafikSegment(models.Model):
    segment_id = models.CharField(max_length=100, unique=True)
    street_name = models.CharField(max_length=255, blank=True, null=True)
    speed_limit = models.FloatField(default=0)
    distance = models.FloatField(default=0)
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)
    
    def __str__(self):
        return f"{self.street_name} ({self.segment_id})"

# TrafikVeri modeli - veritabanında trafik verilerini temsil eder
class TrafikVeri(models.Model):
    segment = models.ForeignKey(TrafikSegment, on_delete=models.CASCADE, related_name='trafik_verileri')
    datetime = models.DateTimeField()
    harmonic_avg_speed = models.FloatField(default=0)
    median_speed = models.FloatField(default=0)
    average_speed = models.FloatField(default=0)
    travel_time = models.FloatField(default=0)
    sample_size = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.segment.street_name} - {self.datetime.strftime('%Y-%m-%d %H:%M')}"

# TrafikTahmin modeli - kullanıcı tahminlerini saklar
class TrafikTahmin(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    time_of_day = models.TimeField()
    day_of_week = models.CharField(max_length=20)
    distance = models.FloatField()
    predicted_speed = models.FloatField()
    predicted_time = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Tahmin: {self.latitude}, {self.longitude} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

# TrafikHeatmapCache modeli - ısı haritası verilerini önbellekleme için kullanılır
class TrafikHeatmapCache(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    data = models.TextField()  # JSON formatında ısı haritası verileri
    point_count = models.IntegerField(default=0)  # Veri noktası sayısı
    
    class Meta:
        ordering = ['-updated_at']
    
    def get_data(self):
        """Önbelleğe alınmış ısı haritası verilerini döndürür"""
        return json.loads(self.data)
    
    def set_data(self, heatmap_data):
        """Isı haritası verilerini önbelleğe alır"""
        self.data = json.dumps(heatmap_data)
        self.point_count = len(heatmap_data)
        self.save()
    
    def is_valid(self, max_age_hours=24):
        """Önbelleğin geçerli olup olmadığını kontrol eder"""
        if not self.updated_at:
            return False
        
        time_diff = timezone.now() - self.updated_at
        return time_diff.total_seconds() < max_age_hours * 3600
    
    @classmethod
    def get_latest_cache(cls, max_age_hours=24):
        """En son önbelleği döndürür, eğer geçerli değilse None döndürür"""
        try:
            latest_cache = cls.objects.latest('updated_at')
            if latest_cache.is_valid(max_age_hours):
                return latest_cache
            return None
        except cls.DoesNotExist:
            return None
    
    def __str__(self):
        return f"Heatmap Cache - {self.point_count} nokta, {self.updated_at.strftime('%Y-%m-%d %H:%M')}" 