#!/bin/bash

# VikPay AI Setup Script
# This script sets up the AI recommendation system with Ollama + ChromaDB

echo "🚀 Setting up VikPay AI Recommendation System..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Ollama is installed
if ! command_exists ollama; then
    echo "📦 Installing Ollama..."
    
    # Install Ollama based on OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://ollama.ai/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ollama
        # Start Ollama service
        brew services start ollama
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "🪟 For Windows, please download Ollama from: https://ollama.ai/download"
        echo "   After installation, start Ollama and run this script again."
        exit 1
    fi
    
    # Start Ollama service (Linux/Mac)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        systemctl start ollama || sudo systemctl start ollama
    fi
else
    echo "✅ Ollama is already installed"
fi

# Wait for Ollama to start
echo "⏳ Waiting for Ollama to start..."
sleep 5

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not running. Please start Ollama manually:"
    echo "   Run: ollama serve"
    echo "   Then run this script again."
    exit 1
fi

echo "✅ Ollama is running"

# Pull the required model
echo "📥 Pulling Ollama model (llama3.2:3b)..."
ollama pull llama3.2:3b

# Verify model is available
if ollama list | grep -q "llama3.2:3b"; then
    echo "✅ Model llama3.2:3b is ready"
else
    echo "❌ Failed to pull model. Please run manually: ollama pull llama3.2:3b"
    exit 1
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

# Create ChromaDB directory
echo "🗃️ Setting up ChromaDB..."
mkdir -p ./chroma_db

# Test the AI setup
echo "🧪 Testing AI setup..."
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

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 AI Recommendation System setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Start your FastAPI server: python main.py"
    echo "   2. Upload some videos to generate embeddings"
    echo "   3. Test recommendations at: http://localhost:8000/api/ai/recommendations"
    echo "   4. Check AI health at: http://localhost:8000/api/ai/health"
    echo ""
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   - If Ollama stops working, restart it: ollama serve"
    echo "   - To rebuild embeddings: POST /api/ai/embeddings/rebuild"
    echo "   - Check logs for any issues"
else
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi
