from django.db import models

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