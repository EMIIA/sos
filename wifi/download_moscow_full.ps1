# download_moscow_full.ps1
$serverStaticPath = "C:\Users\vstar\Desktop\emiia-mrv\static\tiles"

Write-Host "📥 Скачивание векторных тайлов Москвы (300 MB)..." -ForegroundColor Cyan
Write-Host "📍 Путь: $serverStaticPath" -ForegroundColor Cyan

# Создать папки
0..15 | ForEach-Object { 
    New-Item -ItemType Directory -Path "$serverStaticPath\$_" -Force | Out-Null
}

function Download-Tiles {
    param($zoom, $minX, $maxX, $minY, $maxY, $sourceUrl = "https://tiles.openmaptiles.org")
    
    $totalTiles = ($maxX - $minX + 1) * ($maxY - $minY + 1)
    $completed = 0
    $failed = 0
    
    Write-Host "🔽 Zoom $zoom: $totalTiles тайлов..." -ForegroundColor Yellow
    
    for ($x = $minX; $x -le $maxX; $x++) {
        $xDir = "$serverStaticPath\$zoom\$x"
        New-Item -ItemType Directory -Path $xDir -Force | Out-Null
        
        for ($y = $minY; $y -le $maxY; $y++) {
            $url = "$sourceUrl/$zoom/$x/$y.pbf"
            $path = "$xDir\$y.pbf"
            
            if (Test-Path $path) {
                $completed++
                continue
            }
            
            try {
                Invoke-WebRequest -Uri $url -OutFile $path -TimeoutSec 30
                $completed++
                
                if ($completed % 50 -eq 0) {
                    Write-Progress -Activity "Zoom $zoom" -Status "$completed/$totalTiles" -PercentComplete (($completed / $totalTiles) * 100)
                }
            }
            catch {
                $failed++
            }
            
            Start-Sleep -Milliseconds (Get-Random -Minimum 20 -Maximum 50)
        }
    }
    
    Write-Progress -Activity "Zoom $zoom" -Completed
    Write-Host "✅ Zoom $zoom: $completed/$totalTiles тайлов (ошибок: $failed)" -ForegroundColor Green
}

$moscowTiles = @{
    0 = @{minX=0; maxX=0; minY=0; maxY=0}
    1 = @{minX=1; maxX=1; minY=0; maxY=0}
    2 = @{minX=2; maxX=2; minY=1; maxY=1}
    3 = @{minX=4; maxX=4; minY=2; maxY=2}
    4 = @{minX=8; maxX=9; minY=4; maxY=4}
    5 = @{minX=17; maxX=18; minY=8; maxY=9}
    6 = @{minX=35; maxX=36; minY=17; maxY=18}
    7 = @{minX=71; maxX=72; minY=34; maxY=35}
    8 = @{minX=142; maxX=145; minY=69; maxY=70}
    9 = @{minX=285; maxX=290; minY=138; maxY=141}
    10 = @{minX=571; maxX=582; minY=277; maxY=283}
    11 = @{minX=1142; maxX=1165; minY=555; maxY=567}
    12 = @{minX=2285; maxX=2331; minY=1111; maxY=1135}
    13 = @{minX=4571; maxX=4663; minY=2223; maxY=2271}
    14 = @{minX=9143; maxX=9327; minY=4447; maxY=4543}
    15 = @{minX=18287; maxX=18655; minY=8895; maxY=9087}
}

Write-Host "🚀 Начало скачивания..." -ForegroundColor Green

foreach ($zoom in 8..15) {
    $coords = $moscowTiles[$zoom]
    Download-Tiles -zoom $zoom -minX $coords.minX -maxX $coords.maxX -minY $coords.minY -maxY $coords.maxY
}

Write-Host ""
Write-Host "🎉 ВСЕ ТАЙЛЫ СКАЧАНЫ!" -ForegroundColor Green
Write-Host "📁 Папка: $serverStaticPath" -ForegroundColor Green
Write-Host "💾 Примерный размер: 300 MB" -ForegroundColor Green
