#!/bin/bash
# Local development fallback (non-Kubernetes)

echo "🔧 VikPay Backend - Local Development Setup"
echo "=========================================="

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "📈 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file..."
    cat > .env << EOF
# Local development configuration
DATABASE_URL=sqlite:///./vidplay.db
SECRET_KEY=local-development-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Update these with your actual credentials
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=your_bucket
EOF
    echo "⚠️  Please update .env with your actual credentials"
fi

echo "🚀 Starting server..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
