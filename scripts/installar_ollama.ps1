# ============================================================
#  GUÍA DE INSTALACIÓN Y PRUEBA DE OLLAMA PARA SELLIA
#  Ejecutar ESTE script en PowerShell COMO ADMINISTRADOR
#  después de instalar Ollama desde https://ollama.com
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Instalador/Verificador de Ollama" -ForegroundColor Cyan
Write-Host "  para SellIA - Modelos Locales Gratis" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar si Ollama está instalado
$ollamaPath = (Get-Command ollama -ErrorAction SilentlyContinue).Source

if (-not $ollamaPath) {
    Write-Host "Ollama NO está instalado." -ForegroundColor Red
    Write-Host ""
    Write-Host "PASO 1: Descargá Ollama desde:" -ForegroundColor Yellow
    Write-Host "https://ollama.com/download" -ForegroundColor Blue
    Write-Host ""
    Write-Host "PASO 2: Ejecutá el instalador .exe y seguí las instrucciones." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "PASO 3: Cerrá y volvé a abrir PowerShell." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "PASO 4: Volvé a ejecutar este script." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Presioná ENTER para salir"
    exit 1
}

Write-Host "Ollama encontrado en: $ollamaPath" -ForegroundColor Green
Write-Host ""

# 2. Verificar si el servicio está corriendo
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 3
    Write-Host "Servidor Ollama está CORRIENDO en localhost:11434" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "El servidor Ollama NO está respondiendo." -ForegroundColor Red
    Write-Host "Intentando iniciar Ollama..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 3
        Write-Host "Servidor Ollama iniciado correctamente." -ForegroundColor Green
    } catch {
        Write-Host "No se pudo iniciar Ollama automáticamente." -ForegroundColor Red
        Write-Host "Probá reiniciar la PC o ejecutar 'ollama serve' manualmente." -ForegroundColor Yellow
        Read-Host "Presioná ENTER para salir"
        exit 1
    }
}

# 3. Mostrar modelos instalados
Write-Host "Modelos actualmente instalados:" -ForegroundColor Cyan
if ($response.models) {
    $response.models | ForEach-Object { Write-Host "  - $($_.name)" -ForegroundColor White }
} else {
    Write-Host "  (Ninguno)" -ForegroundColor DarkGray
}
Write-Host ""

# 4. Preguntar qué modelo instalar
Write-Host "MODELOS RECOMENDADOS PARA COPY EN ESPAÑOL:" -ForegroundColor Cyan
Write-Host "  1. llama3.1    - Meta, muy popular, buen balance" -ForegroundColor White
Write-Host "  2. mistral     - Muy rápido, bueno para cortos" -ForegroundColor White
Write-Host "  3. qwen2.5     - Alibaba, excelente en español/chino" -ForegroundColor White
Write-Host "  4. phi4        - Microsoft, buen reasoning" -ForegroundColor White
Write-Host ""

$choice = Read-Host "¿Qué modelo querés instalar/prbar? (1/2/3/4, o ENTER para saltar)"

$modelMap = @{
    "1" = "llama3.1"
    "2" = "mistral"
    "3" = "qwen2.5"
    "4" = "phi4"
}

if ($modelMap.ContainsKey($choice)) {
    $model = $modelMap[$choice]
    Write-Host ""
    Write-Host "Descargando $model... esto puede tardar varios minutos la primera vez." -ForegroundColor Yellow
    Write-Host ""
    ollama pull $model
    Write-Host ""
    Write-Host "Modelo $model instalado correctamente." -ForegroundColor Green
} elseif ($choice -ne "") {
    Write-Host "Opción no válida. Saltando..." -ForegroundColor Yellow
}

# 5. Probar generación de copy
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PRUEBA DE GENERACIÓN DE COPY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$testModel = if ($modelMap.ContainsKey($choice)) { $modelMap[$choice] } else { "llama3.1" }

$body = @{
    model = $testModel
    messages = @(
        @{ role = "system"; content = "Sos un copywriter experto en español. Respondé de forma breve y directa." }
        @{ role = "user"; content = "Escribí un caption corto para Instagram sobre un producto de skincare. Solo el texto, sin explicaciones." }
    )
    stream = $false
    options = @{
        temperature = 0.7
        num_predict = 150
    }
} | ConvertTo-Json -Depth 10

try {
    Write-Host "Enviando prueba a Ollama (modelo: $testModel)..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "http://localhost:11434/api/chat" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 60
    Write-Host ""
    Write-Host "RESPUESTA DE OLLAMA:" -ForegroundColor Green
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    Write-Host $result.message.content -ForegroundColor White
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Tokens usados: $($result.prompt_eval_count + $result.eval_count)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "✅ Ollama funciona correctamente. SellIA ya lo detectará automáticamente." -ForegroundColor Green
} catch {
    Write-Host "❌ Error en la prueba: $_" -ForegroundColor Red
}

Write-Host ""
Read-Host "Presioná ENTER para salir"
