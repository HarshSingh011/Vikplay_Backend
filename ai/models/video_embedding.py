"""
AI Models - ChromaDB and Ollama integration for video recommendations
"""
import chromadb
from chromadb.config import Settings
import ollama
from typing import List, Dict, Any, Optional, Tuple
import json
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VideoEmbeddingModel:
    """Handles video content embeddings using Ollama and ChromaDB"""
    
    def __init__(self, collection_name: str = "video_embeddings"):
        self.collection_name = collection_name
        self.chroma_client = None
        self.collection = None
        self.ollama_model = "llama3.2:3b"  # Lightweight model for embeddings
        self._initialize_chromadb()
        self._check_ollama_connection()
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client
            self.chroma_client = chromadb.Client(Settings(
                persist_directory="./chroma_db",
                anonymized_telemetry=False
            ))
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(name=self.collection_name)
                logger.info(f"Retrieved existing ChromaDB collection: {self.collection_name}")
            except Exception:
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Video content embeddings for recommendations"}
                )
                logger.info(f"Created new ChromaDB collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise
    
    def _check_ollama_connection(self):
        """Check if Ollama is running and model is available"""
        try:
            # Check if Ollama is running
            models = ollama.list()
            available_models = [model['name'] for model in models['models']]
            
            if not available_models:
                logger.warning("No Ollama models found. Please install a model first.")
                # Try to pull the default model
                logger.info(f"Pulling {self.ollama_model} model...")
                ollama.pull(self.ollama_model)
            
            if self.ollama_model not in available_models:
                logger.info(f"Model {self.ollama_model} not found. Available models: {available_models}")
                # Use the first available model or pull the default one
                if available_models:
                    self.ollama_model = available_models[0]
                    logger.info(f"Using model: {self.ollama_model}")
                else:
                    logger.info(f"Pulling {self.ollama_model} model...")
                    ollama.pull(self.ollama_model)
            
            logger.info(f"Ollama connection successful. Using model: {self.ollama_model}")
            
        except Exception as e:
            logger.error(f"Ollama connection failed: {str(e)}")
            logger.error("Please ensure Ollama is installed and running")
            raise
    
    def generate_video_description(self, video_data: Dict[str, Any]) -> str:
        """Generate enhanced description for better embeddings"""
        title = video_data.get('title', '')
        description = video_data.get('description', '')
        category = video_data.get('category', '')
        tags = video_data.get('tags', '')
        
        # Create comprehensive description
        full_description = f"Title: {title}\n"
        if description:
            full_description += f"Description: {description}\n"
        if category:
            full_description += f"Category: {category}\n"
        if tags:
            full_description += f"Tags: {tags}\n"
        
        return full_description
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Ollama"""
        try:
            response = ollama.embeddings(
                model=self.ollama_model,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            # Fallback to simple text-based features
            return self._fallback_embedding(text)
    
    def _fallback_embedding(self, text: str) -> List[float]:
        """Fallback embedding method using simple text features"""
        # Simple word-based features (not as good as proper embeddings)
        words = text.lower().split()
        word_count = len(words)
        char_count = len(text)
        
        # Create a simple 384-dimensional vector (common embedding size)
        embedding = [0.0] * 384
        
        # Fill with simple features
        if word_count > 0:
            embedding[0] = min(word_count / 100.0, 1.0)  # Normalized word count
        if char_count > 0:
            embedding[1] = min(char_count / 1000.0, 1.0)  # Normalized char count
        
        # Add some randomness based on text hash for uniqueness
        text_hash = hash(text) % 1000000
        for i in range(2, min(10, len(embedding))):
            embedding[i] = (text_hash % (i + 1)) / (i + 1) / 1000.0
        
        return embedding
    
    def add_video_embedding(self, video_id: int, video_data: Dict[str, Any]):
        """Add or update video embedding in ChromaDB"""
        try:
            description = self.generate_video_description(video_data)
            embedding = self.generate_embedding(description)
            
            # Store in ChromaDB
            self.collection.upsert(
                ids=[str(video_id)],
                embeddings=[embedding],
                documents=[description],
                metadatas=[{
                    "video_id": video_id,
                    "title": video_data.get('title', ''),
                    "category_id": video_data.get('category_id'),
                    "view_count": video_data.get('view_count', 0),
                    "created_at": video_data.get('created_at', '').isoformat() if video_data.get('created_at') else '',
                    "duration": video_data.get('duration', 0),
                    "tags": video_data.get('tags', '')
                }]
            )
            
            logger.info(f"Added/updated embedding for video {video_id}")
            
        except Exception as e:
            logger.error(f"Failed to add video embedding for video {video_id}: {str(e)}")
    
    def find_similar_videos(self, reference_video_ids: List[int], 
                          exclude_ids: List[int] = None, 
                          limit: int = 10) -> List[Tuple[int, float]]:
        """Find videos similar to reference videos"""
        try:
            if not reference_video_ids:
                return []
            
            exclude_ids = exclude_ids or []
            similar_videos = []
            
            for ref_id in reference_video_ids:
                try:
                    # Query similar videos
                    results = self.collection.query(
                        query_embeddings=None,
                        where={"video_id": ref_id},
                        n_results=1
                    )
                    
                    if results['embeddings'] and results['embeddings'][0]:
                        # Use the embedding to find similar videos
                        similar_results = self.collection.query(
                            query_embeddings=[results['embeddings'][0]],
                            n_results=limit * 2,  # Get more to filter out excluded ones
                            where={"video_id": {"$ne": ref_id}}  # Exclude the reference video itself
                        )
                        
                        for i, metadata in enumerate(similar_results['metadatas'][0]):
                            video_id = metadata['video_id']
                            distance = similar_results['distances'][0][i]
                            similarity = 1.0 - distance  # Convert distance to similarity
                            
                            if video_id not in exclude_ids and video_id != ref_id:
                                similar_videos.append((video_id, similarity))
                
                except Exception as e:
                    logger.error(f"Error finding similar videos for {ref_id}: {str(e)}")
                    continue
            
            # Sort by similarity and remove duplicates
            unique_videos = {}
            for video_id, similarity in similar_videos:
                if video_id not in unique_videos or unique_videos[video_id] < similarity:
                    unique_videos[video_id] = similarity
            
            sorted_videos = sorted(unique_videos.items(), key=lambda x: x[1], reverse=True)
            return sorted_videos[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar videos: {str(e)}")
            return []
    
    def search_videos_by_query(self, query: str, limit: int = 10, 
                              exclude_ids: List[int] = None) -> List[Tuple[int, float]]:
        """Search videos using natural language query"""
        try:
            exclude_ids = exclude_ids or []
            query_embedding = self.generate_embedding(query)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit * 2,  # Get more to filter out excluded ones
                include=['metadatas', 'distances']
            )
            
            similar_videos = []
            for i, metadata in enumerate(results['metadatas'][0]):
                video_id = metadata['video_id']
                distance = results['distances'][0][i]
                similarity = 1.0 - distance
                
                if video_id not in exclude_ids:
                    similar_videos.append((video_id, similarity))
            
            return similar_videos[:limit]
            
        except Exception as e:
            logger.error(f"Failed to search videos by query: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        try:
            count = self.collection.count()
            return {
                "total_videos": count,
                "collection_name": self.collection_name,
                "model": self.ollama_model
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {"error": str(e)}
    
    def rebuild_embeddings(self, videos_data: List[Dict[str, Any]]):
        """Rebuild all embeddings (useful for updates)"""
        logger.info("Rebuilding video embeddings...")
        
        try:
            # Clear existing collection
            self.chroma_client.delete_collection(name=self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Video content embeddings for recommendations"}
            )
            
            # Add all video embeddings
            for video_data in videos_data:
                if 'id' in video_data:
                    self.add_video_embedding(video_data['id'], video_data)
            
            logger.info(f"Successfully rebuilt embeddings for {len(videos_data)} videos")
            
        except Exception as e:
            logger.error(f"Failed to rebuild embeddings: {str(e)}")
            raise
