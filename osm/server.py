#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import http.server
import socketserver
import os
import gzip
import re
import socket
import json

# === НАСТРОЙКИ ===
PORT = 8001
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Указываем прямую путь к вашей папке static
STATIC_DIR = r"C:\Users\vstar\Desktop\osm\static"

# === ФУНКЦИЯ ДЛЯ СОЗДАНИЯ ТЕСТОВЫХ ТАЙЛОВ ===
def create_test_tile(z, x, y):
    """Создает тестовый тайл на лету"""
    # Простые тестовые данные Москвы
    features = []
    
    # Основные дороги Москвы
    roads = [
        {"type": "motorway", "name": "МКАД", "coords": [
            [37.368, 55.895], [37.842, 55.895], [37.842, 55.615], [37.368, 55.615]
        ]},
        {"type": "primary", "name": "Ленинградский пр-т", "coords": [
            [37.4, 55.8], [37.7, 55.8]
        ]},
        {"type": "secondary", "name": "Тверская ул", "coords": [
            [37.6, 55.76], [37.6, 55.75]
        ]}
    ]
    
    for road in roads:
        features.append({
            "type": "Feature",
            "properties": {"highway": road["type"], "name": road["name"]},
            "geometry": {
                "type": "LineString", 
                "coordinates": road["coords"]
            }
        })
    
    # Здания в центре Москвы
    buildings = [
        {"height": 50, "coords": [[37.617, 55.755], [37.618, 55.755], [37.618, 55.756], [37.617, 55.756], [37.617, 55.755]]},
        {"height": 30, "coords": [[37.615, 55.754], [37.616, 55.754], [37.616, 55.755], [37.615, 55.755], [37.615, 55.754]]}
    ]
    
    for building in buildings:
        features.append({
            "type": "Feature",
            "properties": {"building": "yes", "height": building["height"]},
            "geometry": {
                "type": "Polygon",
                "coordinates": [building["coords"]]
            }
        })
    
    tile_data = {
        "roads": {
            "type": "FeatureCollection",
            "features": [f for f in features if f["geometry"]["type"] == "LineString"]
        },
        "buildings": {
            "type": "FeatureCollection", 
            "features": [f for f in features if f["geometry"]["type"] == "Polygon"]
        }
    }
    
    return json.dumps(tile_data).encode('utf-8')

# === HTML СТРАНИЦА ===
HTML_CONTENT = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Карта Москвы</title>
    <script src="/static/mapbox-gl.js"></script>
    <link href="/static/mapbox-gl.css" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; }
        #info {
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: Arial;
            font-size: 12px;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="info">Загрузка карты...</div>

    <script>
        // Обход проверки токена
        const originalError = console.error;
        console.error = function(...args) {
            if (args[0] && args[0].includes('access token')) {
                console.log('Офлайн режим активирован');
                return;
            }
            originalError.apply(console, args);
        };

        // Создаем карту
        const map = new mapboxgl.Map({
            container: 'map',
            style: '/static/osm_style.json',
            center: [37.617, 55.755],
            zoom: 11,
            pitch: 45,
            bearing: 0,
            antialias: true,
            accessToken: 'offline'
        });

        map.on('load', () => {
            document.getElementById('info').textContent = 'Карта Москвы загружена!';
            console.log('Карта загружена');
        });

        map.on('error', (e) => {
            if (e.error && e.error.message && e.error.message.includes('access token')) {
                console.log('Работаем в офлайн режиме');
                return;
            }
            console.error('Ошибка:', e.error);
        });

        // Добавляем элементы управления
        map.addControl(new mapboxgl.NavigationControl());
    </script>
</body>
</html>'''.encode('utf-8')

# === MIME ТИПЫ ===
MIME_TYPES = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".pbf": "application/x-protobuf",
    ".html": "text/html",
}

# === ОБРАБОТЧИК ЗАПРОСОВ ===
class MapboxHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        """Минимальное логирование"""
        print(f"{self.client_address[0]} - {format % args}")

    def send_compressed(self, data, content_type, ext):
        """Отправка с gzip-сжатием"""
        accept_encoding = self.headers.get("Accept-Encoding", "")
        
        if ext != ".pbf" and "gzip" in accept_encoding and len(data) > 512:
            compressed = gzip.compress(data, compresslevel=6)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(compressed)))
            self.end_headers()
            self.wfile.write(compressed)
        else:
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    def do_GET(self):
        try:
            # Статические файлы
            if self.path.startswith("/static/"):
                file_path = os.path.join(STATIC_DIR, self.path[8:])
                
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file_path)[1].lower()
                    content_type = MIME_TYPES.get(ext, "text/plain")
                    
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Cache-Control", "public, max-age=3600")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    
                    with open(file_path, "rb") as f:
                        self.send_compressed(f.read(), content_type, ext)
                    return
                
                self.send_error(404)
                return

            # Векторные тайлы
            match = re.match(r"^/tiles/(\d+)/(\d+)/(\d+)\.pbf$", self.path)
            if match:
                z, x, y = match.groups()
                
                # Ищем тайл в разных возможных папках
                possible_paths = [
                    os.path.join(STATIC_DIR, "moscow_tiles", z, x, f"{y}.pbf"),
                    os.path.join(STATIC_DIR, "tiles", z, x, f"{y}.pbf"),
                    os.path.join(STATIC_DIR, "vector_tiles", z, x, f"{y}.pbf")
                ]
                
                for tile_path in possible_paths:
                    if os.path.isfile(tile_path):
                        self.send_response(200)
                        self.send_header("Content-Type", "application/x-protobuf")
                        self.send_header("Cache-Control", "public, max-age=86400")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        
                        with open(tile_path, "rb") as f:
                            self.send_compressed(f.read(), "application/x-protobuf", ".pbf")
                        return
                
                # Если тайл не найден, создаем тестовый
                self.send_response(200)
                self.send_header("Content-Type", "application/x-protobuf")
                self.send_header("Cache-Control", "public, max-age=3600")
                self.send_header("Access-Control-Allow-Origin", "*")
                
                test_data = create_test_tile(int(z), int(x), int(y))
                self.send_compressed(test_data, "application/x-protobuf", ".pbf")
                return

            # Главная страница
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "public, max-age=60")
                self.send_header("Content-Length", str(len(HTML_CONTENT)))
                self.end_headers()
                self.wfile.write(HTML_CONTENT)
                return

            self.send_error(404)

        except (ConnectionAbortedError, BrokenPipeError):
            pass
        except Exception as e:
            print(f"Error: {e}")
            try:
                self.send_error(500)
            except:
                pass

# === СЕРВЕР ===
class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    request_queue_size = 100
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# === ЗАПУСК ===
if __name__ == "__main__":
    # Проверяем существование папки static
    if not os.path.isdir(STATIC_DIR):
        print(f"ERROR: Directory {STATIC_DIR} not found")
        print("Please check the path to your static folder")
        exit(1)
        
    print(f"=== Сервер карты Москвы ===")
    print(f"URL: http://localhost:{PORT}")
    print(f"Static folder: {STATIC_DIR}")
    print("=" * 50)
    
    with ThreadedHTTPServer(("", PORT), MapboxHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nСервер остановлен")
