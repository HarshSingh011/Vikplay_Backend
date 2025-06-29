@echo off
REM Force Merge Script for VikPay Backend (Windows)
echo 🚀 Force Merging Current Code to Main Branch
echo ============================================

REM Get current branch name
for /f %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
echo 📍 Current branch: %CURRENT_BRANCH%

REM Step 1: Commit all current changes
echo 📦 Committing all current changes...
git add -A
git commit -m "Complete AI recommendation system with modular architecture

Features added:
- AI-powered video recommendations using Ollama + ChromaDB
- Content-based filtering with video embeddings  
- Collaborative filtering based on user behavior
- Category-based recommendations
- Natural language search for videos
- Comprehensive user history tracking (watch time, ratings, likes)
- User preferences management
- Modular video management system
- Enhanced database models
- Full API documentation
- Health checks and monitoring
- Backward compatibility maintained

Tech stack:
- FastAPI + SQLAlchemy + Pydantic
- Ollama (llama3.2:3b) for AI processing
- ChromaDB for vector storage and similarity search
- Clean modular architecture with separation of concerns"

echo ✅ Changes committed

REM Step 2: Checkout main branch
echo 🔄 Switching to main branch...
git checkout main

REM Step 3: Reset main to current branch (force merge)
echo ⚡ Force merging %CURRENT_BRANCH% into main...
git reset --hard %CURRENT_BRANCH%

REM Step 4: Force push to remote
echo 🚀 Force pushing to remote main...
git push origin main --force

echo.
echo 🎉 Force merge completed successfully!
echo 📋 Summary:
echo    ✅ All changes from %CURRENT_BRANCH% are now in main
echo    ✅ Remote main branch updated
echo    ✅ Your AI recommendation system is live
echo.
echo 🧪 Test your deployment:
echo    1. python main.py
echo    2. curl http://localhost:8000/health
echo    3. curl http://localhost:8000/api/ai/health
echo    4. Visit http://localhost:8000/docs for API documentation
echo.
pause
