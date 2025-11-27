# check_tile.py
import os
import sys

# Проверяем, есть ли нужная библиотека
try:
    import mapbox_vector_tile
except ImportError:
    print("⏳ Устанавливаю библиотеку...")
    os.system("pip install mapbox-vector-tile")
    import mapbox_vector_tile

def inspect_tile(filepath):
    """Показывает имя слоя и атрибуты"""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        if len(data) < 100:
            print(f"❌ ТАЙЛ ПУСТОЙ: {filepath} ({len(data)} байт)")
            return
        
        # Декодируем
        tile = mapbox_vector_tile.decode(data)
        
        if not tile:
            print(f"❌ Невалидный тайл: {filepath}")
            return
        
        print(f"✅ {filepath}")
        for layer_name, layer in tile.items():
            features = layer.get('features', [])
            print(f"   📦 Слой '{layer_name}': {len(features)} зданий")
            
            if features:
                # Показать атрибуты первого здания
                props = features[0].get('properties', {})
                print(f"   🔍 Пример атрибутов: {dict(list(props.items())[:5])}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

# Проверяем конкретный тайл
if __name__ == "__main__":
    inspect_tile("tiles/12/2372/1370.pbf")
