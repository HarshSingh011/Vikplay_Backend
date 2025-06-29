@echo off
REM Git Merge Conflict Resolution Script for VikPay Backend (Windows)
echo 🔧 Resolving Git Merge Conflicts for VikPay Backend
echo =================================================

REM Step 1: Check current status
echo 📊 Current Git Status:
git status

echo.
echo 🔧 Resolving conflicts...

REM Resolve main.py conflict (use current working version)
git add main.py
echo ✅ main.py conflict resolved

REM Resolve models/models.py conflict (use enhanced version)
git add models/models.py
echo ✅ models/models.py conflict resolved

REM Add video module files
git add video/
echo ✅ video module files added

REM Clean up cache files from Git tracking
git rm --cached models/__pycache__/models.cpython-313.pyc 2>nul
git rm --cached video/__pycache__/__init__.cpython-313.pyc 2>nul
git rm --cached video/repositories/__pycache__/__init__.cpython-313.pyc 2>nul

REM Remove cache directories
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

echo 🧹 Cache files cleaned

REM Complete the merge
echo 📦 Completing merge...
git commit -m "Resolve merge conflicts: integrate AI recommendation system

- Merge enhanced main.py with modular video and AI systems  
- Keep user history models in models/models.py
- Preserve video module structure
- Clean up cache files from tracking"

echo.
echo 🎉 Merge conflicts resolved successfully!
echo 📋 Next steps:
echo    1. Test the application: python main.py
echo    2. Check health: curl http://localhost:8000/health  
echo    3. Verify AI system: curl http://localhost:8000/api/ai/health
echo.
pause
