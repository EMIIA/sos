// ============== КОНФИГУРАЦИЯ ==============
const ROUTER_CONFIG = {
  ssid: 'EMIIA.AI MRV',
  mac: '28-CD-C4-13-EE-A3',
  position: [37.16332212, 55.98346937]
};

const ROOM_CORNERS = [
  [37.16344674, 55.98346609],
  [37.16332363, 55.98346489],  
  [37.16330701, 55.98350694],
  [37.16344154, 55.98350823],
  [37.16344674, 55.98346609]
];

// ============== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==============
let map;
let updateCount = 0;
let positionMarker = null;

// ============== ИНИЦИАЛИЗАЦИЯ ==============
async function initializeApp() {
  try {
    await initializeMap();
    updateSystemStatus('✅ Система готова', 'status-online');
    addDebugInfo('Приложение инициализировано');
  } catch (error) {
    updateSystemStatus('❌ Ошибка инициализации', 'status-offline');
  }
}

// ============== MAPBOX ==============
async function initializeMap() {
  map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/satellite-v9',
    center: ROUTER_CONFIG.position,
    zoom: 20,
    pitch: 45,
    antialias: true
  });

  map.addControl(new mapboxgl.NavigationControl(), 'top-right');
  map.addControl(new mapboxgl.ScaleControl(), 'bottom-right');

  map.on('load', () => {
    // Добавляем полигон комнаты
    map.addSource('room', {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [ROOM_CORNERS]
        }
      }
    });

    map.addLayer({
      id: 'room-fill',
      type: 'fill',
      source: 'room',
      paint: {
        'fill-color': '#00ff88',
        'fill-opacity': 0.1
      }
    });

    map.addLayer({
      id: 'room-border',
      type: 'line',
      source: 'room',
      paint: {
        'line-color': '#00ff88',
        'line-width': 3,
        'line-opacity': 0.8
      }
    });

    // Добавляем маркер роутера
    addRouterMarker();
  });
}

function addRouterMarker() {
  const el = document.createElement('div');
  el.className = 'router-marker';
  el.innerHTML = '📡';

  new mapboxgl.Marker(el)
    .setLngLat(ROUTER_CONFIG.position)
    .setPopup(new mapboxgl.Popup({ offset: 25 })
      .setHTML(`
        <div class="popup-content">
          <h3>EMIIA.AI MRV</h3>
          <p>MAC: ${ROUTER_CONFIG.mac}</p>
          <p>Координаты: ${ROUTER_CONFIG.position[1].toFixed(6)}, ${ROUTER_CONFIG.position[0].toFixed(6)}</p>
        </div>
      `))
    .addTo(map);
}

function updatePositionMarker(coords, accuracy) {
  if (positionMarker) positionMarker.remove();

  const el = document.createElement('div');
  el.className = 'position-marker';
  el.style.width = `${accuracy * 2}px`;
  el.style.height = `${accuracy * 2}px`;

  positionMarker = new mapboxgl.Marker(el)
    .setLngLat(coords)
    .setPopup(new mapboxgl.Popup({ offset: 25 })
      .setHTML(`
        <div class="popup-content">
          <h4>📍 Ваше местоположение</h4>
          <p>Точность: ±${accuracy.toFixed(1)} м</p>
          <p>Обновлений: ${updateCount}</p>
        </div>
      `))
    .addTo(map);

  map.flyTo({ center: coords, zoom: 20, speed: 0.3 });
}

// ============== WIFI СКАНИРОВАНИЕ ==============
async function scanWiFi() {
  if (!window.electronAPI) {
    alert('❌ Запустите приложение через Electron!');
    return;
  }

  try {
    updateSystemStatus('📶 Сканирование Wi-Fi...', 'status-scanning');
    document.getElementById('wifiBtn').disabled = true;

    const networks = await window.electronAPI.scanWiFi();
    
    if (networks.error) {
      throw new Error(networks.error);
    }

    updateCount++;
    addDebugInfo(`✅ Найдено сетей: ${networks.length}`);

    // Находим наш роутер
    const router = networks.find(n => 
      n.ssid === ROUTER_CONFIG.ssid || n.mac === ROUTER_CONFIG.mac
    );

    if (router) {
      const distance = calculateDistanceFromSignal(router.signal);
      
      document.getElementById('signalValue').textContent = router.signal + ' dBm';
      document.getElementById('distanceValue').textContent = distance.toFixed(2) + ' м';
      document.getElementById('networksCount').textContent = networks.length;
      
      addDebugInfo(`📡 Роутер найден: ${router.signal} dBm ≈ ${distance.toFixed(2)} м`);
      
      // Пример триангуляции
      if (networks.length >= 3) {
        const position = calculateTrilateration(networks);
        updatePositionMarker([position.lng, position.lat], position.accuracy);
      }
    } else {
      addDebugInfo('⚠️ Роутер не найден в скане');
    }

    updateSystemStatus('✅ Сканирование завершено', 'status-online');
  } catch (error) {
    addDebugInfo(`❌ Ошибка: ${error.message}`);
    updateSystemStatus('❌ Ошибка сканирования', 'status-offline');
  } finally {
    document.getElementById('wifiBtn').disabled = false;
  }
}

// ============== РАСЧЕТЫ ==============
function calculateDistanceFromSignal(signal) {
  // Free Space Path Loss модель
  const txPower = -20; // мощность роутера
  const pathLoss = txPower - signal;
  return Math.pow(10, (pathLoss - 32.44) / 20); // расстояние в метрах
}

function calculateTrilateration(networks) {
  // Упрощенная взвешенная трилатерация
  const knownNetworks = networks.filter(n => {
    const router = KNOWN_ROUTERS.find(r => r.mac === n.mac);
    if (router) {
      n.lat = router.lat;
      n.lng = router.lng;
      n.weight = Math.abs(n.signal);
      return true;
    }
    return false;
  });

  if (knownNetworks.length < 3) {
    throw new Error('Недостаточно точек для триангуляции');
  }

  let sumLat = 0, sumLng = 0, totalWeight = 0;
  knownNetworks.forEach(n => {
    sumLat += n.lat * n.weight;
    sumLng += n.lng * n.weight;
    totalWeight += n.weight;
  });

  return {
    lat: sumLat / totalWeight,
    lng: sumLng / totalWeight,
    accuracy: 5 // примерная погрешность
  };
}

// ============== UI ФУНКЦИИ ==============
function updateSystemStatus(message, className) {
  const statusElement = document.getElementById('systemStatus');
  const icon = className.includes('online') ? '✅' : 
              className.includes('scanning') ? '🔍' : '⏸️';
  statusElement.innerHTML = `<div class="icon">${icon}</div><span>${message}</span>`;
  statusElement.className = `status-indicator ${className}`;
}

function addDebugInfo(message) {
  const debugInfo = document.getElementById('debugInfo');
  const timestamp = new Date().toLocaleTimeString();
  debugInfo.innerHTML += `[${timestamp}] ${message}<br>`;
  debugInfo.scrollTop = debugInfo.scrollHeight;
}

function showDebugInfo() {
  document.getElementById('debugSection').classList.toggle('hidden');
}

// ============== ИЗВЕСТНЫЕ ТОЧКИ ==============
const KNOWN_ROUTERS = [
  { mac: '28-CD-C4-13-EE-A3', lat: 55.98346937, lng: 37.16332212 }
  // Добавьте больше точек для триангуляции
];

// ============== ЗАПУСК ==============
document.addEventListener('DOMContentLoaded', initializeApp);
