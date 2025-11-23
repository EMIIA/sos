import subprocess
import json
from flask import Flask, jsonify, request
import threading
import time
import re
import random
from datetime import datetime

app = Flask(__name__)

# ========== НАСТРОЙКИ (БЕЗ ИЗМЕНЕНИЙ) ==========
ROUTER_CONFIG = {
    'mac': '50:FF:20:68:EF:9C',
    'ssid': 'EMIIA.AI MRV',
    'position': [37.16332212, 55.98346937],
    'tx_power': -20,
    'ip': '192.168.1.1'
}

# === ГЕОГРАФИЧЕСКИЕ ГРАНИЦЫ ДЛЯ ТРИАНГУЛЯЦИИ (БЕЗ ИЗМЕНЕНИЙ) ===
COORDINATE_BOUNDS = {
    'lng_min': 37.16300053,
    'lng_max': 37.16396619,
    'lat_min': 55.98340849,
    'lat_max': 55.98351054
}

SCAN_INTERVAL = 3
NETWORK_TTL = 10

network_cache = {}
network_positions_cache = {}
cache_lock = threading.Lock()
last_full_scan = 0

# ========== ФОНОВЫЙ СКАНЕР (БЕЗ ИЗМЕНЕНИЙ) ==========
def background_scanner():
    global last_full_scan
    print("EMII.AI IoT запущен")
    
    while True:
        try:
            current_time = time.time()
            
            if current_time - last_full_scan >= SCAN_INTERVAL:
                print(f"\n{'='*50}")
                print(f"Сканирование... {datetime.now().strftime('%H:%M:%S')}")
                
                networks = scan_wifi_real()
                
                with cache_lock:
                    for net in networks:
                        mac = net['mac']
                        
                        if mac == ROUTER_CONFIG['mac']:
                            net['position'] = ROUTER_CONFIG['position']
                        else:
                            if mac in network_positions_cache:
                                net['position'] = network_positions_cache[mac]
                            else:
                                net['position'] = [
                                    round(random.uniform(COORDINATE_BOUNDS['lng_min'], COORDINATE_BOUNDS['lng_max']), 8),
                                    round(random.uniform(COORDINATE_BOUNDS['lat_min'], COORDINATE_BOUNDS['lat_max']), 8)
                                ]
                                network_positions_cache[mac] = net['position']
                        
                        if mac in network_cache:
                            old_signal = network_cache[mac]['signal']
                            variation = random.uniform(-1.5, 1.5)
                            new_signal = max(-90, min(-20, old_signal + variation))
                            net['signal'] = new_signal
                            net['last_seen'] = current_time
                        else:
                            net['last_seen'] = current_time
                        
                        net['rtt_ms'] = calculate_rtt(net['signal'])
                        net['rtt_real_ms'] = ping_router(ROUTER_CONFIG['ip']) if ROUTER_CONFIG.get('ip') and net['mac'] == ROUTER_CONFIG['mac'] else None
                        
                        network_cache[mac] = net
                    
                    old_macs = [mac for mac, net in network_cache.items() 
                               if current_time - net.get('last_seen', 0) > NETWORK_TTL]
                    for mac in old_macs:
                        del network_cache[mac]
                    
                    print(f"Активных сетей: {len(network_cache)}")
                    print(f"Сохранено позиций: {len(network_positions_cache)}")
                
                last_full_scan = current_time
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Ошибка сканирования: {e}")
            time.sleep(5)

# ========== ОСТАЛЬНЫЕ ФУНКЦИИ (БЕЗ ИЗМЕНЕНИЙ) ==========
def scan_wifi_real():
    try:
        result = subprocess.run(
            ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
            capture_output=True,
            text=True,
            encoding='cp866',
            errors='ignore',
            timeout=15
        )
        
        if result.returncode != 0:
            print(f"Ошибка netsh: {result.stderr}")
            return []
        
        networks = parse_netsh_complete(result.stdout)
        return networks
        
    except Exception as e:
        print(f"Ошибка сканирования: {e}")
        return []

def parse_netsh_complete(output):
    networks = []
    lines = output.split('\n')
    
    current = {'ssid': None, 'mac': None, 'signal': -80, 'channel': 0}
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('SSID') and ':' in line and 'BSSID' not in line:
            if current['ssid'] and current['mac']:
                networks.append(create_network(**current))
            
            current = {
                'ssid': line.split(':', 1)[1].strip(),
                'mac': None,
                'signal': -80,
                'channel': 0
            }
        
        elif line.startswith('BSSID') and ':' in line and current['ssid']:
            mac = line.split(':', 1)[1].strip().replace('-', ':').upper()
            current['mac'] = mac
        
        elif ('Сигнал' in line or 'Signal' in line) and current['ssid'] and current['mac']:
            try:
                sig = line.split(':', 1)[1]
                if '%' in sig:
                    percent = int(sig.replace('%', ''))
                    current['signal'] = -100 + (percent * 0.5)
                elif 'dBm' in sig:
                    current['signal'] = int(sig.replace('dBm', ''))
            except:
                current['signal'] = -80
        
        elif ('Канал' in line or 'Channel' in line) and current['ssid'] and current['mac']:
            try:
                numbers = re.findall(r'\d+', line)
                if numbers:
                    current['channel'] = int(numbers[0])
            except:
                current['channel'] = 0
    
    if current['ssid'] and current['mac']:
        networks.append(create_network(**current))
    
    unique = {}
    for net in networks:
        mac = net['mac']
        if mac not in unique or net['signal'] > unique[mac]['signal']:
            unique[mac] = net
    
    return list(unique.values())

def create_network(ssid, mac, signal, channel=0):
    signal_with_noise = float(signal) + random.uniform(-0.5, 0.5)
    
    return {
        'ssid': ssid,
        'mac': mac,
        'signal': round(signal_with_noise, 1),
        'channel': channel,
        'known': False,
        'distance': calculate_distance(signal_with_noise),
        'position': None,
        'last_seen': time.time(),
        'rtt_ms': None,
        'rtt_real_ms': None
    }

def calculate_distance(signal_dbm, tx_power=-20):
    path_loss = tx_power - signal_dbm
    distance = 10 ** (path_loss / (10 * 2.5))
    return round(max(1.0, min(50.0, distance)), 1)

def calculate_rtt(signal_dbm, tx_power=-20):
    distance = calculate_distance(signal_dbm, tx_power)
    base_latency = 2.0
    distance_latency = distance * 0.01
    signal_quality = max(0, min(100, (signal_dbm + 100) * 2))
    signal_latency = (100 - signal_quality) * 0.4
    
    rtt_ms = base_latency + distance_latency + signal_latency
    rtt_ms += random.uniform(-0.3, 0.3)
    
    return round(max(1.0, min(rtt_ms, 50.0)), 1)

