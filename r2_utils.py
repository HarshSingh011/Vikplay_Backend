import boto3
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get R2 credentials from environment variables
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")

# Validate credentials are available
if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME]):
    logging.warning("Missing R2 credentials in environment variables")

# Initialize S3 client with R2 credentials
try:
    s3_client = boto3.client(
        's3',
        endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY
    )
    logging.info("Successfully initialized R2 client")
except Exception as e:
    logging.error(f"Failed to initialize R2 client: {e}")
    s3_client = None

async def upload_file_to_r2(file, filename, content_type):
    """Upload a file to R2 storage"""
    if not s3_client:
        raise Exception("R2 client not initialized. Check your credentials.")
        
    try:
        file_content = await file.read()
        
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=filename,
            Body=file_content,
            ContentType=content_type
        )
        
        # Return the URL to the uploaded file
        return f"https://{R2_BUCKET_NAME}.{R2_ACCOUNT_ID}.r2.dev/{filename}"
    except Exception as e:
        logging.error(f"Error uploading file to R2: {e}")
        raise Exception(f"Failed to upload file to R2: {e}")

async def cleanup_incomplete_uploads(filename):
    """Delete an incomplete upload from R2"""
    if not s3_client:
        return
        
    try:
        s3_client.delete_object(
            Bucket=R2_BUCKET_NAME,
            Key=filename
        )
    except Exception as e:
        logging.error(f"Error cleaning up incomplete upload: {e}")