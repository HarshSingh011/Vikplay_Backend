import boto3
import os
import logging
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get R2 credentials from environment variables
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")

# Configuration for local fallback
LOCAL_STORAGE_PATH = "static/uploads"

# Ensure local storage directory exists
os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)

# Validate credentials are available
if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME]):
    logging.warning("Missing R2 credentials in environment variables")

# Initialize S3 client with R2 credentials
s3_client = None
r2_available = False

try:
    if all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME]):
        s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name='auto'
        )
        
        # Test connection to R2
        try:
            s3_client.head_bucket(Bucket=R2_BUCKET_NAME)
            r2_available = True
            logging.info("Successfully connected to R2 storage")
        except Exception as e:
            logging.warning(f"R2 bucket not accessible: {e}. Will use local storage fallback.")
            r2_available = False
    else:
        logging.warning("R2 credentials not configured. Using local storage.")
        
except Exception as e:
    logging.error(f"Failed to initialize R2 client: {e}. Using local storage fallback.")
    s3_client = None
    r2_available = False

async def upload_file_to_r2(file, filename, content_type):
    """Upload a file to R2 storage or local storage as fallback"""
    
    # Try R2 first if available
    if s3_client and r2_available:
        try:
            file_content = await file.read()
            
            s3_client.put_object(
                Bucket=R2_BUCKET_NAME,
                Key=filename,
                Body=file_content,
                ContentType=content_type
            )
            
            # Return the R2 URL
            file_url = f"https://{R2_BUCKET_NAME}.{R2_ACCOUNT_ID}.r2.dev/{filename}"
            logging.info(f"Successfully uploaded to R2: {filename}")
            return file_url
            
        except Exception as e:
            logging.error(f"R2 upload failed: {e}. Falling back to local storage.")
    
    # Fallback to local storage
    try:
        # Reset file pointer for local save
        await file.seek(0)
        file_content = await file.read()
        
        # Create local file path
        local_file_path = os.path.join(LOCAL_STORAGE_PATH, filename)
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        
        # Save file locally
        with open(local_file_path, 'wb') as f:
            f.write(file_content)
        
        # Return local URL
        file_url = f"/static/uploads/{filename}"
        logging.info(f"Successfully saved locally: {filename}")
        return file_url
        
    except Exception as e:
        logging.error(f"Local storage also failed: {e}")
        raise Exception(f"Failed to upload file: {e}")

async def cleanup_incomplete_uploads(filename):
    """Delete an incomplete upload from R2 or local storage"""
    
    # Try to clean up from R2 first
    if s3_client and r2_available:
        try:
            s3_client.delete_object(
                Bucket=R2_BUCKET_NAME,
                Key=filename
            )
            logging.info(f"Cleaned up R2 file: {filename}")
            return
        except Exception as e:
            logging.error(f"Error cleaning up R2 file: {e}")
    
    # Clean up from local storage
    try:
        local_file_path = os.path.join(LOCAL_STORAGE_PATH, filename)
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            logging.info(f"Cleaned up local file: {filename}")
    except Exception as e:
        logging.error(f"Error cleaning up local file: {e}")

def test_r2_connection():
    """Test R2 connection and return status"""
    if not s3_client:
        return {"status": "error", "message": "R2 client not initialized"}
    
    try:
        s3_client.head_bucket(Bucket=R2_BUCKET_NAME)
        return {"status": "success", "message": "R2 connection successful"}
    except Exception as e:
        return {"status": "error", "message": f"R2 connection failed: {e}"}