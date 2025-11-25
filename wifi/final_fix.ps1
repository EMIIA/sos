# Для каждой папки (4949, 4950, etc) обрабатываем все .pbf файлы
Get-ChildItem -Directory | Where-Object { [int]$_.Name -ge 4949 } | ForEach-Object {
    $folderX = $_.Name  # 4949, 4950 (это z=13, но нам нужно x из имени файла)
    
    Get-ChildItem "$folderX\*.pbf" | ForEach-Object {
        $x = $_.BaseName  # 2823, 2824, 2825 из имени файла
        $y = "1280"       # предполагаем y=1280
        
        # Создаем структуру 13/x/y/
        $newDir = "13\$x\$y"
        New-Item -ItemType Directory -Force -Path $newDir
        
        # Копируем файл
        Copy-Item $_.FullName "$newDir\$y.pbf"
        Write-Host "Создано: 13/$x/$y/$y.pbf из $folderX/$($_.Name)"
    }
}

Write-Host "Готово! Тестируй: https://localhost:8080/moscow_buildings/13/2823/1280.pbf"
