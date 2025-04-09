from django.contrib import admin
from .models import TrafikSegment, TrafikVeri, TrafikTahmin

@admin.register(TrafikSegment)
class TrafikSegmentAdmin(admin.ModelAdmin):
    list_display = ('segment_id', 'street_name', 'speed_limit', 'distance')
    search_fields = ('segment_id', 'street_name')
    list_filter = ('speed_limit',)

@admin.register(TrafikVeri)
class TrafikVeriAdmin(admin.ModelAdmin):
    list_display = ('segment', 'datetime', 'average_speed', 'travel_time', 'sample_size')
    list_filter = ('datetime',)
    date_hierarchy = 'datetime'

@admin.register(TrafikTahmin)
class TrafikTahminAdmin(admin.ModelAdmin):
    list_display = ('latitude', 'longitude', 'time_of_day', 'day_of_week', 'predicted_speed', 'created_at')
    list_filter = ('day_of_week', 'created_at')
    date_hierarchy = 'created_at' 