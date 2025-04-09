from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('tahmin/', views.tahmin, name='tahmin'),
    path('sonuc/', views.sonuc, name='sonuc'),
    path('api/trafik-verisi/', views.trafik_verisi, name='trafik_verisi'),
] 