import http.server
import socketserver
import os
import gzip
import re
import socket
import ssl
from functools import lru_cache

# === SETTINGS ===
PORT = 8002
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
SSL_CERTFILE = os.path.join(BASE_DIR, "cert.pem")
SSL_KEYFILE = os.path.join(BASE_DIR, "key.pem")

# === HTML CONTENT ===
HTML_CONTENT = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>SPATIAL INTELLIGENCE</title>
    <script src="/static/mapbox-gl.js"></script>
    <link href="/static/mapbox-gl.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css.css">
    <style>
        body { margin: 0; padding: 0; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; background: #1a1a1a; }
        #info {
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: system-ui;
            font-size: 12px;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        const originalError = console.error;
        console.error = function(...args) {
            if (args[0] && args[0].includes('access token')) {
                console.log('Offline mode activated');
                return;
            }
            originalError.apply(console, args);
        };

        const map = new mapboxgl.Map({
            container: 'map', 
            style: '/static/moscow_style_2.json',
            zoom: 13,
            center: [37.617, 55.755],
            pitch: 45,
            bearing: 0,
            antialias: true,
            accessToken: 'EMIIA_AI_API_KEY',
            localFontFamily: 'Montserrat, Arial, sans-serif'
        });

        map.on('load', () => {
            console.log('Map loaded');
            document.getElementById('status').textContent = 'Map loaded';
        });

        map.on('sourcedata', (e) => {
            if (e.sourceId === 'moscow-buildings') {
                if (e.isSourceLoaded) {
                    console.log('Buildings loaded');
                    document.getElementById('status').textContent = 'Buildings loaded';
                }
                if (e.tile) {
                    console.log(`Tile: ${e.tile.tileID.z}/${e.tile.tileID.x}/${e.tile.tileID.y}`);
                }
            }
        });

        map.on('data', (e) => {
            if (e.dataType === 'source' && e.tile) {
                document.getElementById('status').textContent = 
                    `Tile: ${e.tile.tileID.z}/${e.tile.tileID.x}/${e.tile.tileID.y}`;
            }
        });

        map.on('error', (e) => {
            if (e.error && e.error.message && e.error.message.includes('access token')) {
                console.log('Working in offline mode');
                return;
            }
            console.error('Error:', e.error);
        });

        setInterval(() => {
            const layers = map.getStyle().layers || [];
            const buildingLayer = layers.find(layer => layer.id === 'buildings-3d');
            if (buildingLayer && buildingLayer.visibility !== 'visible') {
                console.log('Restoring building visibility');
                map.setLayoutProperty('buildings-3d', 'visibility', 'visible');
                map.setLayoutProperty('buildings-outline', 'visibility', 'visible');
            }
        }, 1000);
    </script>
</body>
</html>'''.encode('utf-8')

# === TILE PATH CACHE ===
@lru_cache(maxsize=2048)
def get_tile_path(z, x, y):
    """Returns tile path if exists, else None"""
    path = os.path.join(STATIC_DIR, z, x, f"{y}.pbf")
    return path if os.path.isfile(path) else None

# === MIME TYPES ===
MIME_TYPES = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".pbf": "application/x-protobuf",
    ".html": "text/html",
}

# === REQUEST HANDLER ===
class MapboxHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        """Disable request logging"""
        pass

    def send_compressed(self, data, content_type, ext):
        """Send with gzip compression (except PBF)"""
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
            # Static files
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

            # Vector tiles
            match = re.match(r"^/tiles/(\d+)/(\d+)/(\d+)\.pbf$", self.path)
            if match:
                z, x, y = match.groups()
                tile_path = get_tile_path(z, x, y)
                
                if tile_path:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-protobuf")
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    
                    with open(tile_path, "rb") as f:
                        self.send_compressed(f.read(), "application/x-protobuf", ".pbf")
                    return
                self.send_error(404)
                return

            # Main page
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

# === MULTITHREADED SERVER ===
class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    request_queue_size = 100
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

# === SSL CERTIFICATE GENERATION ===
def generate_ssl_certificates():
    """Generate self-signed SSL certificates if they don't exist"""
    if os.path.isfile(SSL_CERTFILE) and os.path.isfile(SSL_KEYFILE):
        return True
        
    print("Generating SSL certificates...")
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "map.emiia.keenetic.pro"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("map.emiia.keenetic.pro"),
                x509.DNSName("localhost"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write private key
        with open(SSL_KEYFILE, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))
        
        # Write certificate
        with open(SSL_CERTFILE, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
            
        print("SSL certificates generated successfully")
        return True
        
    except ImportError:
        print("ERROR: Install cryptography module: pip install cryptography")
        return False

# === STARTUP ===
if __name__ == "__main__":
    if not os.path.isdir(STATIC_DIR):
        print(f"ERROR: Directory {STATIC_DIR} not found")
        exit(1)
    
    # Generate or check SSL certificates
    if not generate_ssl_certificates():
        print("SSL setup failed")
        exit(1)
    
    print(f"Starting HTTPS server on port {PORT}")
    print(f"Local: https://localhost:{PORT}")
    print(f"External: https://map.emiia.keenetic.pro")
    print(f"Static: {STATIC_DIR}")
    
    with ThreadedHTTPServer(("0.0.0.0", PORT), MapboxHandler) as server:
        # Setup SSL
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(SSL_CERTFILE, SSL_KEYFILE)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")
        except Exception as e:
            print(f"Server error: {e}")
