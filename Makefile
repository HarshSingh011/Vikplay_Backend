# VikPay Backend - Kubernetes Native Makefile
# Pure cloud-native deployment automation

.PHONY: help setup deploy status logs scale clean k8s-check

# Default target
help:
	@echo "☸️  VikPay Backend - Kubernetes Native Commands"
	@echo "============================================="
	@echo ""
	@echo "Kubernetes Native:"
	@echo "  setup      - Generate Kubernetes manifests and setup"
	@echo "  deploy     - Deploy to Kubernetes cluster"
	@echo "  status     - Check deployment status"
	@echo "  logs       - View application logs"
	@echo "  scale      - Scale deployment (make scale REPLICAS=3)"
	@echo "  clean      - Delete deployment from cluster"
	@echo ""
	@echo "Development:"
	@echo "  k8s-check  - Check if Kubernetes tools are available"
	@echo "  local      - Local development fallback (if K8s unavailable)"
	@echo ""

# Setup Kubernetes manifests
setup:
	@echo "☸️  Setting up Kubernetes-native deployment..."
	python3 setup.py

# Deploy to Kubernetes
deploy: setup
	@echo "🚀 Deploying VikPay Backend to Kubernetes..."
	@if [ -f k8s-deploy.sh ]; then \
		./k8s-deploy.sh; \
	else \
		echo "❌ Kubernetes deployment script not found. Run 'make setup' first."; \
	fi

# Check deployment status
status:
	@echo "📊 Checking VikPay Backend status..."
	kubectl get pods -l app=vikpay-backend -n vikpay
	kubectl get svc vikpay-backend-service -n vikpay

# View logs
logs:
	@echo "📜 Viewing VikPay Backend logs..."
	kubectl logs -l app=vikpay-backend -n vikpay -f

# Scale deployment
scale:
	@echo "📈 Scaling VikPay Backend..."
	@if [ -z "$(REPLICAS)" ]; then \
		echo "Usage: make scale REPLICAS=3"; \
	else \
		kubectl scale deployment vikpay-backend --replicas=$(REPLICAS) -n vikpay; \
	fi

# Clean deployment
clean:
	@echo "🧹 Cleaning VikPay Backend deployment..."
	kubectl delete namespace vikpay --ignore-not-found=true

# Check Kubernetes tools
k8s-check:
	@echo "🔍 Checking Kubernetes tools..."
	@command -v kubectl >/dev/null 2>&1 && echo "✅ kubectl found" || echo "❌ kubectl not found"
	@command -v docker >/dev/null 2>&1 && echo "✅ docker found" || echo "❌ docker not found"

# Local development fallback
local:
	@echo "🔧 Starting local development..."
	@if [ -f local-dev.sh ]; then \
		./local-dev.sh; \
	else \
		echo "❌ Local development script not found. Run 'make setup' first."; \
	fi

# Port forward for local access
port-forward:
	@echo "🌐 Setting up port forwarding..."
	kubectl port-forward service/vikpay-backend-service 8000:80 -n vikpay

# Full deployment workflow
full-deploy: k8s-check setup deploy status
	@echo "🎉 Full Kubernetes deployment completed!"
	@echo "Access your app: kubectl port-forward service/vikpay-backend-service 8000:80 -n vikpay"

# Development workflow (local)
dev: setup local

# Production deployment
prod: full-deploy
