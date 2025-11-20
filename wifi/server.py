from flask import Flask, jsonify, request
import subprocess
import threading
import webbrowser

app = Flask(__name__)

def scan_wifi_windows():
    """Сканирует Wi-Fi и находит ваш роутер"""
    try:
        result = subprocess.run(
            ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
            capture_output=True,
            text=True,
            encoding='cp866'
        )
        
        networks = []
        current = {}
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if 'SSID' in line and 'BSSID' not in line:
                if current.get('ssid'):
                    networks.append(current)
                current = {
                    'ssid': line.split(':')[1].strip() if ':' in line else 'Скрытая сеть',
                    'mac': '',
                    'signal': -50
                }
            elif 'BSSID' in line:
                current['mac'] = line.split(':')[1].strip().replace('-', ':').upper() if ':' in line else ''
            elif 'Сигнал' in line or 'Signal' in line:
                try:
                    signal = int(line.split(':')[1].replace('%', '').strip())
                    current['signal'] = -100 + (signal * 0.6)
                except:
                    pass
        
        if current.get('ssid'):
            networks.append(current)
            
        return networks
    except Exception as e:
        return [{'error': str(e)}]

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <title>EMIIA.AI MRV Wi-Fi</title>
        <script src='https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.js'></script>
        <link href='https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.css' rel='stylesheet' />
        <style>
            body { margin: 0; font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #00ff88; }
            #map { position: absolute; top: 0; bottom: 0; width: 100%; }
            .controls {
                position: absolute; top: 20px; left: 20px; background: rgba(26,26,46,0.9);
                padding: 20px; border-radius: 15px; border: 1px solid #00ff88;
                max-width: 450px; max-height: 80vh; overflow-y: auto;
            }
            .btn { padding: 12px 20px; margin: 5px; background: #00ff88; color: #1a1a2e;
                   border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
            .btn:hover { background: #00cc70; }
            .info { margin: 15px 0; font-size: 0.9em; }
            .error { color: #ff4444; }
            .success { color: #00ff88; }
            h2 { margin-top: 0; color: #00ff88; }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="controls">
            <h2>📡 EMIIA.AI MRV Wi-Fi</h2>
            <button class="btn" onclick="scanWiFi()">🔍 Сканировать Wi-Fi</button>
            <button class="btn" onclick="getOSLocation()">📍 Геолокация ОС</button>
            <div id="status" class="info">Статус: Ожидание...</div>
            <div id="networks" class="info"></div>
        </div>
        
        <script>
            const ROUTER_CONFIG = {
                ssid: 'EMIIA.AI MRV',
                mac: '28-CD-C4-13-EE-A3',
                position: [37.16332212, 55.98346937]
            };
            
            mapboxgl.accessToken = 'pk.eyJ1Ijoia211bm96IiwiYSI6ImNsY3A3NDloaDA2bnozcGxiN2U1Y2I2bWIifQ.WY4_mVStBm5c9CjvWsVy3w';
            
            const map = new mapboxgl.Map({
                container: 'map',
                style: 'mapbox://styles/mapbox/satellite-v9',
                center: ROUTER_CONFIG.position,
                zoom: 20,
                pitch: 45
            });
            
            // Добавляем роутер
            new mapboxgl.Marker({ color: '#ff4444' })
                .setLngLat(ROUTER_CONFIG.position)
                .setPopup(new mapboxgl.Popup().setHTML(`
                    <h3>📡 Роутер EMIIA.AI MRV</h3>
                    <p>MAC: ${ROUTER_CONFIG.mac}</p>
                    <p>Координаты: ${ROUTER_CONFIG.position[1].toFixed(6)}, ${ROUTER_CONFIG.position[0].toFixed(6)}</p>
                `))
                .addTo(map);
            
            async function scanWiFi() {
                try {
                    document.getElementById('status').innerHTML = '⏳ Сканирование Wi-Fi...';
                    
                    const response = await fetch('/api/wifi');
                    const networks = await response.json();
                    
                    if (networks.error) throw new Error(networks.error);
                    
                    const router = networks.find(n => 
                        n.ssid === ROUTER_CONFIG.ssid || n.mac === ROUTER_CONFIG.mac
                    );
                    
                    if (router) {
                        const distance = calculateDistance(router.signal);
                        document.getElementById('status').innerHTML = `
                            <div class="success">
                                ✅ <b>Роутер найден!</b><br>
                                SSID: ${router.ssid}<br>
                                Сигнал: ${router.signal.toFixed(1)} dBm<br>
                                MAC: ${router.mac}<br>
                                <b>Расстояние: ${distance.toFixed(2)} м</b>
                            </div>
                        `;
                        
                        // Добавляем маркер с расстоянием
                        new mapboxgl.Marker({ color: '#00ff88' })
                            .setLngLat(ROUTER_CONFIG.position)
                            .setPopup(new mapboxgl.Popup().setHTML(`
                                <h4>📍 Расстояние: ${distance.toFixed(2)} м</h4>
                                <p>Сигнал: ${router.signal.toFixed(1)} dBm</p>
                            `))
                            .addTo(map);
                        
                        document.getElementById('networks').innerHTML = `Всего сетей: ${networks.length}`;
                    } else {
                        document.getElementById('status').innerHTML = `
                            <div class="error">
                                ⚠️ Роутер "${ROUTER_CONFIG.ssid}" не найден<br>
                                Найдено сетей: ${networks.length}
                            </div>
                        `;
                        console.log('Найденные сети:', networks);
                    }
                } catch(e) {
                    document.getElementById('status').innerHTML = `
                        <span class="error">❌ Ошибка: ${e.message}</span>
                    `;
                }
            }
            
            function getOSLocation() {
                if (!navigator.geolocation) {
                    alert('Геолокация не поддерживается');
                    return;
                }
                
                navigator.geolocation.getCurrentPosition(
                    pos => {
                        const { latitude, longitude, accuracy } = pos.coords;
                        document.getElementById('status').innerHTML = `
                            <div class="success">
                                📍 Геолокация ОС: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}<br>
                                Точность: ±${accuracy.toFixed(1)} м
                            </div>
                        `;
                        
                        new mapboxgl.Marker({ color: '#00ccff' })
                            .setLngLat([longitude, latitude])
                            .setPopup(new mapboxgl.Popup().setText(`Ваше местоположение (точность: ${accuracy} м)`))
                            .addTo(map);
                        
                        map.flyTo({ center: [longitude, latitude], zoom: 18 });
                    },
                    err => alert('Ошибка геолокации: ' + err.message),
                    { enableHighAccuracy: true, timeout: 10000 }
                );
            }
            
            function calculateDistance(signalDbm) {
                // Формула FSPL для 2.4 GHz
                const txPower = -20; // dBm
                const pathLoss = txPower - signalDbm;
                return Math.pow(10, (pathLoss - 32.44) / 20); // в метрах
            }
        </script>
    </body>
    </html>
    '''


if __name__ == '__main__':
    # Открываем браузер автоматически
    threading.Timer(1.5, lambda: webbrowser.open('http://localhost:5000')).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
