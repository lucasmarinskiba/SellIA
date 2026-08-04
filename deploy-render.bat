@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   SellIA Deploy to Render.com
echo ==========================================
echo.

REM Validar configuración
echo Validando configuración...

if not exist "backend\render.yaml" (
    echo ERROR: backend\render.yaml no encontrado
    exit /b 1
)
echo [OK] render.yaml encontrado

if not exist "backend\requirements.txt" (
    echo ERROR: backend\requirements.txt no encontrado
    exit /b 1
)
echo [OK] requirements.txt encontrado

if not exist "backend\app\sellbot.py" (
    echo ERROR: backend\app\sellbot.py no encontrado
    exit /b 1
)
echo [OK] Main app file encontrado

echo.
echo Verificando cambios en git...
git status --short
if !errorlevel! neq 0 (
    echo ERROR: No se pudo ejecutar git
    exit /b 1
)

echo.
echo ==========================================
echo   Render.com Manual Deployment
echo ==========================================
echo.
echo ABRE ESTO EN TU NAVEGADOR:
echo:
echo https://dashboard.render.com
echo:
echo PASOS:
echo 1. Click 'New +' = 'Web Service'
echo 2. Selecciona GitHub repo: lucasmarinskiba/SellIA
echo 3. Configura:
echo    - Name: selliaai-backend
echo    - Root Directory: backend
echo    - Build Command: pip install -r requirements.txt
echo    - Start Command: uvicorn app.sellbot:app --host 0.0.0.0 --port 8000
echo:
echo 4. Environment Variables:
echo    ALLOWED_ORIGINS=http://localhost:3000,https://sellia-brain.vercel.app
echo    ENVIRONMENT=production
echo:
echo 5. Click 'Create Web Service'
echo 6. Espera 5-10 minutos
echo 7. URL: https://selliaai-backend.onrender.com
echo:
echo ==========================================
echo   Next Steps After Deploy
echo ==========================================
echo:
echo 1. Copiar la URL del backend deployado
echo 2. Editar: frontend\.env.production
echo    NEXT_PUBLIC_API_URL=<URL-DEL-BACKEND>
echo 3. Redeploy frontend en Vercel
echo 4. Test: https://sellia-brain.vercel.app/sellia-brain
echo:
echo [OK] Deploy configuration lista
echo.
pause
