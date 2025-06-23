# VikPay Backend - Kubernetes Native

A cloud-native FastAPI backend with WebRTC support, designed for Kubernetes deployment with automatic dependency management.

## ☸️ Kubernetes-Native Deployment (Recommended)

### One-Command Deploy

```bash
# Clone repository
git clone <your-repo-url>
cd Backend-VikPay-

# Deploy with Kubernetes (automatic dependency management)
./quickstart.sh

# Or using make
make deploy
```

### Manual Kubernetes Deployment

```bash
# 1. Generate Kubernetes manifests
python3 setup.py

# 2. Deploy to cluster
./k8s-deploy.sh

# 3. Access application
kubectl port-forward service/vikpay-backend-service 8000:80 -n vikpay
```

## 🔧 What Happens During Kubernetes Deployment

The Kubernetes-native approach automatically:

- ✅ **Creates init containers** that install all Python dependencies
- ✅ **Manages ConfigMaps** for application configuration
- ✅ **Handles Secrets** for sensitive data
- ✅ **Sets up health probes** for application monitoring
- ✅ **Configures services** for network access
- ✅ **Enables auto-scaling** and self-healing

## 📦 Dependencies Automatically Managed

All dependencies from `requirements.txt` are installed automatically in Kubernetes:

| Category | Packages |
|----------|----------|
| **Web Framework** | FastAPI, Uvicorn, Starlette |
| **Database** | SQLAlchemy, psycopg2-binary |
| **Authentication** | bcrypt, PyJWT, email-validator |
| **Cloud Storage** | boto3 (AWS S3/R2 compatible) |
| **WebRTC** | aiortc |
| **Data Validation** | Pydantic |
| **Environment** | python-dotenv |

## 🚀 Available Commands

```bash
# Kubernetes Management
make setup      # Generate K8s manifests
make deploy     # Deploy to cluster
make status     # Check deployment status
make logs       # View application logs
make scale REPLICAS=3  # Scale deployment
make clean      # Delete from cluster

# Development
make local      # Local development (fallback)
make k8s-check  # Check K8s tools availability
```

## 🌐 Accessing Your Application

After deployment:

```bash
# Set up port forwarding
kubectl port-forward service/vikpay-backend-service 8000:80 -n vikpay

# Access API documentation
open http://localhost:8000/docs    # Swagger UI
open http://localhost:8000/redoc   # ReDoc
```

## 📊 Monitoring & Management

```bash
# Check pod status
kubectl get pods -n vikpay -w

# View logs
kubectl logs -l app=vikpay-backend -n vikpay -f

# Scale application
kubectl scale deployment vikpay-backend --replicas=3 -n vikpay

# Get service info
kubectl get svc vikpay-backend-service -n vikpay
```

## ⚙️ Configuration

The Kubernetes deployment uses:

- **ConfigMap**: Non-sensitive configuration
- **Secret**: Sensitive data (base64 encoded)
- **PersistentVolume**: Database storage
- **Service**: Network access
- **Deployment**: Application management

## 🔧 Local Development Fallback

If Kubernetes tools aren't available:

```bash
# Automatic fallback to local development
python3 setup.py

# Start local server
./local-dev.sh
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                       │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌─────────────────────────────────────┐ │
│  │ Init Container│  │        Main Application             │ │
│  │               │  │                                     │ │
│  │ • Install deps│  │ • VikPay Backend                    │ │
│  │ • Setup env   │  │ • FastAPI + WebRTC                  │ │
│  │ • Copy packages│  │ • Auto-scaling                      │ │
│  └───────────────┘  └─────────────────────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  Storage & Config                       │ │
│  │  • ConfigMap (app config)                               │ │
│  │  • Secret (credentials)                                 │ │
│  │  • PersistentVolume (database)                          │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Production Features

- **Auto-scaling**: Horizontal Pod Autoscaler ready
- **Health checks**: Liveness and readiness probes
- **Zero-downtime**: Rolling updates
- **Service discovery**: Kubernetes-native networking
- **Secret management**: Encrypted at rest
- **Resource limits**: CPU and memory constraints
- **Monitoring**: Ready for Prometheus/Grafana

## 🔒 Security

- Secrets stored in Kubernetes Secret objects
- Non-root container execution
- Resource limits enforced
- Network policies ready
- RBAC compatible

## 🚀 Getting Started

1. **Prerequisites**: `kubectl` and `docker` installed
2. **Deploy**: Run `./quickstart.sh` or `make deploy`
3. **Access**: `kubectl port-forward service/vikpay-backend-service 8000:80 -n vikpay`
4. **Develop**: Open http://localhost:8000/docs

---

**VikPay Backend** - Cloud-native, Kubernetes-ready, production-grade! ☸️
