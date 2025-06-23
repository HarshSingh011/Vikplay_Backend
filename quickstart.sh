#!/bin/bash

# VikPay Backend - Kubernetes Native Quick Deploy
# Pure Kubernetes approach for cloud-native deployment

set -e

echo "☸️  VikPay Backend - Kubernetes Native Deployment"
echo "==============================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Installing fallback..."
    python3 setup.py
    exit 0
fi

# Check if docker is available  
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Installing fallback..."
    python3 setup.py
    exit 0
fi

echo "✅ Kubernetes tools detected"

# Run Kubernetes-native setup
python3 setup.py

# If k8s manifests were created, deploy them
if [ -d "k8s" ]; then
    echo ""
    echo "🚀 Deploying to Kubernetes..."
    ./k8s-deploy.sh
else
    echo "⚠️  No Kubernetes manifests found. Using local development."
fi
