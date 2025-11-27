import json
import glob
import sqlite3

# Если у вас .mbtiles
conn = sqlite3.connect("moscow.mbtiles")
cursor = conn.cursor()
cursor.execute("SELECT value FROM metadata WHERE name='json'")
metadata = json.loads(cursor.fetchone()[0])
print("Слои в тайлах:", [l['id'] for l in metadata.get('vector_layers', [])])
conn.close()

# Если у вас отдельные .pbf файлы
import mapbox_vector_tile
tile = open(glob.glob("10/**/*.pbf")[0], "rb").read()
decoded = mapbox_vector_tile.decode(tile)
print("Найдены слои:", list(decoded.keys()))
