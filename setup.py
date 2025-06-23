#!/usr/bin/env python3
"""
VikPay Backend - Kubernetes Native Setup
Pure Kubernetes approach for dependency management and deployment
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class KubernetesNativeSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.k8s_namespace = "vikpay"
        self.app_name = "vikpay-backend"
#!/usr/bin/env python3
"""
VikPay Backend - Kubernetes Native Setup
Pure Kubernetes approach for dependency management and deployment
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class KubernetesNativeSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.k8s_namespace = "vikpay"
        self.app_name = "vikpay-backend"
        
    def print_banner(self):
        print("""
╔══════════════════════════════════════════════════════════════╗
║             VikPay Backend - Kubernetes Native              ║
║           Cloud-Native Dependency Management                 ║
╚══════════════════════════════════════════════════════════════╝
        """)
    
    def check_kubernetes_tools(self):
        """Check if Kubernetes tools are available"""
        print("🔍 Checking Kubernetes environment...")
        
        tools = {
            'docker': 'Docker is required for building container images',
            'kubectl': 'kubectl is required for Kubernetes deployment'
        }
        
        missing_tools = []
        for tool, description in tools.items():
            try:
                subprocess.run([tool, '--version'], 
                             check=True, capture_output=True, text=True)
                print(f"✅ {tool} is available")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"❌ {tool} not found - {description}")
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"\n⚠️  Missing tools: {', '.join(missing_tools)}")
            print("Installing with local Python environment as fallback...")
            return False
        return True
    
    def create_kubernetes_manifests(self):
        """Generate Kubernetes manifests with dependency management"""
        print("📝 Creating Kubernetes manifests...")
        
        # ConfigMap for application configuration
        configmap = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': f'{self.app_name}-config',
                'namespace': self.k8s_namespace
            },
            'data': {
                'DATABASE_URL': 'sqlite:///./data/vidplay.db',
                'SECRET_KEY': 'kubernetes-managed-secret-key',
                'ALGORITHM': 'HS256',
                'ACCESS_TOKEN_EXPIRE_MINUTES': '30',
                'SMTP_SERVER': 'smtp.gmail.com',
                'SMTP_PORT': '587'
            }
        }
        
        # Secret for sensitive data
        secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': f'{self.app_name}-secrets',
                'namespace': self.k8s_namespace
            },
            'type': 'Opaque',
            'data': {
                'email-username': 'eW91cl9lbWFpbEBnbWFpbC5jb20=',  # base64: your_email@gmail.com
                'email-password': 'eW91cl9hcHBfcGFzc3dvcmQ=',      # base64: your_app_password
                'r2-access-key': 'eW91cl9hY2Nlc3Nfa2V5',           # base64: your_access_key
                'r2-secret-key': 'eW91cl9zZWNyZXRfa2V5'            # base64: your_secret_key
            }
        }
        
        # Init Container for dependency installation
        init_container = {
            'name': 'dependency-installer',
            'image': 'python:3.11-slim',
            'command': ['sh', '-c'],
            'args': ['''
                echo "🔧 Installing dependencies in Kubernetes..."
                pip install --no-cache-dir -r /app/requirements.txt
                echo "✅ Dependencies installed successfully"
                cp -r /usr/local/lib/python3.11/site-packages/* /shared/site-packages/
            '''],
            'volumeMounts': [
                {'name': 'app-source', 'mountPath': '/app'},
                {'name': 'shared-deps', 'mountPath': '/shared'}
            ]
        }
        
        # Main application deployment
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': self.app_name,
                'namespace': self.k8s_namespace,
                'labels': {'app': self.app_name}
            },
            'spec': {
                'replicas': 1,
                'selector': {'matchLabels': {'app': self.app_name}},
                'template': {
                    'metadata': {'labels': {'app': self.app_name}},
                    'spec': {
                        'initContainers': [init_container],
                        'containers': [{
                            'name': self.app_name,
                            'image': 'python:3.11-slim',
                            'command': ['sh', '-c'],
                            'args': ['''
                                export PYTHONPATH="/shared/site-packages:$PYTHONPATH"
                                cd /app
                                python -m uvicorn main:app --host 0.0.0.0 --port 8000
                            '''],
                            'ports': [{'containerPort': 8000}],
                            'env': [
                                {'name': 'DATABASE_URL', 'valueFrom': {'configMapKeyRef': {'name': f'{self.app_name}-config', 'key': 'DATABASE_URL'}}},
                                {'name': 'SECRET_KEY', 'valueFrom': {'configMapKeyRef': {'name': f'{self.app_name}-config', 'key': 'SECRET_KEY'}}},
                                {'name': 'EMAIL_USERNAME', 'valueFrom': {'secretKeyRef': {'name': f'{self.app_name}-secrets', 'key': 'email-username'}}},
                                {'name': 'EMAIL_PASSWORD', 'valueFrom': {'secretKeyRef': {'name': f'{self.app_name}-secrets', 'key': 'email-password'}}}
                            ],
                            'volumeMounts': [
                                {'name': 'app-source', 'mountPath': '/app'},
                                {'name': 'shared-deps', 'mountPath': '/shared'},
                                {'name': 'app-data', 'mountPath': '/app/data'}
                            ],
                            'livenessProbe': {
                                'httpGet': {'path': '/docs', 'port': 8000},
                                'initialDelaySeconds': 30,
                                'periodSeconds': 10
                            },
                            'readinessProbe': {
                                'httpGet': {'path': '/docs', 'port': 8000},
                                'initialDelaySeconds': 5,
                                'periodSeconds': 5
                            }
                        }],
                        'volumes': [
                            {'name': 'app-source', 'hostPath': {'path': str(self.project_root)}},
                            {'name': 'shared-deps', 'emptyDir': {}},
                            {'name': 'app-data', 'emptyDir': {}}
                        ]
                    }
                }
            }
        }
        
        # Service for external access
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f'{self.app_name}-service',
                'namespace': self.k8s_namespace
            },
            'spec': {
                'selector': {'app': self.app_name},
                'ports': [{'protocol': 'TCP', 'port': 80, 'targetPort': 8000}],
                'type': 'LoadBalancer'
            }
        }
        
        # Save manifests
        manifests_dir = self.project_root / 'k8s'
        manifests_dir.mkdir(exist_ok=True)
        
        manifest_files = {
            'namespace.yaml': {'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': self.k8s_namespace}},
            'configmap.yaml': configmap,
            'secret.yaml': secret,
            'deployment.yaml': deployment,
            'service.yaml': service
        }
        
        for filename, manifest in manifest_files.items():
            with open(manifests_dir / filename, 'w') as f:
                f.write('# Auto-generated Kubernetes manifest\n')
                f.write('# Dependencies are automatically managed by init containers\n')
                f.write('---\n')
                f.write(json.dumps(manifest, indent=2))
        
        print(f"✅ Kubernetes manifests created in {manifests_dir}/")
        return manifests_dir
    
    def create_deployment_script(self):
        """Create Kubernetes deployment script"""
        print("🚀 Creating deployment automation...")
        
        deploy_script = f'''#!/bin/bash
# VikPay Backend - Kubernetes Native Deployment
# This script handles everything automatically

set -e

echo "🚀 VikPay Backend - Kubernetes Native Deployment"
echo "================================================"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    echo "   https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

echo "✅ kubectl found"

# Create namespace
echo "📦 Creating namespace..."
kubectl create namespace {self.k8s_namespace} --dry-run=client -o yaml | kubectl apply -f -

# Apply all manifests
echo "📝 Applying Kubernetes manifests..."
kubectl apply -f k8s/ -n {self.k8s_namespace}

# Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/{self.app_name} -n {self.k8s_namespace}

# Get service info
echo "🌐 Getting service information..."
kubectl get service {self.app_name}-service -n {self.k8s_namespace}

echo ""
echo "🎉 VikPay Backend deployed successfully!"
echo ""
echo "Access your application:"
echo "• Local: kubectl port-forward service/{self.app_name}-service 8000:80 -n {self.k8s_namespace}"
echo "• Then visit: http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "• Check pods: kubectl get pods -n {self.k8s_namespace}"
echo "• View logs: kubectl logs -l app={self.app_name} -n {self.k8s_namespace} -f"
echo "• Delete deployment: kubectl delete namespace {self.k8s_namespace}"
'''
        
        script_path = self.project_root / 'k8s-deploy.sh'
        with open(script_path, 'w') as f:
            f.write(deploy_script)
        
        # Make executable
        os.chmod(script_path, 0o755)
        print(f"✅ Deployment script created: {script_path}")
        return script_path
    
    def create_local_fallback(self):
        """Create local development fallback if K8s not available"""
        print("🔧 Creating local development fallback...")
        
        local_script = '''#!/bin/bash
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
'''
        
        script_path = self.project_root / 'local-dev.sh'
        with open(script_path, 'w') as f:
            f.write(local_script)
        
        os.chmod(script_path, 0o755)
        print(f"✅ Local fallback script created: {script_path}")
    
    def display_completion_message(self, has_k8s_tools):
        """Display completion message with deployment options"""
        if has_k8s_tools:
            print("""
╔══════════════════════════════════════════════════════════════╗
║               🎉 Kubernetes Setup Complete! 🎉              ║
╚══════════════════════════════════════════════════════════════╝

🚀 KUBERNETES-NATIVE DEPLOYMENT:

1. Deploy to Kubernetes (Automatic dependency management):
   ./k8s-deploy.sh

2. Access your application:
   kubectl port-forward service/vikpay-backend-service 8000:80 -n vikpay
   Open: http://localhost:8000/docs

3. Monitor deployment:
   kubectl get pods -n vikpay -w
   kubectl logs -l app=vikpay-backend -n vikpay -f

4. Scale your application:
   kubectl scale deployment vikpay-backend --replicas=3 -n vikpay

5. Clean up:
   kubectl delete namespace vikpay

╔══════════════════════════════════════════════════════════════╗
║ Dependencies are automatically managed by Kubernetes! 🎯    ║
╚══════════════════════════════════════════════════════════════╝
            """)
        else:
            print("""
╔══════════════════════════════════════════════════════════════╗
║            🔧 Local Development Setup Complete! 🔧          ║
╚══════════════════════════════════════════════════════════════╝

📝 Kubernetes tools not available. Using local development:

1. Start local development:
   ./local-dev.sh

2. Or manual activation:
   source .venv/bin/activate
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

3. Install Kubernetes tools for cloud-native deployment:
   • Docker: https://docs.docker.com/get-docker/
   • kubectl: https://kubernetes.io/docs/tasks/tools/

4. Then re-run: python3 setup.py

╔══════════════════════════════════════════════════════════════╗
║ For production, use Kubernetes-native deployment! ☸️        ║
╚══════════════════════════════════════════════════════════════╝
            """)
    
    def run(self):
        """Run Kubernetes-native setup"""
        self.print_banner()
        
        has_k8s_tools = self.check_kubernetes_tools()
        
        if has_k8s_tools:
            print("🎯 Setting up Kubernetes-native deployment...")
            self.create_kubernetes_manifests()
            self.create_deployment_script()
        else:
            print("🔧 Setting up local development fallback...")
            self.create_local_fallback()
        
        self.display_completion_message(has_k8s_tools)

if __name__ == "__main__":
    setup = KubernetesNativeSetup()
    try:
        setup.run()
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)
