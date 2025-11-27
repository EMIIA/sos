#!/usr/bin/env python3
import osmium
import json
import os
import math
from datetime import datetime

class CentralDistrictHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.buildings = []
        self.roads = []
        
        # Границы центрального федерального округа (приблизительно)
        self.central_district_bbox = {
            'min_lon': 35.0,   # запад
            'max_lon': 41.0,   # восток  
            'min_lat': 54.0,   # юг
            'max_lat': 57.5    # север
        }
        
        self.road_count = 0
        self.building_count = 0
    
    def in_central_district(self, lon, lat):
        """Проверяет, находится ли точка в пределах центрального округа"""
        return (self.central_district_bbox['min_lon'] <= lon <= self.central_district_bbox['max_lon'] and
                self.central_district_bbox['min_lat'] <= lat <= self.central_district_bbox['max_lat'])
    
    def way(self, w):
        try:
            # Обрабатываем дороги
            if 'highway' in w.tags:
                coordinates = []
                valid_points = 0
                
                for node in w.nodes:
                    if node.location.valid():
                        lon, lat = node.location.lon, node.location.lat
                        if self.in_central_district(lon, lat):
                            coordinates.append([round(lon, 6), round(lat, 6)])
                            valid_points += 1
                
                # Нужно минимум 2 точки для дороги
                if valid_points >= 2:
                    properties = {
                        'highway': w.tags['highway'],
                        'osm_id': w.id
                    }
                    
                    # Добавляем дополнительные свойства дорог
                    if 'name' in w.tags:
                        properties['name'] = w.tags['name']
                    if 'maxspeed' in w.tags:
                        properties['maxspeed'] = w.tags['maxspeed']
                    if 'lanes' in w.tags:
                        properties['lanes'] = w.tags['lanes']
                    if 'oneway' in w.tags:
                        properties['oneway'] = w.tags['oneway']
                    
                    self.roads.append({
                        'type': 'Feature',
                        'properties': properties,
                        'geometry': {
                            'type': 'LineString',
                            'coordinates': coordinates
                        }
                    })
                    self.road_count += 1
            
            # Обрабатываем здания
            elif 'building' in w.tags and w.tags['building'] not in ['no', 'false', '0']:
                if len(w.nodes) >= 4:  # Полигон должен иметь хотя бы 4 точки
                    coordinates = []
                    valid_points = 0
                    
                    for node in w.nodes:
                        if node.location.valid():
                            lon, lat = node.location.lon, node.location.lat
                            if self.in_central_district(lon, lat):
                                coordinates.append([round(lon, 6), round(lat, 6)])
                                valid_points += 1
                    
                    if valid_points >= 4:
                        # Замыкаем полигон
                        if coordinates[0] != coordinates[-1]:
                            coordinates.append(coordinates[0])
                        
                        properties = {
                            'building': 'yes',
                            'osm_id': w.id
                        }
                        
                        # Добавляем высоту если есть
                        if 'height' in w.tags:
                            try:
                                properties['height'] = float(w.tags['height'])
                            except:
                                properties['height'] = 10
                        elif 'building:levels' in w.tags:
                            try:
                                levels = float(w.tags['building:levels'])
                                properties['height'] = levels * 3
                                properties['levels'] = levels
                            except:
                                properties['height'] = 10
                        else:
                            properties['height'] = 10
                        
                        # Дополнительные свойства зданий
                        if 'name' in w.tags:
                            properties['name'] = w.tags['name']
                        if 'addr:street' in w.tags:
                            properties['street'] = w.tags['addr:street']
                        if 'addr:housenumber' in w.tags:
                            properties['housenumber'] = w.tags['addr:housenumber']
                        
                        self.buildings.append({
                            'type': 'Feature',
                            'properties': properties,
                            'geometry': {
                                'type': 'Polygon',
                                'coordinates': [coordinates]
                            }
                        })
                        self.building_count += 1
                        
        except Exception as e:
            print(f"Ошибка при обработке way {w.id}: {e}")
    
    def print_stats(self):
        print(f"Обработано дорог: {self.road_count}")
        print(f"Обработано зданий: {self.building_count}")

