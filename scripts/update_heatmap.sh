#!/bin/bash
# Isı haritası önbelleğini güncelleme betiği

echo "Isı haritası önbelleği güncelleniyor..."
cd "$(dirname "$0")/.."
python manage.py update_heatmap_cache --force
echo "İşlem tamamlandı!" 