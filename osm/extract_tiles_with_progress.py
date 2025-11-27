#!/usr/bin/env python3
import osmium
import json
import os
import math
import time

STATIC_DIR = r"C:\Users\vstar\Desktop\osm\static"
PBF_FILE = os.path.join(STATIC_DIR, "central-fed-district-latest.osm.pbf")
TILES_DIR = os.path.join(STATIC_DIR, "tiles")

print("=== ИЗВЛЕЧЕНИЕ ТАЙЛОВ ИЗ PBF ===")
print(f"PBF файл: {PBF_FILE}")
print(f"Размер файла: {os.path.getsize(PBF_FILE) // 1024 // 1024} МБ")
print()

class MoscowExtractor(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.buildings = []
        self.roads = []
        self.way_count = 0
        self.start_time = time.time()
        
        # Границы Москвы
        self.bbox = {
            "min_lon": 37.35, "max_lon": 37.85,
            "min_lat": 55.55, "max_lat": 55.91
        }
        
    def in_bbox(self, lon, lat):
        return (self.bbox["min_lon"] <= lon <= self.bbox["max_lon"] and
                self.bbox["min_lat"] <= lat <= self.bbox["max_lat"])
    
    def way(self, w):
        self.way_count += 1
        
        # Показываем прогресс каждые 10000 ways
        if self.way_count % 10000 == 0:
            elapsed = time.time() - self.start_time
            print(f"Обработано {self.way_count:,} ways... Дорог: {len(self.roads)}, Зданий: {len(self.buildings)} [Время: {elapsed:.1f}с]")
        
        # Дороги
        if "highway" in w.tags:
            coords = []
            for node in w.nodes:
                if node.location.valid():
                    lon, lat = node.location.lon, node.location.lat
                    if self.in_bbox(lon, lat):
                        coords.append([round(lon, 6), round(lat, 6)])
            
            if len(coords) >= 2:
                self.roads.append({
                    "type": "Feature",
                    "properties": {"highway": w.tags["highway"]},
                    "geometry": {"type": "LineString", "coordinates": coords}
                })
        
        # Здания
        elif "building" in w.tags and w.tags["building"] not in ["no", "false", "0"]:
            coords = []
            for node in w.nodes:
                if node.location.valid():
                    lon, lat = node.location.lon, node.location.lat
                    if self.in_bbox(lon, lat):
                        coords.append([round(lon, 6), round(lat, 6)])
            
            if len(coords) >= 4:
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                
                height = 10
                if "height" in w.tags:
                    try: height = float(w.tags["height"])
                    except: pass
                elif "building:levels" in w.tags:
                    try: height = float(w.tags["building:levels"]) * 3
                    except: pass
                
                self.buildings.append({
                    "type": "Feature",
                    "properties": {"building": "yes", "height": height},
                    "geometry": {"type": "Polygon", "coordinates": [coords]}
                })

def create_tiles(roads, buildings):
    print("\n=== СОЗДАНИЕ ТАЙЛОВ ===")
    
    def lon_to_x(lon, zoom): return int((lon + 180) / 360 * (2 ** zoom))
    def lat_to_y(lat, zoom): return int((1 - math.log(math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)) / math.pi) / 2 * (2 ** zoom))
    
    total_tiles = 0
    
    # Создаем тайлы для масштабов 10-14
    for zoom in [10, 11, 12, 13, 14]:
        print(f"\nZoom {zoom}...")
        
        # Диапазон тайлов для Москвы
        x_min, x_max = lon_to_x(37.35, zoom), lon_to_x(37.85, zoom)
        y_min, y_max = lat_to_y(55.91, zoom), lat_to_y(55.55, zoom)
        
        print(f"  Диапазон тайлов: X[{x_min}-{x_max}], Y[{y_min}-{y_max}]")
        
        created = 0
        # Ограничиваем количество тайлов для теста
        for x in range(x_min, min(x_max + 1, x_min + 5)):
            for y in range(y_min, min(y_max + 1, y_min + 5)):
                tile_dir = os.path.join(TILES_DIR, str(zoom), str(x))
                os.makedirs(tile_dir, exist_ok=True)
                
                # Берем объекты для этого тайла
                tile_roads = roads[:20]  # первые 20 дорог
                tile_buildings = buildings[:10]  # первые 10 зданий
                
                tile_data = {
                    "roads": {"type": "FeatureCollection", "features": tile_roads},
                    "buildings": {"type": "FeatureCollection", "features": tile_buildings}
                }
                
                tile_path = os.path.join(tile_dir, f"{y}.pbf")
                with open(tile_path, "w", encoding="utf-8") as f:
                    json.dump(tile_data, f, ensure_ascii=False)
                
                created += 1
                total_tiles += 1
        
        print(f"  Создано тайлов: {created}")
    
    return total_tiles

# ЗАПУСК
if __name__ == "__main__":
    if not os.path.exists(PBF_FILE):
        print(f"ОШИБКА: Файл {PBF_FILE} не найден!")
        exit(1)
    
    print("Чтение PBF файла...")
    print("Это может занять 5-15 минут в зависимости от скорости диска")
    print("=" * 50)
    
    start_time = time.time()
    extractor = MoscowExtractor()
    extractor.apply_file(PBF_FILE, locations=True)
    
    read_time = time.time() - start_time
    
    print("\n" + "=" * 50)
    print("ЧТЕНИЕ ЗАВЕРШЕНО!")
    print(f"Всего обработано ways: {extractor.way_count:,}")
    print(f"Найдено дорог: {len(extractor.roads):,}")
    print(f"Найдено зданий: {len(extractor.buildings):,}")
    print(f"Время чтения: {read_time:.1f} секунд")
    
    # Создаем тайлы
    tile_start = time.time()
    total_tiles = create_tiles(extractor.roads, extractor.buildings)
    tile_time = time.time() - tile_start
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 50)
    print("ГОТОВО!")
    print(f"Создано тайлов: {total_tiles}")
    print(f"Время создания тайлов: {tile_time:.1f} секунд")
    print(f"Общее время: {total_time:.1f} секунд")
    print(f"Тайлы сохранены в: {TILES_DIR}")
