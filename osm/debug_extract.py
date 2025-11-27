#!/usr/bin/env python3
import traceback
import sys

try:
    import osmium
    import json
    import os
    import math
    from datetime import datetime

    print("=== ДЕБАГ СКРИПТА ===")
    
    STATIC_DIR = r"C:\Users\vstar\Desktop\osm\static"
    PBF_FILE = os.path.join(STATIC_DIR, "central-fed-district-latest.osm.pbf")
    
    print(f"Проверяю файл: {PBF_FILE}")
    print(f"Файл существует: {os.path.exists(PBF_FILE)}")
    
    if os.path.exists(PBF_FILE):
        print(f"Размер файла: {os.path.getsize(PBF_FILE)} байт")
    else:
        print("Файл не найден!")
        sys.exit(1)
    
    print("Пытаюсь прочитать PBF файл...")
    
    class TestHandler(osmium.SimpleHandler):
        def __init__(self):
            super().__init__()
            self.count = 0
        
        def way(self, w):
            self.count += 1
            if self.count % 10000 == 0:
                print(f"Обработано ways: {self.count}")
    
    handler = TestHandler()
    handler.apply_file(PBF_FILE, locations=True)
    print(f"Всего обработано ways: {handler.count}")
    
except Exception as e:
    print(f"ОШИБКА: {e}")
    print("Трассировка:")
    traceback.print_exc()
    input("Нажмите Enter для выхода...")
