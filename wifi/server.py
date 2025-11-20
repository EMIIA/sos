import subprocess
import json
from flask import Flask, jsonify, request

app = Flask(__name__)

def scan_wifi_debug():
    """Сканирует Wi-Fi с подробной отладкой"""
    try:
        print("Запускаю команду netsh...")
        
        result = subprocess.run(
            ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
            capture_output=True,
            text=True,
            encoding='cp866',
            errors='ignore'
        )
        
        print(f"Код возврата: {result.returncode}")
        print(f"Вывод stdout:\n{result.stdout}")
        print(f"Ошибки stderr:\n{result.stderr}")
        
        if result.returncode != 0:
            return [{'error': f'Команда netsh завершилась с ошибкой: {result.stderr}'}]
        
        networks = []
        current = {}
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            print(f"Обрабатываю строку: {line}")
            
            if 'SSID' in line and 'BSSID' not in line:
                if current and current.get('ssid'):
                    networks.append(current)
                current = {
                    'ssid': line.split(':', 1)[1].strip() if ':' in line else 'Скрытая сеть',
                    'mac': '',
                    'signal': -50
                }
            elif 'BSSID' in line:
                bssid = line.split(':', 1)[1].strip() if ':' in line else ''
                current['mac'] = bssid.replace('-', ':').upper()
            elif 'Сигнал' in line or 'Signal' in line:
                try:
                    signal_str = line.split(':', 1)[1].strip()
                    signal_percent = int(signal_str.replace('%', '').strip())
                    current['signal'] = -100 + (signal_percent * 0.6)
                except:
                    current['signal'] = -50
        
        if current and current.get('ssid'):
            networks.append(current)
        
        print(f"Найдено сетей: {len(networks)}")
        print(f"Сети: {json.dumps(networks, ensure_ascii=False, indent=2)}")
        
        return networks
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return [{'error': f'Критическая ошибка: {str(e)}'}]

