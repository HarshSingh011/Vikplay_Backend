@echo off
REM VikPay Backend - Kubernetes Native Quick Deploy (Windows)

echo ☸️  VikPay Backend - Kubernetes Native Deployment
echo ===============================================

REM Check if kubectl is available
kubectl version --client >nul 2>&1
if errorlevel 1 (
    echo ❌ kubectl not found. Installing fallback...
    python setup.py
    pause
    exit /b 0
)

REM Check if docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found. Installing fallback...
    python setup.py
    pause
    exit /b 0
)

echo ✅ Kubernetes tools detected

REM Run Kubernetes-native setup
python setup.py

REM If k8s manifests were created, deploy them
if exist "k8s" (
    echo.
    echo 🚀 Deploying to Kubernetes...
    REM Note: Windows users should use WSL or Git Bash for k8s-deploy.sh
    echo Please run: ./k8s-deploy.sh in WSL or Git Bash
) else (
    echo ⚠️  No Kubernetes manifests found. Using local development.
)

pause
