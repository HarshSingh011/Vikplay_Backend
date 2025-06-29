"""
Test script for AI Recommendation System
This script tests the basic AI functionality without requiring a full server setup
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if all AI modules can be imported"""
    print("🧪 Testing AI module imports...")
    
    try:
        import ollama
        print("✅ Ollama imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ollama: {e}")
        return False
    
    try:
        import chromadb
        print("✅ ChromaDB imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import chromadb: {e}")
        return False
    
    try:
        import numpy
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import numpy: {e}")
        return False
    
    try:
        from ai.models.video_embedding import VideoEmbeddingModel
        print("✅ VideoEmbeddingModel imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import VideoEmbeddingModel: {e}")
        return False
    
    return True

def test_chromadb():
    """Test ChromaDB functionality"""
    print("\n🗃️ Testing ChromaDB...")
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Initialize ChromaDB client
        client = chromadb.Client(Settings(
            persist_directory="./test_chroma_db",
            anonymized_telemetry=False
        ))
        
        # Create a test collection
        collection = client.create_collection(
            name="test_collection",
            metadata={"description": "Test collection"}
        )
        
        # Add a test document
        collection.add(
            documents=["This is a test document"],
            metadatas=[{"source": "test"}],
            ids=["test_1"]
        )
        
        # Query the collection
        results = collection.query(
            query_texts=["test document"],
            n_results=1
        )
        
        if results['documents']:
            print("✅ ChromaDB test successful")
            
            # Clean up
            client.delete_collection(name="test_collection")
            return True
        else:
            print("❌ ChromaDB test failed: No results returned")
            return False
            
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        return False

def test_ollama_connection():
    """Test Ollama connection (requires Ollama to be running)"""
    print("\n🤖 Testing Ollama connection...")
    
    try:
        import ollama
        
        # Try to list models
        models = ollama.list()
        print(f"✅ Ollama connected. Available models: {len(models.get('models', []))}")
        
        # Check if our preferred model is available
        model_names = [model['name'] for model in models.get('models', [])]
        if 'llama3.2:3b' in model_names:
            print("✅ Preferred model (llama3.2:3b) is available")
        else:
            print("⚠️ Preferred model (llama3.2:3b) not found")
            print(f"Available models: {model_names}")
            
        return True
        
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        print("💡 Please ensure Ollama is installed and running:")
        print("   1. Install Ollama from https://ollama.ai/download")
        print("   2. Run: ollama serve")
        print("   3. Run: ollama pull llama3.2:3b")
        return False

def test_video_embedding_model():
    """Test the VideoEmbeddingModel class"""
    print("\n🧠 Testing VideoEmbeddingModel...")
    
    try:
        from ai.models.video_embedding import VideoEmbeddingModel
        
        # Initialize the model (this will create ChromaDB collection)
        model = VideoEmbeddingModel(collection_name="test_video_embeddings")
        
        # Test adding a video embedding
        test_video_data = {
            "id": 1,
            "title": "Test Video",
            "description": "This is a test video about AI",
            "category": "Technology",
            "tags": "AI, machine learning, test",
            "view_count": 100,
            "duration": 300,
            "created_at": "2024-01-01T00:00:00"
        }
        
        model.add_video_embedding(1, test_video_data)
        print("✅ Video embedding added successfully")
        
        # Test finding similar videos
        similar_videos = model.find_similar_videos([1], limit=5)
        print(f"✅ Similar videos search completed. Found: {len(similar_videos)} results")
        
        # Test search by query
        search_results = model.search_videos_by_query("AI technology", limit=5)
        print(f"✅ Search by query completed. Found: {len(search_results)} results")
        
        # Get collection stats
        stats = model.get_collection_stats()
        print(f"✅ Collection stats: {stats}")
        
        # Clean up
        model.chroma_client.delete_collection(name="test_video_embeddings")
        
        return True
        
    except Exception as e:
        print(f"❌ VideoEmbeddingModel test failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    import shutil
    
    test_dirs = ["./test_chroma_db", "./chroma_db"]
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            try:
                shutil.rmtree(test_dir)
                print(f"🧹 Cleaned up {test_dir}")
            except Exception as e:
                print(f"⚠️ Could not clean up {test_dir}: {e}")

def main():
    """Run all tests"""
    print("🚀 Testing VikPay AI Recommendation System")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("ChromaDB Tests", test_chromadb),
        ("Ollama Connection", test_ollama_connection),
        ("VideoEmbeddingModel Tests", test_video_embedding_model),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your AI system is ready to use.")
        print("\n📋 Next steps:")
        print("   1. Start Ollama: ollama serve")
        print("   2. Pull model: ollama pull llama3.2:3b")
        print("   3. Start FastAPI: python main.py")
        print("   4. Test API: http://localhost:8000/api/ai/health")
    else:
        print("⚠️ Some tests failed. Please fix the issues above.")
    
    # Clean up test files
    cleanup_test_files()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
