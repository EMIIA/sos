# Обрабатываем только папки с 4949 и выше
Get-ChildItem -Directory | Where-Object { [int]$_.Name -ge 4949 } | ForEach-Object {
    $x = $_.Name  # 4949, 4950, etc
    
    # Проверяем что внутри
    $innerItems = Get-ChildItem $x
    if ($innerItems) {
        # Предполагаем структуру x/1280/1280.pbf
        $newDir = "13\$x\1280"
        New-Item -ItemType Directory -Force -Path $newDir
        Copy-Item "$x\1280\1280.pbf" "$newDir\1280.pbf" -Force
        Write-Host "Создано: 13/$x/1280/1280.pbf"
    }
}

Write-Host "Готово! Тестируй: https://localhost:8080/moscow_buildings/13/4949/1280.pbf"
