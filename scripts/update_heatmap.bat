@echo off
echo Isı haritası önbelleği güncelleniyor...
cd /d %~dp0..
python manage.py update_heatmap_cache --force
echo İşlem tamamlandı!
pause 