@app.route('/api/wifi')
def get_wifi():
    networks = scan_wifi_debug()
    return jsonify(networks)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <title>EMIIA.AI MRV Wi-Fi Debug</title>
        <script src='https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.js'></script>
        <link href='https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.css' rel='stylesheet' />
        <style>
            body { margin: 0; font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #00ff88; }
            #map { position: absolute; top: 0; bottom: 0; width: 100%; }
            .controls {
                position: absolute; top: 20px; left: 20px; background: rgba(0,0,0,0.9);
                padding: 20px; border-radius: 15px; border: 1px solid #00ff88; max-width: 450px;
            }
            .btn { padding: 12px 20px; margin: 5px; background: #00ff88; color: #1a1a2e;
                   border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
            .btn:hover { background: #00cc70; }
            .info { margin: 10px 0; font-size: 0.9em; }
            .error { color: #ff4444; }
            .success { color: #00ff88; }
            pre { background: rgba(0,0,0,0.5); padding: 10px; border-radius: 5px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="controls">
            <h2>📡 EMIIA.AI MRV Wi-Fi Debug</h2>
            <button class="btn" onclick="scanWiFi()">🔍 Сканировать Wi-Fi</button>
            <button class="btn" onclick="getOSLocation()">📍 Геолокация ОС</button>
            <div id="status" class="info">Статус: Ожидание...</div>
            <div id="debug" class="info"></div>
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
            
            // Маркер роутера
            new mapboxgl.Marker({ color: '#ff4444' })
                .setLngLat(ROUTER_CONFIG.position)
                .setPopup(new mapboxgl.Popup().setHTML(`
                    <h3>📡 ${ROUTER_CONFIG.ssid}</h3>
                    <p>MAC: ${ROUTER_CONFIG.mac}</p>
                `))
                .addTo(map);
            
            async function scanWiFi() {
                try {
                    document.getElementById('status').innerHTML = '⏳ Сканирование Wi-Fi...';
                    document.getElementById('debug').innerHTML = '';
                    
                    const response = await fetch('/api/wifi');
                    const networks = await response.json();
                    
                    console.log('Получен ответ:', networks);
                    
                    if (networks.length === 0) {
                        throw new Error('Сетей Wi-Fi не найдено');
                    }
                    
                    if (networks[0].error) {
                        throw new Error(networks[0].error);
                    }
                    
                    const router = networks.find(n => 
                        n.ssid === ROUTER_CONFIG.ssid || 
                        n.mac === ROUTER_CONFIG.mac ||
                        n.mac === '28-CD-C4-13-EE-A3'
                    );
                    
                    let html = `<div class="info"><b>Всего сетей: ${networks.length}</b></div>`;
                    
                    networks.forEach(n => {
                        html += `<div class="info" style="font-size:0.8em">
                            SSID: ${n.ssid}<br>
                            MAC: ${n.mac || 'N/A'}<br>
                            Сигнал: ${n.signal.toFixed(1)} dBm
                        </div>`;
                    });
                    
                    document.getElementById('debug').innerHTML = html;
                    
                    if (router) {
                        const distance = calculateDistance(router.signal);
                        document.getElementById('status').innerHTML = `
                            <div class="success">
                                ✅ <b>РОУТЕР НАЙДЕН!</b><br>
                                SSID: ${router.ssid}<br>
                                Сигнал: ${router.signal.toFixed(1)} dBm<br>
                                MAC: ${router.mac}<br>
                                <b style="font-size:1.2em">Расстояние: ${distance.toFixed(2)} м</b>
                            </div>
                        `;
                        
                        new mapboxgl.Marker({ color: '#00ff88' })
                            .setLngLat(ROUTER_CONFIG.position)
                            .setPopup(new mapboxgl.Popup().setHTML(`
                                <h4>📍 Расстояние: ${distance.toFixed(2)} м</h4>
                                <p>Сигнал: ${router.signal.toFixed(1)} dBm</p>
                            `))
                            .addTo(map);
                    } else {
                        document.getElementById('status').innerHTML = `
                            <div class="error">
                                ⚠️ <b>Роутер не найден</b><br>
                                Проверьте SSID: "${ROUTER_CONFIG.ssid}"<br>
                                Ищите в консоли браузера (F12) полный список сетей
                            </div>
                        `;
                        console.log('Все найденные сети:', networks);
                    }
                } catch(e) {
                    document.getElementById('status').innerHTML = `
                        <span class="error">❌ Ошибка: ${e.message}</span>
                    `;
                    console.error('Ошибка:', e);
                }
            }
            
            function getOSLocation() {
                if (!navigator.geolocation) {
                    document.getElementById('status').innerHTML = '<span class="error">❌ Геолокация не поддерживается</span>';
                    return;
                }
                
                document.getElementById('status').innerHTML = '⏳ Запрос геолокации ОС...';
                
                navigator.geolocation.getCurrentPosition(
                    pos => {
                        const { latitude, longitude, accuracy } = pos.coords;
                        document.getElementById('status').innerHTML = `
                            <div class="success">
                                ✅ <b>Геолокация ОС:</b><br>
                                ${latitude.toFixed(6)}, ${longitude.toFixed(6)}<br>
                                Точность: ±${accuracy.toFixed(1)} м
                                ${accuracy > 100 ? '<br><small>Включите Wi-Fi для улучшения точности</small>' : ''}
                            </div>
                        `;
                        
                        new mapboxgl.Marker({ color: '#00ccff' })
                            .setLngLat([longitude, latitude])
                            .setPopup(new mapboxgl.Popup().setText(`Вы здесь: точность ${accuracy} м`))
                            .addTo(map);
                        
                        map.flyTo({ center: [longitude, latitude], zoom: 18 });
                    },
                    err => {
                        document.getElementById('status').innerHTML = `
                            <span class="error">❌ Ошибка: ${err.message}</span>
                        `;
                    },
                    { enableHighAccuracy: true, timeout: 10000 }
                );
            }
            
            function calculateDistance(signalDbm) {
                const txPower = -20; // dBm, мощность роутера
                const pathLoss = txPower - signalDbm;
                return Math.pow(10, (pathLoss - 32.44) / 20);
            }
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("Запуск Flask сервера...")
    print("Откройте браузер по адресу: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