def create_vector_tiles(roads_geojson, buildings_geojson):
    """Создает структуру векторных тайлов из GeoJSON данных"""
    print("Создаю векторные тайлы...")
    
    # Функции для работы с тайлами
    def lon_to_tile_x(lon, zoom):
        return int((lon + 180.0) / 360.0 * (2 ** zoom))
    
    def lat_to_tile_y(lat, zoom):
        return int((1.0 - math.log(math.tan(lat * math.pi / 180.0) + 1.0 / math.cos(lat * math.pi / 180.0)) / math.pi) / 2.0 * (2 ** zoom))
    
    # Создаем тайлы для разных масштабов
    for zoom in range(10, 15):
        print(f"Создаю тайлы для zoom {zoom}...")
        
        # Собираем объекты для каждого тайла
        tile_features = {}
        
        # Обрабатываем дороги
        for feature in roads_geojson['features']:
            coords = feature['geometry']['coordinates']
            for coord in coords:
                x = lon_to_tile_x(coord[0], zoom)
                y = lat_to_tile_y(coord[1], zoom)
                
                tile_key = f"{zoom}/{x}/{y}"
                if tile_key not in tile_features:
                    tile_features[tile_key] = {'roads': [], 'buildings': []}
                
                # Добавляем дорогу если ее еще нет в этом тайле
                if feature not in tile_features[tile_key]['roads']:
                    tile_features[tile_key]['roads'].append(feature)
        
        # Обрабатываем здания
        for feature in buildings_geojson['features']:
            coords = feature['geometry']['coordinates'][0]  # внешнее кольцо полигона
            for coord in coords:
                x = lon_to_tile_x(coord[0], zoom)
                y = lat_to_tile_y(coord[1], zoom)
                
                tile_key = f"{zoom}/{x}/{y}"
                if tile_key not in tile_features:
                    tile_features[tile_key] = {'roads': [], 'buildings': []}
                
                # Добавляем здание если его еще нет в этом тайле
                if feature not in tile_features[tile_key]['buildings']:
                    tile_features[tile_key]['buildings'].append(feature)
        
        # Сохраняем тайлы
        for tile_key, features in tile_features.items():
            z, x, y = tile_key.split('/')
            
            tile_dir = os.path.join("static", "tiles", z, x)
            os.makedirs(tile_dir, exist_ok=True)
            
            tile_data = {
                "roads": {
                    "type": "FeatureCollection",
                    "features": features['roads']
                },
                "buildings": {
                    "type": "FeatureCollection", 
                    "features": features['buildings']
                }
            }
            
            tile_path = os.path.join(tile_dir, f"{y}.pbf")
            with open(tile_path, 'w', encoding='utf-8') as f:
                json.dump(tile_data, f, ensure_ascii=False)
        
        print(f"  Zoom {zoom}: создано {len(tile_features)} тайлов")

def main():
    print("Извлечение всех дорог и зданий центрального федерального округа...")
    print(f"Время начала: {datetime.now()}")
    
    # Файлы
    pbf_file = "static/central-fed-district-latest.osm.pbf"
    roads_output = "roads_central.geojson"
    buildings_output = "buildings_central.geojson"
    
    if not os.path.exists(pbf_file):
        print(f"Ошибка: Файл {pbf_file} не найден!")
        return
    
    # Обрабатываем PBF файл
    handler = CentralDistrictHandler()
    
    print("Чтение PBF файла... (это может занять несколько минут)")
    handler.apply_file(pbf_file, locations=True)
    
    handler.print_stats()
    
    # Сохраняем GeoJSON файлы
    print("Сохранение GeoJSON файлов...")
    
    roads_geojson = {
        "type": "FeatureCollection",
        "features": handler.roads
    }
    
    buildings_geojson = {
        "type": "FeatureCollection", 
        "features": handler.buildings
    }
    
    with open(roads_output, 'w', encoding='utf-8') as f:
        json.dump(roads_geojson, f, ensure_ascii=False, indent=2)
    
    with open(buildings_output, 'w', encoding='utf-8') as f:
        json.dump(buildings_geojson, f, ensure_ascii=False, indent=2)
    
    print(f"Дороги сохранены в: {roads_output}")
    print(f"Здания сохранены в: {buildings_output}")
    
    # Создаем векторные тайлы
    create_vector_tiles(roads_geojson, buildings_geojson)
    
    print(f"Время окончания: {datetime.now()}")
    print("Готово! Все данные центрального округа извлечены.")

if __name__ == "__main__":
    main()
