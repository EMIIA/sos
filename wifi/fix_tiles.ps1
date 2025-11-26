# fix_tiles.ps1
# Скрипт для исправления структуры тайлов

$root = ".\static"
$temp = ".\static_temp"

# Создаем временную папку
if (Test-Path $temp) { Remove-Item $temp -Recurse -Force }
New-Item -ItemType Directory -Force -Path $temp

# Ищем все .pbf файлы и перемещаем на правильный уровень
Get-ChildItem -Path $root -Filter "*.pbf" -Recurse | ForEach-Object {
    $parts = $_.FullName.Split('\')
    # Пример: static\13\4947\2835\3869.pbf
    # parts[-1] = 3869.pbf (Y)
    # parts[-2] = 2835 (лишний уровень)
    # parts[-3] = 4947 (X)
    # parts[-4] = 13 (Z)
    
    $z = $parts[-4]
    $x = $parts[-3]
    $y = $_.BaseName  # 3869
    
    # Новый путь: static_temp/13/4947/3869.pbf
    $newDir = Join-Path $temp $z $x
    New-Item -ItemType Directory -Force -Path $newDir | Out-Null
    
    $newPath = Join-Path $newDir "$y.pbf"
    Copy-Item $_.FullName $newPath -Force
    
    Write-Host "Перемещено: $z/$x/$y.pbf" -ForegroundColor Green
}

# Заменяем структуру
Remove-Item $root -Recurse -Force
Rename-Item $temp $root

Write-Host "✓ Готово! Новая структура:" -ForegroundColor Cyan
Get-ChildItem $root -Directory | ForEach-Object {
    $tiles = Get-ChildItem $_.FullName -Filter "*.pbf" -Recurse
    Write-Host "Зум $($_.Name): $($tiles.Count) тайлов" -ForegroundColor Yellow
}
