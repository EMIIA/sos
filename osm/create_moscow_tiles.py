#!/usr/bin/env python3
import json
import os
import math

STATIC_DIR = r"C:\Users\vstar\Desktop\osm\static"
TILES_DIR = os.path.join(STATIC_DIR, "tiles")

def create_moscow_tiles():
    """Создает тайлы для координат Москвы"""
    print("Создание тайлов для Москвы...")
    
    def lon_to_x(lon, zoom): return int((lon + 180) / 360 * (2 ** zoom))
    def lat_to_y(lat, zoom): return int((1 - math.log(math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)) / math.pi) / 2 * (2 ** zoom))
    
    # Координаты Москвы
    moscow_bbox = {
        'min_lon': 37.35, 'max_lon': 37.85,
        'min_lat': 55.55, 'max_lat': 55.91
    }
    
    for zoom in [10, 11, 12, 13, 14]:
        print(f"Zoom {zoom}...")
        
        x_min = lon_to_x(moscow_bbox['min_lon'], zoom)
        x_max = lon_to_x(moscow_bbox['max_lon'], zoom) 
        y_min = lat_to_y(moscow_bbox['max_lat'], zoom)
        y_max = lat_to_y(moscow_bbox['min_lat'], zoom)
        
        print(f"  X: {x_min}-{x_max}, Y: {y_min}-{y_max}")
        
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                tile_dir = os.path.join(TILES_DIR, str(zoom), str(x))
                os.makedirs(tile_dir, exist_ok=True)
                
                # Простые тестовые данные
                tile_data = {
                    "roads": {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "properties": {"highway": "motorway"},
                                "geometry": {
                                    "type": "LineString", 
                                    "coordinates": [[37.6, 55.75], [37.7, 55.8]]
                                }
                            }
                        ]
                    },
                    "buildings": {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature", 
                                "properties": {"building": "yes", "height": 50},
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [[[37.617, 55.755], [37.618, 55.755], [37.618, 55.756], [37.617, 55.756], [37.617, 55.755]]]
                                }
                            }
                        ]
                    }
                }
                
                tile_path = os.path.join(tile_dir, f"{y}.json")
                with open(tile_path, 'w', encoding='utf-8') as f:
                    json.dump(tile_data, f, ensure_ascii=False)
        
        print(f"  Создано тайлов для zoom {zoom}")

if __name__ == "__main__":
    # Удаляем старые тайлы
    import shutil
    if os.path.exists(TILES_DIR):
        shutil.rmtree(TILES_DIR)
    
    create_moscow_tiles()
    print("Готово! Созданы тайлы для Москвы")
