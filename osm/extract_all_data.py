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
            
            # ИСПРАВЛЕННАЯ СТРОКА - сохраняем прямо в static
            tile_dir = os.path.join(r"C:\Users\vstar\Desktop\osm\static", "tiles", z, x)
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