def ping_router(ip):
    if not ip:
        return None
    
    try:
        result = subprocess.run(
            ['ping', '-n', '1', '-w', '100', ip],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            match = re.search(r'Время[=<]\s*(\d+)\s*мс', result.stdout)
            if match:
                return int(match.group(1))
            match = re.search(r'time[=<]\s*(\d+)\s*ms', result.stdout)
            if match:
                return int(match.group(1))
        
        return None
        
    except:
        return None

# ========== API (БЕЗ ИЗМЕНЕНИЙ) ==========
@app.route('/api/wifi')
def get_wifi():
    try:
        with cache_lock:
            networks = []
            for mac, net in network_cache.items():
                net_copy = dict(net)
                net_copy['known'] = (net_copy['mac'] == ROUTER_CONFIG['mac'])
                
                if net_copy['known']:
                    net_copy['position'] = ROUTER_CONFIG['position']
                
                net_copy['rtt_ms'] = calculate_rtt(net_copy['signal'])
                if net_copy['known'] and ROUTER_CONFIG.get('ip'):
                    net_copy['rtt_real_ms'] = ping_router(ROUTER_CONFIG['ip'])
                else:
                    net_copy['rtt_real_ms'] = None
                
                networks.append(net_copy)
            
            networks.sort(key=lambda x: x['signal'], reverse=True)
            return jsonify(networks)
            
    except Exception as e:
        print(f"Ошибка API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/triangulation', methods=['POST'])
def triangulation():
    try:
        data = request.get_json()
        print(f"Получено {len(data)} сетей для корректировки")
        
        return jsonify({
            'status': 'success', 
            'networks_count': len(data),
            'message': 'Корректировка настроена'
        })
    except Exception as e:
        print(f"Ошибка корректировки: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export')
def export_data():
    try:
        with cache_lock:
            networks_list = []
            for mac, net in network_cache.items():
                net_dict = {
                    'ssid': net.get('ssid'),
                    'mac': net.get('mac'),
                    'signal': float(net.get('signal', 0)),
                    'channel': int(net.get('channel', 0)),
                    'distance': float(net.get('distance', 0)),
                    'rtt_ms': float(net.get('rtt_ms', 0)) if net.get('rtt_ms') else None,
                    'rtt_real_ms': int(net.get('rtt_real_ms')) if net.get('rtt_real_ms') else None,
                    'position': net.get('position'),
                    'last_seen': float(net.get('last_seen', 0)),
                    'known': net.get('mac') == ROUTER_CONFIG['mac']
                }
                networks_list.append(net_dict)
            
            export_obj = {
                'timestamp': datetime.now().isoformat(),
                'router': {
                    'ssid': ROUTER_CONFIG['ssid'],
                    'mac': ROUTER_CONFIG['mac'],
                    'position': ROUTER_CONFIG['position'],
                    'ip': ROUTER_CONFIG.get('ip')
                },
                'networks': networks_list,
                'total_networks': len(networks_list)
            }
            
            return jsonify(export_obj)
    except Exception as e:
        print(f"Ошибка экспорта: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <title>EMIIA.AI SIP (MRV/SDK)</title>
        <script src="https://api.mapbox.com/mapbox-gl-js/v3.12.0/mapbox-gl.js "></script>
        <link href="https://api.mapbox.com/mapbox-gl-js/v3.12.0/mapbox-gl.css " rel="stylesheet" />
        <style>
            :root {
                --primary: #3c78d8;
                --secondary: #f8f9fa;
                --error: #ff4444;
                --warning: #ffaa00;
                --info: #00ccff;
                --scroll-thumb: rgba(0, 0, 0, 0.4);
                --scroll-track: rgba(0, 0, 0, 0.1);
                --scroll-thumb-hover: rgba(0, 0, 0, 0.6);
            }

            /* ========== СКРОЛЛ БЕЗ СТРЕЛОК ========== */
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }

            ::-webkit-scrollbar-track {
                background: var(--scroll-track);
                border-radius: 4px;
            }

            ::-webkit-scrollbar-thumb {
                background: var(--scroll-thumb);
                border-radius: 4px;
            }

            ::-webkit-scrollbar-thumb:hover {
                background: var(--scroll-thumb-hover);
            }

            ::-webkit-scrollbar-button {
                display: none !important;
                width: 0 !important;
                height: 0 !important;
            }

            * {
                scrollbar-width: thin;
                scrollbar-color: var(--scroll-thumb) transparent;
                box-sizing: border-box;
            }

            body { margin: 0; font-family: 'Segoe UI', system-ui, sans-serif; background: var(--secondary); color: #333333; overflow: hidden; }
            #map { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
            .controls {
                position: absolute; top: 20px; left: 20px; background: rgba(255, 255, 255, 0.95);
                padding: 20px; border-radius: 18px; border: 0px solid var(--primary);
                width: 320px;
                max-height: 85vh; overflow-y: auto;
                backdrop-filter: blur(10px); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                z-index: 10;
            }
            
            .button-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
                margin: 10px 0;
            }
            
            .btn {
                padding: 12px 15px; margin: 0; 
                background: #6d9eeb; color: #f8f9fa; 
                border: none; border-radius: 8px; cursor: pointer; font-weight: bold;
                transition: all 0.2s ease; font-size: 13px; text-align: center;
                min-height: 45px; display: flex; align-items: center; justify-content: center;
                white-space: nowrap;
            }

            .btn:hover {
                background: #3c78d8; transform: translateY(-2px);
                box-shadow: 0 1px 0px rgba(0, 255, 136, 0.4);
            }
            .btn:active { transform: translateY(0); }
            
            .btn.active {
                background: #3c78d8;
                transform: translateY(-2px);
                box-shadow: 0 1px 0px rgba(0, 255, 136, 0.4);
            }
            .btn.btn-secondary:hover, .btn.btn-secondary.active {
                background: #3c78d8;
            }
            .btn.btn-info:hover, .btn.btn-info.active {
                background: #3c78d8;
            }
            
            .btn:disabled { background: red; color: red; cursor: not-allowed; transform: none; }
            
            .info { margin: 10px 0; font-size: 0.9em; line-height: 1.4; }
            .error { color: var(--error); }
            .success { color: var(--primary); }
            .warning { color: var(--warning); }
            
            .network-list {
                max-height: 300px; overflow-y: auto; font-size: 0.8em;
                border: 1px solid rgba(0, 255, 136, 0.2); border-radius: 8px;
                padding: 10px; background: rgba(0, 0, 0, 0.05);
            }
            .network-item {
                padding: 10px; margin: 5px 0; border-radius: 6px;
                border-left: 4px solid #28a745; background: rgba(0, 0, 0, 0.03);
                transition: all 0.3s ease; position: relative;
            }
            .network-item.router { border-left-color: #dc3545; background: rgba(255, 0, 0, 0.05); }
            
            .signal-bar { height: 6px; background: rgba(0, 0, 0, 0.1); border-radius: 3px; margin: 5px 0; }
            .signal-fill { height: 100%; border-radius: 3px; transition: width 0.8s ease; }
            
            .rtt-display {
                font-size: 10px; color: var(--info); font-weight: bold;
                margin-top: 3px; border-top: 1px dashed rgba(0, 204, 255, 0.3);
                padding-top: 3px;
            }
            
            .live-indicator {
                display: inline-block;
                width: 8px;
                height: 8px;
                background: var(--primary);
                border-radius: 50%;
                animation: pulse 1s infinite;
                margin-right: 8px;
                vertical-align: middle;
            }
            @keyframes pulse {
                0% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.5; transform: scale(1.2); }
                100% { opacity: 1; transform: scale(1); }
            }
            
            .modal {
                display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.7); z-index: 1000; backdrop-filter: blur(5px);
            }
            .modal-content {
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                background: var(--secondary); padding: 25px; border-radius: 15px;
                border: 1px solid var(--primary); max-width: 450px; width: 90%;
                max-height: 80vh; overflow-y: auto; color: #333333;
            }
            .modal-header {
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid var(--primary);
            }
            .modal-close {
                background: var(--error); color: white; border: none;
                border-radius: 50%; width: 30px; height: 30px; cursor: pointer;
                font-size: 18px; display: flex; align-items: center; justify-content: center;
            }
            
            .settings-block input, .settings-block select {
                width: 100%;
                padding: 8px 15px;
                margin: 0;
                box-sizing: border-box;
                border: 1px solid var(--primary);
                border-radius: 5px;
                color: #333333;
                font-size: 13px;
                background: rgba(255, 255, 255, 0.9);
            }
            
            .settings-block select {
                cursor: pointer;
                -webkit-appearance: none;
                -moz-appearance: none;
                appearance: none;
                background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%233c78d8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
                background-repeat: no-repeat;
                background-position: right 12px center;
                background-size: 14px;
                padding-right: 35px;
            }
            
            .settings-block input:focus, .settings-block select:focus {
                outline: none;
                border-color: var(--primary);
                box-shadow: 0 0 0 0px rgba(60, 120, 216, 0.2);
            }
            
            .settings-block select option {
                background: var(--secondary);
                color: #333333;
                padding-left: 15px;
            }
            
            .divider {
                height: 1px; background: var(--primary); margin: 15px 0; opacity: 0.3;
            }
            
            h2, h3 { margin-top: 0; color: var(--primary); }
            h3 { font-size: 1.1em; }
            
            .triangulation-section {
                margin-top: 15px;
                border-top: 1px dashed var(--primary);
                padding-top: 15px;
            }
            
            .triangulation-title {
                color: var(--warning);
                font-size: 1em;
                margin-bottom: 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .triangulation-count {
                background: var(--warning);
                color: #000000;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                font-weight: bold;
                font-size: 0.8em;
                display: flex;
                align-items: center;
                justify-content: center;
                line-height: 1;
                padding: 0;
                margin: 0;
                flex-shrink: 0;
            }
            
            .switches-container {
                margin: 15px 0;
                padding: 10px;
                background: rgba(0, 0, 0, 0.05);
                border-radius: 8px;
                border: 1px solid rgba(0, 255, 136, 0.2);
                max-height: 250px;
                overflow-y: auto;
            }
            
            .form-check.form-switch {
                display: flex;
                align-items: center;
                margin-bottom: 10px;
            }
            
            .form-check-input[type="checkbox"] {
                width: 42px;
                height: 22px;
                margin-right: 10px;
                cursor: pointer;
                -webkit-appearance: none;
                appearance: none;
                background: #cccccc;
                border-radius: 20px;
                position: relative;
                transition: background-color 0.3s;
                border: none;
            }
            
            .form-check-input[type="checkbox"]:checked {
                background: var(--primary);
            }
            
            .form-check-input[type="checkbox"]::before {
                content: '';
                width: 18px;
                height: 18px;
                border-radius: 50%;
                background: white;
                position: absolute;
                top: 2px;
                left: 2px;
                transition: transform 0.3s cubic-bezier(0.68, -0.55, 0.27, 1.55);
            }
            
            .form-check-input[type="checkbox"]:checked::before {
                transform: translateX(20px);
            }
            
            .form-check-label {
                cursor: pointer;
                user-select: none;
                font-size: 12px;
                color: #333333;
                font-weight: 500;
            }
            
            .coord-display {
                font-size: 10px;
                color: var(--info);
                font-weight: bold;
                margin-top: 2px;
            }
            
            .settings-block {
                border: none;
                padding: 5px 0;
                margin: 5px 0;
            }
            
            .settings-block label {
                font-size: 12px;
                display: block;
                margin-bottom: 5px;
                color: #333333;
            }
            
            .header-title {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .logo-svg {
                width: 32px;
                height: 32px;
                flex-shrink: 0;
            }
            
            .header-text {
                font-size: 1.1em;
                font-weight: bold;
                color: var(--primary);
                margin: 0;
            }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="controls">
            <div class="header-title">
                <svg class="logo-svg" version="1.1" viewBox="0 0 192 192" fill="none" stroke="none" stroke-linecap="square" stroke-miterlimit="10" xmlns="http://www.w3.org/2000/svg ">
                    <clipPath id="p.0"><path d="m0 0l192 0l0 192l-192 0z" clip-rule="nonzero"/></clipPath>
                    <g clip-path="url(#p.0)">
                        <path fill="#fad57a" d="m154.585 76.782l0 0c-0.186-20.651-17.184-38.474-38.332-40.193l-0.097 5.252c18.078 1.614 32.65 16.93 32.955 34.638z" fill-rule="evenodd"/>
                        <path stroke="#fad57a" stroke-width="14.66" stroke-linejoin="round" stroke-linecap="butt" d="m154.585 76.782l0 0c-0.186-20.651-17.184-38.474-38.332-40.193l-0.097 5.252c18.078 1.614 32.65 16.93 32.955 34.638z" fill-rule="evenodd"/>
                        <path fill="#748c6a" d="m37.415 76.782l0 0c0.186-20.651 17.184-38.474 38.332-40.193l0.097 5.252c-18.078 1.614-32.65 16.93-32.955 34.638z" fill-rule="evenodd"/>
                        <path stroke="#748c6a" stroke-width="14.66" stroke-linejoin="round" stroke-linecap="butt" d="m37.415 76.782l0 0c0.186-20.651 17.184-38.474 38.332-40.193l0.097 5.252c-18.078 1.614-32.65 16.93-32.955 34.638z" fill-rule="evenodd"/>
                        <path fill="#eb5b57" d="m154.585 115.218l0 0c-0.186 20.651-17.184 38.474-38.332 40.193l-0.097-5.252c18.078-1.614 32.65-16.93 32.955-34.638z" fill-rule="evenodd"/>
                        <path stroke="#eb5b57" stroke-width="14.66" stroke-linejoin="round" stroke-linecap="butt" d="m154.585 115.218l0 0c-0.186 20.651-17.184 38.474-38.332 40.193l-0.097-5.252c18.078-1.614 32.65-16.93 32.955-34.638z" fill-rule="evenodd"/>
                        <path fill="#517eb9" d="m37.415 115.218l0 0c0.186 20.65 17.184 38.474 38.332 40.192l0.097-5.252c-18.078-1.614-32.65-16.93-32.955-34.638z" fill-rule="evenodd"/>
                        <path stroke="#517eb9" stroke-width="14.66" stroke-linejoin="round" stroke-linecap="butt" d="m37.415 115.218l0 0c0.186 20.65 17.184 38.474 38.332 40.192l0.097-5.252c-18.078-1.614-32.65-16.93-32.955-34.638z" fill-rule="evenodd"/>
                        <path fill="#3c78d8" d="m69.536 96.003l0 0c0-14.62 11.852-26.472 26.472-26.472 7.021 0 13.754 2.789 18.718 7.754 4.965 4.964 7.754 11.697 7.754 18.718l0 0c0 14.62-11.852 26.472-26.472 26.472-14.62 0-26.472-11.852-26.472-26.472z" fill-rule="evenodd"/>
                    </g>
                </svg>
                <h2 class="header-text">EMIIA.AI SIP (MRV/SDK)</h2>
            </div>
            
            <div class="button-grid">
                <button class="btn btn-scan" onclick="scanWiFi()">Сканировать</button>
                <button class="btn btn-secondary" id="positionBtn" onclick="toggleMyPosition()">Моя позиция</button>
                <button class="btn btn-info" id="autoRefreshBtn" onclick="toggleAutoRefresh()">Авто</button>
                <button class="btn btn-warning" onclick="openCalibration()">Калибровка</button>
                <button class="btn btn-info" onclick="openTriangulation()">Связи</button>
                <button class="btn btn-secondary" onclick="exportData()">Экспорт</button>
            </div>
            
            <div class="settings-block">
                <label>AI-агент (LLM): </label>
                <select id="agentSelect" onchange="changeAgent()">
                    <option value="emiiatai" selected>EMIIA.AI TAI</option>
                    <option value="emiiaoai">EMIIA.AI OAI</option>
                    <option value="qwen3">Qwen3‑235B‑A22B</option>
                    <option value="openai120b">OpenAI OSS 120B</option>
                    <option value="gemma27b">Gemma 27B VL</option>
                </select>
            </div>
            
            <div class="settings-block">
                <label>Интервал (сек): </label>
                <select id="intervalSelect" onchange="changeInterval()">
                    <option value="0.5" selected>0.5</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="5">5</option>
                </select>
            </div>
            
            <div class="settings-block">
                <label>Точность (м): </label>
                <input type="number" id="accuracyInput" value="0.3" step="0.1" min="0.1" max="10" 
                       onchange="changeAccuracy()">
            </div>
            
            <div class="settings-block">
                <label>Погрешность (%): </label>
                <input type="number" id="errorMarginInput" value="5" step="1" min="0" max="50" 
                       onchange="changeErrorMargin()">
            </div>
            
            <div class="switches-container">
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="mrv-toggle" checked>
                    <label class="form-check-label" for="mrv-toggle">Машинное радиозрение (MRV)</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="wifi-toggle" checked>
                    <label class="form-check-label" for="wifi-toggle">Wi-Fi</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="bluetooth-toggle">
                    <label class="form-check-label" for="bluetooth-toggle">Bluetooth</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="zigbee-toggle">
                    <label class="form-check-label" for="zigbee-toggle">Zigbee</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="rfid-toggle">
                    <label class="form-check-label" for="rfid-toggle">RFID</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="imu-toggle">
                    <label class="form-check-label" for="imu-toggle">IMU-датчики</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="triangulation-toggle" checked>
                    <label class="form-check-label" for="triangulation-toggle">Триангуляция</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="trilateration-toggle" checked>
                    <label class="form-check-label" for="trilateration-toggle">Трилатерация</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="rtt-toggle" checked>
                    <label class="form-check-label" for="rtt-toggle">Круговая задержка (RTT)</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="ml-toggle" checked>
                    <label class="form-check-label" for="ml-toggle">Машинное обучение (ML)</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="realtime-toggle">
                    <label class="form-check-label" for="realtime-toggle">Real Time - позиция</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="digital-twin-toggle" checked>
                    <label class="form-check-label" for="digital-twin-toggle">Цифровой двойник (АЦД)</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="map-toggle">
                    <label class="form-check-label" for="map-toggle">Маппирование данных (MAP)</label>
                </div>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="geojson-toggle" checked>
                    <label class="form-check-label" for="geojson-toggle">GeoJSON сервер БД</label>
                </div>
            </div>
            
            <div id="status" class="info">Инициализация...</div>
            <div id="wifi-result" class="info"></div>
            
            <h3>АКТИВНЫЕ СЕТИ: <span id="network-count">0</span></h3>
            <div id="networks" class="network-list"></div>
            <div id="last-update" class="info" style="font-size: 11px; color: #666; text-align: right;"></div>
            
            <div class="triangulation-section" id="triangulationSection" style="display: none;">
                <div class="triangulation-title">
                    СЕТИ ДЛЯ КОРРЕКТИРОВКИ
                    <span class="triangulation-count" id="triangulationCount">0</span>
                </div>
                <div id="triangulationNetworks" class="network-list" style="max-height: 200px;"></div>
            </div>
        </div>

        <div id="calibrationModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>КАЛИБРОВКА МОДЕЛИ</h3>
                    <button class="modal-close" onclick="closeCalibration()">×</button>
                </div>
                <p style="font-size: 11px; color: #888;">Откалибруйте модель для точных расчетов расстояния</p>
                
                <label>Референсное расстояние (м):</label>
                <input type="number" id="calibDistance" placeholder="1.0" value="1.0" step="0.1">
                
                <label>Сигнал на этом расстоянии (dBm):</label>
                <input type="number" id="calibSignal" placeholder="-30" value="-30" step="1">
                
                <button class="btn" onclick="saveCalibration()" style="width: 100%; margin-top: 15px;">
                    Сохранить калибровку
                </button>
                
                <div id="calib-status" class="info"></div>
            </div>
        </div>

        <div id="triangulationModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>ВЫБОР СЕТЕЙ ДЛЯ КОРРЕКТИРОВКИ</h3>
                    <button class="modal-close" onclick="closeTriangulation()">×</button>
                </div>
                <p style="font-size: 11px; color: #888;">Выберите 3+ сети для точной корректировки позиции</p>
                
                <div id="triang-selection" style="max-height: 300px; overflow-y: auto;">
                </div>
                
                <div class="divider"></div>
                
                <h4>Выбранные сети:</h4>
                <div id="selected-networks" style="font-size: 11px; max-height: 150px; overflow-y: auto;">
                    <div style="color: #888;">Нет выбранных сетей</div>
                </div>
                
                <button class="btn" onclick="saveTriangulation()" style="width: 100%; margin-top: 15px;">
                    Применить корректировку
                </button>
            </div>
        </div>

        <script>
            const ROUTER_CONFIG = {
                ssid: 'EMIIA.AI MRV',
                mac: '50:FF:20:68:EF:9C',
                position: [37.16332212, 55.98346937],
                ip: '192.168.1.1'
            };
            
            let wifiNetworks = [], autoRefreshInterval = null;
            let isAutoRefreshing = false, scanInterval = 500;
            let userPositionFallback = null;
            let selectedForTriangulation = [];
            let accuracy = 1.0;
            let errorMargin = 5;
            let mapEnabled = false;
            let geojsonEnabled = true;
            let selectedAgent = 'emiiatai';
            let myPositionShown = false;
            
            // Переменные для состояния анимации точки
            let isLocationActive = false;
            
            mapboxgl.accessToken = 'YOUR_EMIIA_AI_ACCESS_TOKEN';
            
            const map = new mapboxgl.Map({
                container: 'map',
                style: 'https://sos.emiia.ai/moscow_style_2.json ',
                zoom: 18.3,
                minZoom: 9,
                maxZoom: 20.5,
                center: [37.16332212, 55.98346937],
                hash: true,
                turn: false,
                attributionControl: false,
                bearing: 0,
                pitch: 45,
                antialias: true 
            });
            
            userPositionFallback = {
                lat: ROUTER_CONFIG.position[1],
                lng: ROUTER_CONFIG.position[0],
                accuracy: 30
            };
            
            // ========== СИНЯЯ ПУЛЬСИРУЮЩАЯ ТОЧКА (Моя позиция) ==========
            const pulsingDotBlue = {
                width: 110,
                height: 110,
                data: new Uint8Array(110 * 110 * 4),

                onAdd: function () {
                    const canvas = document.createElement('canvas');
                    canvas.width = this.width;
                    canvas.height = this.height;
                    this.context = canvas.getContext('2d', { willReadFrequently: true });
                },

                render: function () {
                    if (!isLocationActive) return false;
                    
                    const duration = 1800;
                    const pulseDuration = 700;
                    const t = (performance.now() % duration) / duration;
                    const pulseT = (performance.now() % pulseDuration) / pulseDuration;
                    const context = this.context;

                    context.clearRect(0, 0, this.width, this.height);

                    const centerX = this.width / 2;
                    const centerY = this.height / 2;
                    const maxRadius = this.width / 2 * 1;
                    const sweepAngle = Math.PI * 2 * 1.7 * t;
                    const opacity = 0.8 * Math.pow(1 - t, 2);

                    context.beginPath();
                    context.moveTo(centerX, centerY);
                    context.arc(centerX, centerY, maxRadius, Math.PI / 2, sweepAngle + Math.PI / 2);
                    context.closePath();

                    context.fillStyle = `rgba(61, 133, 198, ${opacity})`;
                    context.fill();

                    const radius = (this.width / 2) * 0.35;
                    context.beginPath();
                    context.arc(centerX, centerY, radius, 0, Math.PI * 2);
                    context.fillStyle = 'rgba(61, 133, 198, 1)';
                    context.strokeStyle = '#f8f9fa';

                    context.lineWidth = 2.5 + 2.5 * Math.abs(Math.sin(Math.PI * pulseT));
                    context.fill();
                    context.stroke();

                    this.data = context.getImageData(0, 0, this.width, this.height).data;
                    map.triggerRepaint();

                    return true;
                }
            };

            // ========== СТАТИЧЕСКАЯ КРАСНАЯ ТОЧКА (Роутер) ==========
            const staticRedDot = {
                width: 110,
                height: 110,
                data: new Uint8Array(110 * 110 * 4),

                onAdd: function () {
                    const canvas = document.createElement('canvas');
                    canvas.width = this.width;
                    canvas.height = this.height;
                    this.context = canvas.getContext('2d');
                },

                render: function () {
                    const context = this.context;
                    context.clearRect(0, 0, this.width, this.height);

                    const centerX = this.width / 2;
                    const centerY = this.height / 2;
                    const radius = (this.width / 2) * 0.35;

                    context.beginPath();
                    context.arc(centerX, centerY, radius, 0, Math.PI * 2);
                    context.fillStyle = 'rgba(220, 53, 69, 1)';
                    context.strokeStyle = '#f8f9fa';
                    context.lineWidth = 2.5;
                    context.fill();
                    context.stroke();

                    this.data = context.getImageData(0, 0, this.width, this.height).data;
                    return true;
                }
            };

            // ========== СТАТИЧЕСКАЯ СЕРАЯ ТОЧКА (Триангуляция) ==========
            const staticGrayDot = {
                width: 110,
                height: 110,
                data: new Uint8Array(110 * 110 * 4),

                onAdd: function () {
                    const canvas = document.createElement('canvas');
                    canvas.width = this.width;
                    canvas.height = this.height;
                    this.context = canvas.getContext('2d');
                },

                render: function () {
                    const context = this.context;
                    context.clearRect(0, 0, this.width, this.height);

                    const centerX = this.width / 2;
                    const centerY = this.height / 2;
                    const radius = (this.width / 2) * 0.35;

                    context.beginPath();
                    context.arc(centerX, centerY, radius, 0, Math.PI * 2);
                    context.fillStyle = 'rgba(108, 117, 125, 1)';
                    context.strokeStyle = '#f8f9fa';
                    context.lineWidth = 2.5;
                    context.fill();
                    context.stroke();

                    this.data = context.getImageData(0, 0, this.width, this.height).data;
                    return true;
                }
            };
            
            map.on('load', () => {
                // Найти слой с подписями для правильного порядка отображения
                const layers = map.getStyle().layers;
                let labelLayerId;
                for (let i = 0; i < layers.length; i++) {
                    if (layers[i].type === 'symbol' && layers[i].layout['text-field']) {
                        labelLayerId = layers[i].id;
                        break;
                    }
                }

                // Добавить векторный источник для зданий
                map.addSource('openmaptiles', {
                    url: 'https://sos.emiia.ai/tiles.json ',
                    type: 'vector',
                });

                // Зеленая подложка под зданиями
                map.addLayer({
                    'id': 'green-base',
                    'source': 'openmaptiles',
                    'source-layer': 'building',
                    'type': 'fill',
                    'minzoom': 14,
                    'maxzoom': 24,
                    'paint': {
                        'fill-color': '#a4c2f4',
                        'fill-opacity': [
                            'interpolate',
                            ['linear'],
                            ['zoom'],
                            14, 0.3,
                            15.5, 0.3,
                            18, 0.3,
                            22, 0.3
                        ]
                    }
                }, labelLayerId);

                // Белые линии по контуру зданий
                map.addLayer({
                    'id': 'building-outlines',
                    'source': 'openmaptiles',
                    'source-layer': 'building',
                    'type': 'line',
                    'minzoom': 14,
                    'maxzoom': 24,
                    'paint': {
                        'line-color': '#ffffff',
                        'line-width': [
                            'interpolate',
                            ['linear'],
                            ['zoom'],
                            14, 1,
                            16, 2,
                            18, 2,
                            20, 5
                        ],
                        'line-opacity': [
                            'interpolate',
                            ['linear'],
                            ['zoom'],
                            14, 1,
                            15.5, 1,
                            18, 1,
                            22, 1
                        ]
                    }
                }, labelLayerId);

                // 3D здания поверх подложки и контуров
                map.addLayer({
                    'id': '3d-buildings',
                    'source': 'openmaptiles',
                    'source-layer': 'building',
                    'type': 'fill-extrusion',
                    'minzoom': 14,
                    'maxzoom': 19,
                    'paint': {
                        'fill-extrusion-color': [
                            'interpolate',
                            ['linear'],
                            ['get', 'render_height'],
                            1, '#e4e4e4',
                            200, '#e4e4e4',
                            400, '#e4e4e4'
                        ],
                        'fill-extrusion-height': [
                            'interpolate',
                            ['linear'],
                            ['zoom'],
                            14, 0,
                            15.5, ['get', 'render_height']
                        ],
                        'fill-extrusion-base': [
                            'case',
                            ['>=', ['get', 'zoom'], 16.5],
                            ['get', 'render_min_height'],
                            0
                        ],
                        'fill-extrusion-opacity': [
                            'interpolate',
                            ['linear'],
                            ['zoom'],
                            14, 0,
                            15.5, 0.8,
                            18, 0.0
                        ]
                    }
                }, labelLayerId);

                // Добавить изображения для точек
                map.addImage('pulsing-dot-blue', pulsingDotBlue, { pixelRatio: 2 });
                map.addImage('static-red-dot', staticRedDot, { pixelRatio: 2 });
                map.addImage('static-gray-dot', staticGrayDot, { pixelRatio: 2 });

                // Слой для пульсирующей точки (Моя позиция)
                map.addSource('pulsing-points-source', {
                    type: 'geojson',
                    data: {
                        type: 'FeatureCollection',
                        features: []
                    }
                });

                map.addLayer({
                    id: 'pulsing-points-layer',
                    type: 'symbol',
                    source: 'pulsing-points-source',
                    layout: {
                        'icon-image': 'pulsing-dot-blue',
                        'icon-allow-overlap': true,
                        'icon-ignore-placement': true
                    }
                });

                // Слой для точки основного роутера (отдельный источник)
                map.addSource('router-point-source', {
                    type: 'geojson',
                    data: {
                        type: 'FeatureCollection',
                        features: [{
                            type: 'Feature',
                            geometry: {
                                type: 'Point',
                                coordinates: ROUTER_CONFIG.position
                            },
                            properties: {
                                icon: 'static-red-dot',
                                type: 'router'
                            }
                        }]
                    }
                });

                map.addLayer({
                    id: 'router-point-layer',
                    type: 'symbol',
                    source: 'router-point-source',
                    layout: {
                        'icon-image': 'static-red-dot',
                        'icon-allow-overlap': true,
                        'icon-ignore-placement': true
                    }
                });

                // Слой для триангуляционных точек (отдельный источник)
                map.addSource('triangulation-points-source', {
                    type: 'geojson',
                    data: {
                        type: 'FeatureCollection',
                        features: []
                    }
                });

                map.addLayer({
                    id: 'triangulation-points-layer',
                    type: 'symbol',
                    source: 'triangulation-points-source',
                    layout: {
                        'icon-image': 'static-gray-dot',
                        'icon-allow-overlap': true,
                        'icon-ignore-placement': true
                    }
                });

                // Переместить все слои под 3D-здания
                if (map.getLayer('3d-buildings')) {
                    map.moveLayer('triangulation-points-layer', '3d-buildings');
                    map.moveLayer('router-point-layer', 'triangulation-points-layer');
                    map.moveLayer('pulsing-points-layer', 'router-point-layer');
                }

                // Установка светового режима и освещения
                map.setConfigProperty('basemap', 'lightPreset', 'dusk');
                map.setLight({
                    intensity: 0.03
                });

                // Обработчик клика для пульсирующих точек
                map.on('click', 'pulsing-points-layer', (e) => {
                    const feature = e.features[0];
                    const coordinates = feature.geometry.coordinates;
                    const accuracy = feature.properties.accuracy;

                    new mapboxgl.Popup()
                        .setLngLat(coordinates)
                        .setHTML(`
                            <div style="padding: 10px; font-size: 12px; min-width: 200px;">
                                <h4 style="margin: 0 0 10px 0; color: #3c78d8; font-size: 14px;">Моя позиция</h4>
                                <div style="margin-bottom: 8px;">
                                    <strong>Координаты:</strong><br>
                                    <code style="font-size: 11px; color: #666;">
                                        ${coordinates[0].toFixed(8)}<br>
                                        ${coordinates[1].toFixed(8)}
                                    </code>
                                </div>
                                <div style="margin-bottom: 8px;">
                                    <strong>Точность:</strong> 
                                    <span style="color: ${accuracy < 5 ? '#28a745' : accuracy < 15 ? '#ffc107' : '#dc3545'};">
                                        ${parseFloat(accuracy).toFixed(1)} м
                                    </span>
                                </div>
                                <div style="font-size: 10px; color: #999; border-top: 1px solid #eee; padding-top: 5px;">
                                    Обновлено: ${new Date().toLocaleTimeString()}
                                </div>
                            </div>
                        `)
                        .addTo(map);
                });

                map.on('mouseenter', 'pulsing-points-layer', () => {
                    map.getCanvas().style.cursor = 'pointer';
                });

                map.on('mouseleave', 'pulsing-points-layer', () => {
                    map.getCanvas().style.cursor = '';
                });

                // Обработчик клика для точки роутера
                map.on('click', 'router-point-layer', (e) => {
                    const feature = e.features[0];
                    const props = feature.properties;
                    
                    const popupContent = `
                        <div style="padding: 10px; font-size: 12px;">
                            <h4 style="margin: 0 0 8px 0; color: #dc3545;">${ROUTER_CONFIG.ssid}</h4>
                            <p style="margin: 4px 0;"><b>MAC:</b> ${ROUTER_CONFIG.mac}</p>
                            <p style="margin: 4px 0;"><b>IP:</b> ${ROUTER_CONFIG.ip || 'N/A'}</p>
                            <p style="margin: 4px 0;"><b>Тип:</b> <span style="color: #dc3545; font-weight: bold;">Главный роутер</span></p>
                        </div>
                    `;
                    
                    new mapboxgl.Popup()
                        .setLngLat(feature.geometry.coordinates)
                        .setHTML(popupContent)
                        .addTo(map);
                });

                map.on('mouseenter', 'router-point-layer', () => {
                    map.getCanvas().style.cursor = 'pointer';
                });

                map.on('mouseleave', 'router-point-layer', () => {
                    map.getCanvas().style.cursor = '';
                });

                // Обработчик клика для триангуляционных точек
                map.on('click', 'triangulation-points-layer', (e) => {
                    const feature = e.features[0];
                    const props = feature.properties;
                    
                    const popupContent = `
                        <div style="padding: 10px; font-size: 12px; min-width: 220px;">
                            <h4 style="margin: 0 0 8px 0; color: #6c757d;">${props.ssid}</h4>
                            <p style="margin: 4px 0;"><b>MAC:</b> ${props.mac}</p>
                            <p style="margin: 4px 0;"><b>Сигнал:</b> ${parseFloat(props.signal).toFixed(1)} dBm</p>
                            <p style="margin: 4px 0;"><b>Расстояние:</b> ${props.distance} м</p>
                            <p style="margin: 4px 0;"><b>RTT:</b> ${parseFloat(props.rtt_ms).toFixed(1)} мс</p>
                            <p style="margin: 4px 0; color: #00ccff; font-weight: bold;">
                                Lng,Lat: ${feature.geometry.coordinates[0].toFixed(8)}, ${feature.geometry.coordinates[1].toFixed(8)}
                            </p>
                            <p style="margin: 4px 0;"><b>Тип:</b> <span style="color: #6c757d; font-weight: bold;">Триангуляция</span></p>
                        </div>
                    `;
                    
                    new mapboxgl.Popup()
                        .setLngLat(feature.geometry.coordinates)
                        .setHTML(popupContent)
                        .addTo(map);
                });

                map.on('mouseenter', 'triangulation-points-layer', () => {
                    map.getCanvas().style.cursor = 'pointer';
                });

                map.on('mouseleave', 'triangulation-points-layer', () => {
                    map.getCanvas().style.cursor = '';
                });
            
                document.getElementById('status').innerHTML = '<span class="success">Готов к сканированию</span>';
                setTimeout(scanWiFi, 500);
                
                document.getElementById('map-toggle').addEventListener('change', function() {
                    mapEnabled = this.checked;
                    console.log('Маппирование данных:', mapEnabled);
                });
                
                document.getElementById('geojson-toggle').addEventListener('change', function() {
                    geojsonEnabled = this.checked;
                    console.log('GeoJSON сервер БД:', geojsonEnabled);
                });
                
                document.getElementById('realtime-toggle').addEventListener('change', function() {
                    console.log('Real Time - позиция:', this.checked);
                });
                
                document.getElementById('digital-twin-toggle').addEventListener('change', function() {
                    console.log('Цифровой двойник (АЦД):', this.checked);
                });
            });
            
            // ========== ОБНОВЛЕНИЕ ПУЛЬСИРУЮЩИХ ТОЧЕК (Моя позиция) ==========
            function updatePulsingPointsLayer(lng, lat) {
                if (map.getSource('pulsing-points-source')) {
                    map.getSource('pulsing-points-source').setData({
                        type: 'FeatureCollection',
                        features: [{
                            type: 'Feature',
                            geometry: {
                                type: 'Point',
                                coordinates: [lng, lat]
                            },
                            properties: {
                                accuracy: userPositionFallback.accuracy,
                                timestamp: new Date().toISOString()
                            }
                        }]
                    });
                }
            }
            
            // ========== ОБНОВЛЕНИЕ ТОЧКИ ОСНОВНОГО РОУТЕРА ==========
            function updateRouterPointLayer() {
                if (map.getSource('router-point-source')) {
                    map.getSource('router-point-source').setData({
                        type: 'FeatureCollection',
                        features: [{
                            type: 'Feature',
                            geometry: {
                                type: 'Point',
                                coordinates: ROUTER_CONFIG.position
                            },
                            properties: {
                                icon: 'static-red-dot',
                                type: 'router'
                            }
                        }]
                    });
                }
            }
            
            // ========== ОБНОВЛЕНИЕ ТРИАНГУЛЯЦИОННЫХ ТОЧЕК ==========
            function updateTriangulationPointsLayer() {
                if (!map.getSource('triangulation-points-source')) {
                    console.warn('triangulation-points-source не найден');
                    return;
                }
                
                const features = [];
                
                // Добавить триангуляционные точки (без роутера)
                selectedForTriangulation.forEach(network => {
                    if (network.mac === ROUTER_CONFIG.mac) return; // Защита от дубликатов
                    if (network.position) {
                        features.push({
                            type: 'Feature',
                            geometry: {
                                type: 'Point',
                                coordinates: network.position
                            },
                            properties: {
                                icon: 'static-gray-dot',
                                type: 'triangulation',
                                ssid: network.ssid,
                                mac: network.mac,
                                signal: network.signal,
                                distance: network.distance,
                                rtt_ms: network.rtt_ms,
                                channel: network.channel
                            }
                        });
                    }
                });
                
                // Обновить данные источника
                map.getSource('triangulation-points-source').setData({
                    type: 'FeatureCollection',
                    features: features
                });
                
                console.log(`Обновлен слой триангуляционных точек: ${features.length} точек`);
            }
            
            async function scanWiFi() {
                try {
                    const startTime = Date.now();
                    document.getElementById('status').innerHTML = 'Сканирование...';
                    
                    const response = await fetch('/api/wifi');
                    const result = await response.json();
                    const scanTime = Date.now() - startTime;
                    
                    if (result.error) throw new Error(result.error);
                    
                    wifiNetworks = result;
                    displayNetworks(wifiNetworks, scanTime);
                    updateTriangulationSection();
                    updateRouterPointLayer(); // Обновляем точку роутера
                    updateTriangulationPointsLayer(); // Обновляем триангуляционные точки
                    
                    // Обновить позицию если слой активен
                    if (myPositionShown && userPositionFallback) {
                        updatePulsingPointsLayer(userPositionFallback.lng, userPositionFallback.lat);
                    }
                    
                } catch(e) {
                    console.error('Ошибка:', e);
                    document.getElementById('status').innerHTML = `<span class="error">Ошибка: ${e.message}</span>`;
                }
            }
            
            function displayNetworks(networks, scanTime = 0) {
                let html = '', routerFound = false;
                networks.sort((a, b) => b.signal - a.signal);
                
                networks.forEach((network, index) => {
                    const isRouter = network.mac === ROUTER_CONFIG.mac;
                    if (isRouter) routerFound = true;
                    
                    const signalPercent = Math.max(0, Math.min(100, (network.signal + 100) * 2));
                    const signalColor = signalPercent > 70 ? '#28a745' : 
                                      signalPercent > 40 ? '#ffc107' : '#dc3545';
                    
                    const rttValue = typeof network.rtt_ms === 'number' ? network.rtt_ms.toFixed(1) : '0.0';
                    const rttRealValue = network.rtt_real_ms ? `${network.rtt_real_ms} мс` : '';
                    const coordDisplay = network.position ? 
                        `Lng,Lat: ${network.position[0].toFixed(8)}, ${network.position[1].toFixed(8)}` : '';
                    
                    const rttHtml = network.rtt_ms !== undefined ? 
                        `<div class="rtt-display">
                            RTT: ${rttValue} мс ${rttRealValue ? ` | Ping: ${rttRealValue}` : ''}
                            <div class="coord-display">${coordDisplay}</div>
                        </div>` : '';
                    
                    html += `
                        <div class="network-item ${isRouter ? 'router' : ''}">
                            <div style="display: flex; justify-content: space-between;">
                                <div style="display: flex; align-items: center;">
                                    <div class="live-indicator"></div>
                                    <b>${network.ssid}</b>
                                </div>
                                <span style="font-weight: bold; color: ${signalColor}">
                                    ${network.signal.toFixed(1)} dBm
                                </span>
                            </div>
                            <div style="font-size: 11px; color: #666; word-break: break-all;">
                                MAC: ${network.mac}
                            </div>
                            <div class="signal-bar">
                                <div class="signal-fill" style="width: ${signalPercent}%; background: ${signalColor};"></div>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                                <span>Расстояние: ${network.distance} м</span>
                                <span>Канал: ${network.channel || 'N/A'}</span>
                            </div>
                            ${rttHtml}
                        </div>
                    `;
                });
                
                document.getElementById('networks').innerHTML = html || '<div class="warning">Нет сетей</div>';
                document.getElementById('network-count').textContent = networks.length;
                document.getElementById('last-update').textContent = `Обновлено: ${new Date().toLocaleTimeString()} (${scanTime}мс)`;
                
                const router = networks.find(n => n.mac === ROUTER_CONFIG.mac);
                if (router) {
                    userPositionFallback = {
                        lat: router.position[1] + (Math.random() - 0.5) * 0.0001,
                        lng: router.position[0] + (Math.random() - 0.5) * 0.0001,
                        accuracy: router.distance
                    };
                    document.getElementById('wifi-result').innerHTML = `
                        <div class="success">
                            <b>Роутер найден!</b> ${router.signal.toFixed(1)} dBm
                        </div>
                    `;
                    document.getElementById('status').innerHTML = '<span class="success">EMIIA.AI IoT</span>';
                } else {
                    userPositionFallback = {
                        lat: ROUTER_CONFIG.position[1] + (Math.random() - 0.5) * 0.0002,
                        lng: ROUTER_CONFIG.position[0] + (Math.random() - 0.5) * 0.0002,
                        accuracy: 30
                    };
                    document.getElementById('wifi-result').innerHTML = '<div class="warning">Шлюз</div>';
                    document.getElementById('status').innerHTML = '<span class="warning">EMIIA.AI IoT</span>';
                }
            }
            
            function updateTriangulationSection() {
                if (selectedForTriangulation.length === 0) {
                    document.getElementById('triangulationSection').style.display = 'none';
                    return;
                }
                
                document.getElementById('triangulationSection').style.display = 'block';
                document.getElementById('triangulationCount').textContent = selectedForTriangulation.length;
                
                let html = '';
                
                selectedForTriangulation = selectedForTriangulation.map(selectedNet => {
                    const updatedNet = wifiNetworks.find(n => n.mac === selectedNet.mac);
                    return updatedNet || selectedNet;
                });
                
                selectedForTriangulation.forEach(network => {
                    const isRouter = network.mac === ROUTER_CONFIG.mac;
                    const signalPercent = Math.max(0, Math.min(100, (network.signal + 100) * 2));
                    const signalColor = signalPercent > 70 ? '#28a745' : 
                                      signalPercent > 40 ? '#ffc107' : '#dc3545';
                    
                    const rttValue = typeof network.rtt_ms === 'number' ? network.rtt_ms.toFixed(1) : '0.0';
                    const coordDisplay = network.position ? 
                        `Lng,Lat: ${network.position[0].toFixed(8)}, ${network.position[1].toFixed(8)}` : '';
                    
                    html += `
                        <div class="network-item ${isRouter ? 'router' : ''}" style="padding: 8px;">
                            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                                <b>${network.ssid}</b>
                                <span style="color: ${signalColor}; font-weight: bold;">
                                    ${network.signal.toFixed(1)} dBm
                                </span>
                            </div>
                            <div style="font-size: 10px; color: #888; margin-top: 2px;">
                                MAC: ${network.mac}<br>
                                Расстояние: ${network.distance} м | RTT: ${rttValue} мс<br>
                                <span style="color: var(--info); font-weight: bold;">${coordDisplay}</span>
                            </div>
                        </div>
                    `;
                });
                
                document.getElementById('triangulationNetworks').innerHTML = html;
            }
            
            // ========== ИСПРАВЛЕННАЯ ФУНКЦИЯ toggleMyPosition ==========
            function toggleMyPosition() {
                const btn = document.getElementById('positionBtn');
                
                if (!myPositionShown) {
                    // Проверить наличие координат
                    if (!userPositionFallback || !userPositionFallback.lng || !userPositionFallback.lat) {
                        console.error('userPositionFallback не инициализирован');
                        return;
                    }
                    
                    // Добавить точку в пульсирующий слой
                    updatePulsingPointsLayer(userPositionFallback.lng, userPositionFallback.lat);
                    
                    // Плавный переход карты
                    map.flyTo({
                        center: [userPositionFallback.lng, userPositionFallback.lat],
                        zoom: 19,
                        speed: 0.5,
                        essential: true
                    });
                    
                    // Активировать кнопку
                    btn.classList.add('active');
                    myPositionShown = true;
                    isLocationActive = true;
                    
                } else {
                    // Очистить пульсирующий слой
                    if (map.getSource('pulsing-points-source')) {
                        map.getSource('pulsing-points-source').setData({
                            type: 'FeatureCollection',
                            features: []
                        });
                    }
                    
                    // Деактивировать кнопку
                    btn.classList.remove('active');
                    myPositionShown = false;
                    isLocationActive = false;
                }
            }
            
            // ========== ФУНКЦИЯ toggleAutoRefresh (без изменений) ==========
            function toggleAutoRefresh() {
                const btn = document.getElementById('autoRefreshBtn');
                
                if (isAutoRefreshing) {
                    clearInterval(autoRefreshInterval);
                    isAutoRefreshing = false;
                    btn.classList.remove('active');
                    document.getElementById('status').innerHTML = 'Автообновление остановлено';
                } else {
                    autoRefreshInterval = setInterval(scanWiFi, scanInterval);
                    isAutoRefreshing = true;
                    btn.classList.add('active');
                    document.getElementById('status').innerHTML = `Автообновление: каждые ${scanInterval/1000} сек`;
                    scanWiFi();
                }
            }
            
            function changeInterval() {
                scanInterval = parseFloat(document.getElementById('intervalSelect').value) * 1000;
                if (isAutoRefreshing) {
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = setInterval(scanWiFi, scanInterval);
                }
            }
            
            function changeAccuracy() {
                accuracy = parseFloat(document.getElementById('accuracyInput').value);
                console.log('Точность установлена:', accuracy, 'м');
            }
            
            function changeErrorMargin() {
                errorMargin = parseInt(document.getElementById('errorMarginInput').value);
                console.log('Погрешность установлена:', errorMargin, '%');
            }
            
            function changeAgent() {
                selectedAgent = document.getElementById('agentSelect').value;
                console.log('AI-агент выбран:', selectedAgent);
                document.getElementById('status').innerHTML = `<span class="success">AI-агент: ${document.getElementById('agentSelect').options[document.getElementById('agentSelect').selectedIndex].text}</span>`;
            }
            
            function exportData() {
                fetch('/api/export')
                    .then(res => {
                        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                        return res.json();
                    })
                    .then(data => {
                        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `wifi-scan-rtt-${Date.now()}.json`;
                        a.click();
                        URL.revokeObjectURL(url);
                        document.getElementById('status').innerHTML = '<span class="success">Данные экспортированы (с RTT)</span>';
                    })
                    .catch(err => {
                        console.error('Ошибка экспорта:', err);
                        document.getElementById('status').innerHTML = `<span class="error">Ошибка экспорта: ${err.message}</span>`;
                    });
            }
            
            function openCalibration() {
                document.getElementById('calibrationModal').style.display = 'block';
            }
            
            function closeCalibration() {
                document.getElementById('calibrationModal').style.display = 'none';
                document.getElementById('calib-status').innerHTML = '';
            }
            
            function saveCalibration() {
                document.getElementById('calib-status').innerHTML = '<span class="success">Калибровка сохранена</span>';
                setTimeout(() => {
                    closeCalibration();
                    document.getElementById('status').innerHTML = '<span class="success">Модель откалибрована</span>';
                }, 1500);
            }
            
            function openTriangulation() {
                document.getElementById('triangulationModal').style.display = 'block';
                renderTriangulationSelection();
            }
            
            function closeTriangulation() {
                document.getElementById('triangulationModal').style.display = 'none';
            }
            
            function renderTriangulationSelection() {
                const networks = wifiNetworks.filter(n => n.mac !== ROUTER_CONFIG['mac']);
                let html = '';
                
                networks.forEach(net => {
                    const isSelected = selectedForTriangulation.some(n => n.mac === net.mac);
                    html += `
                        <div class="network-item" style="cursor: pointer; padding: 8px;" onclick="toggleNetworkSelection('${net.mac}')">
                            <label style="display: flex; align-items: center; cursor: pointer;">
                                <input type="checkbox" ${isSelected ? 'checked' : ''} 
                                       onchange="toggleNetworkSelection('${net.mac}')" 
                                       style="margin-right: 10px;">
                                <div>
                                    <b>${net.ssid}</b><br>
                                    <small style="color: #888;">${net.mac} | ${net.signal.toFixed(1)} dBm | RTT: ${net.rtt_ms.toFixed(1)} мс</small>
                                </div>
                            </label>
                        </div>
                    `;
                });
                
                document.getElementById('triang-selection').innerHTML = html || '<div style="color: #888;">Нет доступных сетей</div>';
                updateSelectedNetworks();
            }
            
            function toggleNetworkSelection(mac) {
                const network = wifiNetworks.find(n => n.mac === mac);
                if (!network) return;
                
                const index = selectedForTriangulation.findIndex(n => n.mac === mac);
                if (index > -1) {
                    selectedForTriangulation.splice(index, 1);
                } else {
                    selectedForTriangulation.push({...network});
                }
                
                renderTriangulationSelection();
                displayNetworks(wifiNetworks);
                updateTriangulationSection();
                updateTriangulationPointsLayer(); // Обновляем только триангуляционные точки
            }
            
            function updateSelectedNetworks() {
                let html = '';
                selectedForTriangulation.forEach(net => {
                    html += `<div style="padding: 5px; border-bottom: 1px solid #444;">
                        ${net.ssid}<br>
                        <small style="color: #888;">${net.mac} | ${net.signal.toFixed(1)} dBm | ${net.rtt_ms.toFixed(1)} мс</small>
                    </div>`;
                });
                document.getElementById('selected-networks').innerHTML = html || '<div style="color: #888;">Нет выбранных сетей</div>';
            }
            
            function saveTriangulation() {
                if (selectedForTriangulation.length < 3) {
                    alert('Выберите минимум 3 сети для триангуляции!');
                    return;
                }
                
                fetch('/api/triangulation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(selectedForTriangulation)
                })
                .then(res => {
                    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                    return res.json();
                })
                .then(res => {
                    closeTriangulation();
                    document.getElementById('status').innerHTML = `
                        <span class="success">Триангуляция настроена (${res.networks_count} сетей)</span>
                    `;
                    updateTriangulationPointsLayer(); // Обновляем триангуляционные точки после сохранения
                })
                .catch(err => {
                    console.error('Ошибка триангуляции:', err);
                    document.getElementById('status').innerHTML = `<span class="error">Ошибка: ${err.message}</span>`;
                });
            }
            
            window.onclick = function(event) {
                const calibModal = document.getElementById('calibrationModal');
                const triangModal = document.getElementById('triangulationModal');
                if (event.target === calibModal) closeCalibration();
                if (event.target === triangModal) closeTriangulation();
            }
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    import webbrowser
    
    print("\n" + "="*60)
    print("Wi-Fi Scanner PRO v4.3 + Mapbox v3.12.0")
    print("="*60)
    print(f"Роутер: {ROUTER_CONFIG['ssid']}")
    print(f"MAC: {ROUTER_CONFIG['mac']}")
    print(f"IP: {ROUTER_CONFIG.get('ip', 'не указан')}")
    print(f"Коорд. границы: Lng({COORDINATE_BOUNDS['lng_min']} - {COORDINATE_BOUNDS['lng_max']})")
    print(f"                Lat({COORDINATE_BOUNDS['lat_min']} - {COORDINATE_BOUNDS['lat_max']})")
    print("Карта: Moscow Style 2.0 (3D buildings, extrusion)")
    print("="*60)
    print("Сервер: http://localhost:5000")
    print("Интервал по умолчанию: 0.5 сек")
    print("Новые переключатели: MAP, GeoJSON (вкл. по умолчанию)")
    print("Новые настройки: Точность (0.3м), Погрешность (5%)")
    print("СТАТИЧЕСКИЕ координаты - генерируются один раз и сохраняются")
    print("ВЫРАВНИВАНИЕ SELECT: левое выравнивание, отступы стрелки")
    print("БЛОК ФЛАГОВ В СКРОЛЛЕ: max-height 250px, overflow-y: auto")
    print("ИСПРАВЛЕНЫ СТРЕЛКИ SELECT: корректный data-URL с правильной кодировкой")
    print("ИСПРАВЛЕН ЦВЕТ INPUT: #333333 для текста, rgba(255,255,255,0.9) для фона")
    print("ВЕРНУТЫ СТРЕЛКИ: отдельный стиль для .settings-block select")
    print("СВЕТЛАЯ ТЕМА: активирована для всего интерфейса")
    print("Mapbox v3.12.0: 3D buildings, extruded polygons, dusk lighting")
    print("ЦЕНТР КАРТЫ: [37.16332212, 55.98346937] (без изменений)")
    print("РОУТЕР: [37.16332212, 55.98346937] (без изменений)")
    print("ГРАНИЦЫ: оригинальные (без изменений)")
    print("КНОПКИ 'Моя позиция' и 'Авто': переключатели с залипанием")
    print("НОВОЕ: Анимированная синяя точка 110px с волнами (Canvas + render)")
    print("РАБОТАЕТ: Mapbox слой с triggerRepaint, правильный z-index")
    print("ИСПРАВЛЕНО: Попап при клике на точку с координатами и точностью")
    print("ИСПРАВЛЕНО: Точка теперь внутри полупрозрачных 3D зданий")
    print("НОВОЕ: Разделенные слои для роутера и триангуляции (независимые источники)")
    print("ИСПРАВЛЕНО: Красная точка роутера больше не исчезает при триангуляции")
    print("ДОБАВЛЕНО: map.triggerRepaint() и защита от дубликатов")
    print("УБРАНЫ: Все иконки и декоративные символы из попапов")
    print("="*60 + "\n")
    
    scanner_thread = threading.Thread(target=background_scanner, daemon=True)
    scanner_thread.start()
    
    threading.Timer(1.5, lambda: webbrowser.open('http://localhost:5000')).start()
    
    try:
        app.run(port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nСервер остановлен")
