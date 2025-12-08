```python
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
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".glb": "model/gltf-binary",
    ".gltf": "model/gltf+json",
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

            # Fonts with CORS headers
            font_match = re.match(r"^/fonts/(.+)/(\d+-\d+)\.pbf$", self.path)
            if font_match:
                fontstack, range_part = font_match.groups()
                fontstack = fontstack.replace("%20", " ")
                
                font_path = os.path.join(STATIC_DIR, "fonts", fontstack, f"{range_part}.pbf")
                
                if os.path.isfile(font_path):
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-protobuf")
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                    self.send_header("Access-Control-Allow-Headers", "Range")
                    self.send_header("Access-Control-Expose-Headers", "Content-Length,Content-Range")
                    
                    with open(font_path, "rb") as f:
                        data = f.read()
                        self.send_header("Content-Length", str(len(data)))
                        self.end_headers()
                        self.wfile.write(data)
                    return
                else:
                    print(f"Font not found: {font_path}")
                    self.send_error(404)
                    return

            # Handle OPTIONS requests for CORS preflight
            if self.path.startswith("/fonts/") and self.command == "OPTIONS":
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Range")
                self.send_header("Access-Control-Max-Age", "86400")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            # Main page - serve index.html from static directory
            if self.path == "/":
                index_path = os.path.join(STATIC_DIR, "index.html")
                if os.path.isfile(index_path):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "public, max-age=60")
                    
                    with open(index_path, "rb") as f:
                        data = f.read()
                        self.send_header("Content-Length", str(len(data)))
                        self.end_headers()
                        self.wfile.write(data)
                    return
                else:
                    self.send_error(404, "index.html not found in static directory")
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
    
    if not generate_ssl_certificates():
        print("SSL setup failed")
        exit(1)
    
    print(f"Starting HTTPS server on port {PORT}")
    print(f"Local: https://localhost:{PORT}")
    print(f"External: https://map.emiia.keenetic.pro")
    print(f"Static: {STATIC_DIR}")
    print("Note: Make sure index.html is in the static directory")
    
    with ThreadedHTTPServer(("0.0.0.0", PORT), MapboxHandler) as server:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(SSL_CERTFILE, SSL_KEYFILE)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")
        except Exception as e:
            print(f"Server error: {e}")
```
