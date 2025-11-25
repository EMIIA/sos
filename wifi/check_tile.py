import requests
import os
from math import floor
import time

# Параметры
API_KEY = "QN6ALYSRnAohNK6Y8BiB"
BASE_URL = "https://api.maptiler.com/tiles/v3/{z}/{x}/{y}.pbf?key={key}"
OUTPUT_DIR = "tiles"
MIN_ZOOM = 10
MAX_ZOOM = 15

# Границы Москвы
MIN_LON, MIN_LAT = 37.3197, 55.4917
MAX_LON, MAX_LAT = 37.9455, 55.9380

# Настройки загрузки
RETRY_COUNT = 3
DELAY_BETWEEN_REQUESTS = 0.1  # секунды

def deg2num(lat_deg, lon_deg, zoom):
    """Преобразование координат в номера тайлов"""
    lat_rad = lat_deg * 3.141592653589793 / 180
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - (lat_rad / 3.141592653589793)) / 2.0 * n)
    return xtile, ytile

def download_tile(zoom, x, y, retry_count=RETRY_COUNT):
    """Загрузка одного тайла с повторными попытками"""
    url = BASE_URL.format(z=zoom, x=x, y=y, key=API_KEY)
    x_dir = os.path.join(OUTPUT_DIR, str(zoom), str(x))
    filename = os.path.join(x_dir, f"{y}.pbf")
    
    # Проверяем, существует ли файл
    if os.path.exists(filename):
        print(f"Пропущен (уже есть): {zoom}/{x}/{y}.pbf")
        return True
    
    os.makedirs(x_dir, exist_ok=True)
    
    for attempt in range(retry_count):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"Скачан: {zoom}/{x}/{y}.pbf")
                return True
            else:
                print(f"Ошибка загрузки {zoom}/{x}/{y}.pbf (попытка {attempt+1}): {response.status_code}")
        except Exception as e:
            print(f"Ошибка при загрузке {zoom}/{x}/{y}.pbf (попытка {attempt+1}): {e}")
        
        if attempt < retry_count - 1:
            time.sleep(2)  # Ждем перед повторной попыткой
    
    return False

def download_tiles():
    """Загрузка тайлов в заданном диапазоне"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    total_tiles = 0
    downloaded_tiles = 0
    
    # Сначала подсчитаем общее количество тайлов
    for zoom in range(MIN_ZOOM, MAX_ZOOM + 1):
        min_x, max_y = deg2num(MIN_LAT, MIN_LON, zoom)
        max_x, min_y = deg2num(MAX_LAT, MAX_LON, zoom)
        total_tiles += (max_x - min_x + 1) * (max_y - min_y + 1)
    
    print(f"Всего тайлов для загрузки: {total_tiles}")
    
    # Загружаем тайлы
    for zoom in range(MIN_ZOOM, MAX_ZOOM + 1):
        min_x, max_y = deg2num(MIN_LAT, MIN_LON, zoom)
        max_x, min_y = deg2num(MAX_LAT, MAX_LON, zoom)
        
        print(f"Загрузка тайлов для zoom {zoom}: x={min_x}-{max_x}, y={min_y}-{max_y}")
        
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if download_tile(zoom, x, y):
                    downloaded_tiles += 1
                
                time.sleep(DELAY_BETWEEN_REQUESTS)
    
    print(f"Загрузка завершена. Успешно загружено: {downloaded_tiles}/{total_tiles} тайлов")

if __name__ == "__main__":
    download_tiles()
