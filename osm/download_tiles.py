# download_tiles.py - скачивание тайлов без внешних зависимостей
import os
import math
import urllib.request
import urllib.error
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Параметры
API_KEY = "QN6ALYSRnAohNK6Y8BiB"
OUTPUT_DIR = r"D:\road"
MIN_ZOOM = 10
MAX_ZOOM = 14

# Границы Москвы
MIN_LON = 37.3197
MIN_LAT = 55.4917  
MAX_LON = 37.9455
MAX_LAT = 55.9380

def convert_to_tile(lon, lat, zoom):
    """Конвертация координат в тайлы"""
    n = 2.0 ** zoom
    x = math.floor((lon + 180.0) / 360.0 * n)
    rad_lat = lat * math.pi / 180.0
    y = math.floor((1.0 - math.log(math.tan(rad_lat) + 1.0 / math.cos(rad_lat)) / math.pi) / 2.0 * n)
    return int(x), int(y)

def download_tile(zoom, x, y):
    """Скачивание одного тайла"""
    url = f"https://api.maptiler.com/tiles/v3-openmaptiles/{zoom}/{x}/{y}.pbf?key={API_KEY}"
    file_path = os.path.join(OUTPUT_DIR, str(zoom), str(x), f"{y}.pbf")
    
    # Создаем папку если нужно
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        # Скачиваем файл
        urllib.request.urlretrieve(url, file_path)
        
        # Проверяем размер файла
        file_size = os.path.getsize(file_path)
        if file_size > 100:
            return True, zoom, x, y, file_size
        else:
            # Удаляем пустой файл
            os.remove(file_path)
            return False, zoom, x, y, 0
    except Exception as e:
        # Удаляем файл если ошибка
        if os.path.exists(file_path):
            os.remove(file_path)
        return False, zoom, x, y, 0

def main():
    """Основная функция скачивания"""
    print("🚀 ЗАГРУЗКА ТАЙЛОВ ЗДАНИЙ МОСКВЫ")
    print(f"📁 Папка назначения: {OUTPUT_DIR}")
    print(f"🗺️  Масштабы: {MIN_ZOOM}-{MAX_ZOOM}")
    print("⏳ Это займет несколько минут...")
    
    # Создаем папку
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    total_tiles = 0
    successful = 0
    failed = 0
    
    # Считаем общее количество тайлов
    print("\n📊 Подсчет тайлов...")
    for zoom in range(MIN_ZOOM, MAX_ZOOM + 1):
        min_x, max_y = convert_to_tile(MIN_LON, MIN_LAT, zoom)
        max_x, min_y = convert_to_tile(MAX_LON, MAX_LAT, zoom)
        
        n = 2 ** zoom
        min_x = max(0, min_x)
        min_y = max(0, min_y)
        max_x = min(n - 1, max_x)
        max_y = min(n - 1, max_y)
        
        tiles_in_zoom = (max_x - min_x + 1) * (max_y - min_y + 1)
        total_tiles += tiles_in_zoom
        print(f"  Масштаб {zoom}: {tiles_in_zoom} тайлов")
    
    print(f"\n🎯 Всего тайлов для скачивания: {total_tiles}")
    
    # Скачиваем тайлы последовательно (без многопоточности)
    print("\n📥 Начинаем загрузку...")
    
    for zoom in range(MIN_ZOOM, MAX_ZOOM + 1):
        min_x, max_y = convert_to_tile(MIN_LON, MIN_LAT, zoom)
        max_x, min_y = convert_to_tile(MAX_LON, MAX_LAT, zoom)
        
        n = 2 ** zoom
        min_x = max(0, min_x)
        min_y = max(0, min_y)
        max_x = min(n - 1, max_x)
        max_y = min(n - 1, max_y)
        
        print(f"\n📍 Масштаб {zoom}: {min_x}-{max_x}, {min_y}-{max_y}")
        zoom_tiles = 0
        
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                success, z, x_val, y_val, size = download_tile(zoom, x, y)
                
                if success:
                    successful += 1
                    print(f"  ✅ {zoom}/{x}/{y}.pbf ({size} байт)")
                else:
                    failed += 1
                    print(f"  ❌ {zoom}/{x}/{y}.pbf (ошибка)")
                
                zoom_tiles += 1
                # Задержка чтобы не перегружать сервер
                time.sleep(0.1)
        
        print(f"  📈 Масштаб {zoom} завершен: {zoom_tiles} тайлов")
    
    # Итоговая статистика
    print(f"\n{'='*50}")
    print("✅ ВЫПОЛНЕНО!")
    print(f"📊 Статистика:")
    print(f"   Успешно: {successful}")
    print(f"   Ошибки: {failed}")
    print(f"   Всего: {total_tiles}")
    print(f"   Папка: {OUTPUT_DIR}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
