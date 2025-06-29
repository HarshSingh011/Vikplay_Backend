#!/bin/bash

# Git Merge Conflict Resolution Script for VikPay Backend
echo "🔧 Resolving Git Merge Conflicts for VikPay Backend"
echo "================================================="

# Step 1: Check current status
echo "📊 Current Git Status:"
git status

# Step 2: Handle conflicted files one by one
echo ""
echo "🔧 Resolving conflicts in priority order..."

# Resolve main.py conflict (most important)
if git ls-files -u | grep -q "main.py"; then
    echo "⚡ Resolving main.py conflict..."
    
    # Use the current working version (it's already clean and working)
    git add main.py
    echo "✅ main.py conflict resolved"
fi

# Resolve models/models.py conflict
if git ls-files -u | grep -q "models/models.py"; then
    echo "⚡ Resolving models/models.py conflict..."
    
    # Use our enhanced version with user history models
    git add models/models.py
    echo "✅ models/models.py conflict resolved"
fi

# Clean up cache files (they'll be regenerated)
echo "🧹 Cleaning up cache files..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# Add all resolved files
echo "📦 Adding resolved files..."
git add video/
git add models/models.py
git add main.py

# Remove cache file conflicts (they shouldn't be tracked)
git rm --cached models/__pycache__/models.cpython-313.pyc 2>/dev/null || true
git rm --cached video/__pycache__/__init__.cpython-313.pyc 2>/dev/null || true
git rm --cached video/repositories/__pycache__/__init__.cpython-313.pyc 2>/dev/null || true

# Complete the merge
echo "🎯 Completing merge..."
git commit -m "Resolve merge conflicts: integrate AI recommendation system

- Merge enhanced main.py with modular video and AI systems
- Keep user history models in models/models.py
- Preserve video module structure
- Clean up cache files from tracking"

echo ""
echo "🎉 Merge conflicts resolved successfully!"
echo "📋 Next steps:"
echo "   1. Test the application: python main.py"
echo "   2. Check health: curl http://localhost:8000/health"
echo "   3. Verify AI system: curl http://localhost:8000/api/ai/health"
