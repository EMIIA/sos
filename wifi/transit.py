# ... [предыдущий код без изменений] ...

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
        
        <!-- PWA -->
        <link rel="shortcut icon" href="https://sos.emiia.ai/vv.ico" type="image/x-icon">
        <meta name="theme-color" content="#f8f9fa">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <link rel="manifest" href="https://sos.emiia.ai/vv.webmanifest">
        
        <title>EMIIA.AI SIP (MRV/SDK)</title>
        <script src="https://api.mapbox.com/mapbox-gl-js/v3.12.0/mapbox-gl.js"></script>
        <link href="https://api.mapbox.com/mapbox-gl-js/v3.12.0/mapbox-gl.css" rel="stylesheet" />
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
            
            /* ========== СКРЫТЫЕ СКРОЛЛБАРЫ СО СОХРАНЕНИЕМ ФУНКЦИОНАЛЬНОСТИ ========== */
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: transparent;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: transparent;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: transparent;
            }
            
            ::-webkit-scrollbar-button {
                display: none;
            }
            
            * {
                scrollbar-width: thin;
                scrollbar-color: transparent transparent;
                box-sizing: border-box;
            }
            
            body { 
                margin: 0; 
                font-family: 'Segoe UI', system-ui, sans-serif; 
                background: var(--secondary); 
                color: #333333; 
                overflow: hidden; 
            }
            
            #map { 
                position: absolute; 
                top: 0; 
                left: 0; 
                width: 100%; 
                height: 100%; 
            }
            
            .controls {
                position: absolute; 
                top: 20px; 
                left: 20px; 
                background: rgba(255, 255, 255, 0.95);
                padding: 0;
                border-radius: 18px; 
                border: 0px solid var(--primary);
                width: 320px;
                max-height: 85vh;
                backdrop-filter: blur(10px); 
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                z-index: 10;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            /* Новый залипший блок */
            .sticky-header {
                position: sticky;
                top: 0;
                background: #f8f9fa;
                padding: 20px;
                border-radius: 18px 18px 0 0;
                z-index: 20;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                flex-shrink: 0;
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
            
            /* Контент под залипшим блоком */
            .controls-content {
                padding: 20px;
                overflow-y: auto;
                flex: 1;
                /* Скрываем скроллбары, но сохраняем функциональность */
                scrollbar-width: thin;
                scrollbar-color: transparent transparent;
            }
            
            .controls-content::-webkit-scrollbar {
                width: 8px;
            }
            
            .controls-content::-webkit-scrollbar-track {
                background: transparent;
            }
            
            .controls-content::-webkit-scrollbar-thumb {
                background: transparent;
            }
            
            /* Остальные стили без изменений */
            .button-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
                margin: 10px 0;
            }
            
            .btn {
                padding: 12px 15px; 
                margin: 0; 
                background: #6d9eeb; 
                color: #f8f9fa; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                font-weight: bold;
                transition: all 0.2s ease; 
                font-size: 13px; 
                text-align: center;
                min-height: 45px; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                white-space: nowrap;
            }
            
            .btn:hover {
                background: #3c78d8; 
                transform: translateY(-2px);
                box-shadow: 0 1px 0px rgba(0, 255, 136, 0.4);
            }
            
            .btn:active { 
                transform: translateY(0); 
            }
            
            .btn.active {
                background: #3c78d8;
                transform: translateY(-2px);
                box-shadow: 0 1px 0px rgba(0, 255, 136, 0.4);
            }
            
            .btn.btn-secondary:hover, 
            .btn.btn-secondary.active {
                background: #3c78d8;
            }
            
            .btn.btn-info:hover, 
            .btn.btn-info.active {
                background: #3c78d8;
            }
            
            .btn:disabled { 
                background: red; 
                color: red; 
                cursor: not-allowed; 
                transform: none; 
            }
            
            .info { 
                margin: 10px 0; 
                font-size: 0.9em; 
                line-height: 1.4; 
            }
            
            .error { 
                color: var(--error); 
            }
            
            .success { 
                color: var(--primary); 
            }
            
            .warning { 
                color: var(--warning); 
            }
            
            .network-list {
                max-height: 300px;
                font-size: 0.8em;
                border: 1px solid rgba(0, 255, 136, 0.2); 
                border-radius: 8px;
                padding: 10px; 
                background: rgba(0, 0, 0, 0.05);
                overflow-y: auto;
                /* Скрываем скроллбары */
                scrollbar-width: thin;
                scrollbar-color: transparent transparent;
            }
            
            .network-list::-webkit-scrollbar {
                width: 8px;
            }
            
            .network-list::-webkit-scrollbar-track {
                background: transparent;
            }
            
            .network-list::-webkit-scrollbar-thumb {
                background: transparent;
            }
            
            .network-item {
                padding: 10px; 
                margin: 5px 0; 
                border-radius: 6px;
                border-left: 4px solid #28a745; 
                background: rgba(0, 0, 0, 0.03);
                transition: all 0.3s ease; 
                position: relative;
            }
            
            .network-item.router { 
                border-left-color: #dc3545; 
                background: rgba(255, 0, 0, 0.05); 
            }
            
            .signal-bar { 
                height: 6px; 
                background: rgba(0, 0, 0, 0.1); 
                border-radius: 3px; 
                margin: 5px 0; 
            }
            
            .signal-fill { 
                height: 100%; 
                border-radius: 3px; 
                transition: width 0.8s ease; 
            }
            
            .rtt-display {
                font-size: 10px; 
                color: var(--info); 
                font-weight: bold;
                margin-top: 3px; 
                border-top: 1px dashed rgba(0, 204, 255, 0.3);
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
                display: none; 
                position: fixed; 
                top: 0; 
                left: 0; 
                width: 100%; 
                height: 100%;
                background: rgba(0, 0, 0, 0.7); 
                z-index: 1000; 
                backdrop-filter: blur(5px);
            }
            
            .modal-content {
                position: absolute; 
                top: 50%; 
                left: 50%; 
                transform: translate(-50%, -50%);
                background: var(--secondary); 
                padding: 25px; 
                border-radius: 15px;
                border: 1px solid var(--primary); 
                max-width: 450px; 
                width: 90%;
                max-height: 80vh; 
                overflow-y: auto; 
                color: #333333;
                /* Скрываем скроллбары */
                scrollbar-width: thin;
                scrollbar-color: transparent transparent;
            }
            
            .modal-content::-webkit-scrollbar {
                width: 8px;
            }
            
            .modal-content::-webkit-scrollbar-track {
                background: transparent;
            }
            
            .modal-content::-webkit-scrollbar-thumb {
                background: transparent;
            }
            
            .modal-header {
                display: flex; 
                justify-content: space-between; 
                align-items: center;
                margin-bottom: 20px; 
                padding-bottom: 10px; 
                border-bottom: 1px solid var(--primary);
            }
            
            .modal-close {
                background: var(--error); 
                color: white; 
                border: none;
                border-radius: 50%; 
                width: 30px; 
                height: 30px; 
                cursor: pointer;
                font-size: 18px; 
                display: flex; 
                align-items: center; 
                justify-content: center;
            }
            
            .settings-block input, 
            .settings-block select {
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
            
            .settings-block input:focus, 
            .settings-block select:focus {
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
                height: 1px; 
                background: var(--primary); 
                margin: 15px 0; 
                opacity: 0.3;
            }
            
            h2, h3 { 
                margin-top: 0; 
                color: var(--primary); 
            }
            
            h3 { 
                font-size: 1.1em; 
            }
            
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
                /* Скрываем скроллбары */
                scrollbar-width: thin;
                scrollbar-color: transparent transparent;
            }
            
            .switches-container::-webkit-scrollbar,
            .network-list::-webkit-scrollbar,
            .modal-content::-webkit-scrollbar,
            .controls-content::-webkit-scrollbar {
                width: 8px;
            }
            
            .switches-container::-webkit-scrollbar-track,
            .network-list::-webkit-scrollbar-track,
            .modal-content::-webkit-scrollbar-track,
            .controls-content::-webkit-scrollbar-track {
                background: transparent;
            }
            
            .switches-container::-webkit-scrollbar-thumb,
            .network-list::-webkit-scrollbar-thumb,
            .modal-content::-webkit-scrollbar-thumb,
            .controls-content::-webkit-scrollbar-thumb {
                background: transparent;
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
            
            .btn.active {
                background: #3c78d8;
                transform: translateY(-2px);
                box-shadow: 0 1px 0px #3c78d8;
            }
            
            a.mapboxgl-ctrl-logo{
                width: 0;
                height: 0;
                margin: 0 0 -4px-4px;
                display: block;
                background-repeat: no-repeat;
                cursor: pointer;
                overflow: hidden;
                background-image: url(data:image/svg+xml;charset=utf-8,%3Csvg width='88' height='23' viewBox='0 0 88 23' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' fill-rule='evenodd'%3E %3Cdefs%3E %3Cpath id='logo' d='M11.5 2.25c5.105 0 9.25 4.145 9.25 9.25s-4.145 9.25-9.25 9.25-9.25-4.145-9.25-9.25 4.145-9.25 9.25-9.25zM6.997 15.983c-.051-.338-.828-5.802 2.233-8.873a4.395 4.395 0 013.13-1.28c1.27 0 2.49.51 3.39 1.42.91.9 1.42 2.12 1.42 3.39 0 1.18-.449 2.301-1.28 3.13C12.72 16.93 7 16 7 16l-.003-.017zM15.3 10.5l-2 .8-.8 2-.8-2-2-.8 2-.8.8-2 .8 2 2 .8z'/%3E %3Cpath id='text' d='M50.63 8c.13 0 .23.1.23.23V9c.7-.76 1.7-1.18 2.73-1.18 2.17 0 3.95 1.85 3.95 4.17s-1.77 4.19-3.94 4.19c-1.04 0-2.03-.43-2.74-1.18v3.77c0 .13-.1.23-.23.23h-1.4c-.13 0-.23-.1-.23-.23V8.23c0-.12.1-.23.23-.23h1.4zm-3.86.01c.01 0 .01 0 .01-.01.13 0 .22.1.22.22v7.55c0 .12-.1.23-.23.23h-1.4c-.13 0-.23-.1-.23-.23V15c-.7.76-1.69 1.19-2.73 1.19-2.17 0-3.94-1.87-3.94-4.19 0-2.32 1.77-4.19 3.94-4.19 1.03 0 2.02.43 2.73 1.18v-.75c0-.12.1-.23.23-.23h1.4zm26.375-.19a4.24 4.24 0 00-4.16 3.29c-.13.59-.13 1.19 0 1.77a4.233 4.233 0 004.17 3.3c2.35 0 4.26-1.87 4.26-4.19 0-2.32-1.9-4.17-4.27-4.17zM60.63 5c.13 0 .23.1.23.23v3.76c.7-.76 1.7-1.18 2.73-1.18 1.88 0 3.45 1.4 3.84 3.28.13.59.13 1.2 0 1.8-.39 1.88-1.96 3.29-3.84 3.29-1.03 0-2.02-.43-2.73-1.18v.77c0 .12-.1.23-.23.23h-1.4c-.13 0-.23-.1-.23-.23V5.23c0-.12.1-.23.23-.23h1.4zm-34 11h-1.4c-.13 0-.23-.11-.23-.23V8.22c.01-.13.1-.22.23-.22h1.4c.13 0 .22.11.23.22v.68c.5-.68 1.3-1.09 2.16-1.1h.03c1.09 0 2.09.6 2.6 1.55.45-.95 1.4-1.55 2.44-1.56 1.62 0 2.93 1.25 2.9 2.78l.03 5.2c0 .13-.1.23-.23.23h-1.41c-.13 0-.23-.11-.23-.23v-4.59c0-.98-.74-1.71-1.62-1.71-.8 0-1.46.7-1.59 1.62l.01 4.68c0 .13-.11.23-.23.23h-1.41c-.13 0-.23-.11-.23-.23v-4.59c0-.98-.74-1.71-1.62-1.71-.85 0-1.54.79-1.6 1.8v4.5c0 .13-.1.23-.23.23zm53.615 0h-1.61c-.04 0-.08-.01-.12-.03-.09-.06-.13-.19-.06-.28l2.43-3.71-2.39-3.65a.213.213 0 01-.03-.12c0-.12.09-.21.21-.21h1.61c.13 0 .24.06.3.17l1.41 2.37 1.4-2.37a.34.34 0 01.3-.17h1.6c.04 0 .08.01.12.03.09.06.13.19.06.28l-2.37 3.65 2.43 3.7c0 .05.01.09.01.13 0 .12-.09.21-.21.21h-1.61c-.13 0-.24-.06-.3-.17l-1.44-2.42-1.44 2.42a.34.34 0 01-.3.17zm-7.12-1.49c-1.33 0-2.42-1.12-2.42-2.51 0-1.39 1.08-2.52 2.42-2.52 1.33 0 2.42 1.12 2.42 2.51 0 1.39-1.08 2.51-2.42 2.52zm-19.865 0c-1.32 0-2.39-1.11-2.42-2.48v-.07c.02-1.38 1.09-2.49 2.4-2.49 1.32 0 2.41 1.12 2.41 2.51 0 1.39-1.07 2.52-2.39 2.53zm-8.11-2.48c-.01 1.37-1.09 2.47-2.41 2.47s-2.42-1.12-2.42-2.51c0-1.39 1.08-2.52 2.4-2.52 1.33 0 2.39 1.11 2.41 2.48l.02.08zm18.12 2.47c-1.32 0-2.39-1.11-2.41-2.48v-.06c.02-1.38 1.09-2.48 2.41-2.48s2.42 1.12 2.42 2.51c0 1.39-1.09 2.51-2.42 2.51z'/%3E %3C/defs%3E %3Cmask id='clip'%3E %3Crect x='0' y='0' width='100%25' height='100%25' fill='white'/%3E %3Cuse xlink:href='%23logo'/%3E %3Cuse xlink:href='%23text'/%3E %3C/mask%3E %3Cg id='outline' opacity='0.3' stroke='%23000' stroke-width='3'%3E %3Ccircle mask='url(%23clip)' cx='11.5' cy='11.5' r='9.25'/%3E %3Cuse xlink:href='%23text' mask='url(%23clip)'/%3E %3C/g%3E %3Cg id='fill' opacity='0.9' fill='%23fff'%3E %3Cuse xlink:href='%23logo'/%3E %3Cuse xlink:href='%23text'/%3E %3C/g%3E %3C/svg%3E);
            }
            
            .switches-container {
                margin: 15px 0;
                padding: 10px;
                background: white;
                border-radius: 8px;
                border: 1px solid #3c78d8;
                max-height: 250px;
                overflow-y: auto;
                /* Скрываем скроллбары */
                scrollbar-width: thin;
                scrollbar-color: transparent transparent;
            }
            
            .switches-container::-webkit-scrollbar {
                width: 8px;
            }
            
            .switches-container::-webkit-scrollbar-track {
                background: transparent;
            }
            
            .switches-container::-webkit-scrollbar-thumb {
                background: transparent;
            }
            
            .network-list {
                max-height: 300px;
                font-size: 0.8em;
                border: 1px solid #3c78d8;
                border-radius: 8px;
                padding: 10px;
                background: #fff;
                overflow-y: auto;
                /* Скрываем скроллбары */
                scrollbar-width: thin;
                scrollbar-color: transparent transparent;
            }
            
            .network-list::-webkit-scrollbar {
                width: 8px;
            }
            
            .network-list::-webkit-scrollbar-track {
                background: transparent;
            }
            
            .network-list::-webkit-scrollbar-thumb {
                background: transparent;
            }
            
            .network-item {
                padding: 10px;
                margin: 5px 0;
                border-radius: 6px;
                border-left: 4px solid #28a745;
                background: #fff;
                transition: all 0.3s ease;
                position: relative;
            }
            
            .network-item.router {
                border-left-color: #dc3545;
                background: rgb(205 221 247 / 42%);
            }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="controls">
            <!-- Залипший блок с логотипом и текстом -->
            <div class="sticky-header">
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
            </div>
            
            <!-- Основной контент под залипшим блоком -->
            <div class="controls-content">
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
                        <input class="form-check-input" type="checkbox" id="rtt-toggle" checked>
                        <label class="form-check-label" for="rtt-toggle">Круговая задержка (RTT)</label>
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
                        <input class="form-check-input" type="checkbox" id="trilateration-toggle" checked>
                        <label class="form-check-label" for="trilateration-toggle">Трилатерация</label>
                    </div>
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="triangulation-toggle" checked>
                        <label class="form-check-label" for="triangulation-toggle">Триангуляция</label>
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
        </div>
        
        <!-- Модальные окна без изменений -->
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
