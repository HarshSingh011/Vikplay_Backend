@echo off
REM VikPay AI Setup Script for Windows
REM This script sets up the AI recommendation system with Ollama + ChromaDB

echo 🚀 Setting up VikPay AI Recommendation System...

REM Check if Ollama is installed
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Ollama not found. Please install Ollama first:
    echo    1. Go to https://ollama.ai/download
    echo    2. Download and install Ollama for Windows  
    echo    3. Restart your terminal
    echo    4. Run this script again
    pause
    exit /b 1
)

echo ✅ Ollama is installed

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo 🚀 Starting Ollama...
    start /B ollama serve
    timeout /t 10 /nobreak >nul
)

REM Check again if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ollama is not running. Please start Ollama manually:
    echo    Run: ollama serve
    echo    Then run this script again.
    pause
    exit /b 1
)

echo ✅ Ollama is running

REM Pull the required model
echo 📥 Pulling Ollama model (llama3.2:3b)...
ollama pull llama3.2:3b

REM Verify model is available
ollama list | findstr "llama3.2:3b" >nul
if %errorlevel% neq 0 (
    echo ❌ Failed to pull model. Please run manually: ollama pull llama3.2:3b
    pause
    exit /b 1
)

echo ✅ Model llama3.2:3b is ready

REM Install Python dependencies
echo 🐍 Installing Python dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)

REM Create ChromaDB directory
echo 🗃️ Setting up ChromaDB...
if not exist "chroma_db" mkdir chroma_db

REM Test the AI setup
echo 🧪 Testing AI setup...
python -c "
import sys
try:
    import ollama
    import chromadb
    print('✅ All AI dependencies installed successfully')
    
    # Test Ollama connection
    models = ollama.list()
    print(f'✅ Ollama connected. Available models: {len(models[\"models\"])}')
    
    # Test ChromaDB
    client = chromadb.Client()
    print('✅ ChromaDB initialized successfully')
    
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Setup test failed: {e}')
    sys.exit(1)
"

if %errorlevel% neq 0 (
    echo ❌ Setup failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo 🎉 AI Recommendation System setup completed successfully!
echo.
echo 📋 Next steps:
echo    1. Start your FastAPI server: python main.py
echo    2. Upload some videos to generate embeddings
echo    3. Test recommendations at: http://localhost:8000/api/ai/recommendations
echo    4. Check AI health at: http://localhost:8000/api/ai/health
echo.
echo 📚 API Documentation: http://localhost:8000/docs
echo.
echo 🔧 Troubleshooting:
echo    - If Ollama stops working, restart it: ollama serve
echo    - To rebuild embeddings: POST /api/ai/embeddings/rebuild
echo    - Check logs for any issues
echo.
pause
