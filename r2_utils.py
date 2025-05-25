import boto3
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

# R2 Configuration
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", f"https://{R2_BUCKET_NAME}.{R2_ACCOUNT_ID}.r2.cloudflarestorage.com")

# Initialize R2 client (using S3-compatible API)
s3_client = boto3.client(
    's3',
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto"  # R2 doesn't use regions, but boto3 requires this
)

async def upload_file_to_r2(file, filename, content_type):
    """
    Upload a file to Cloudflare R2 bucket
    """
    try:
        file_content = await file.read()
        
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=filename,
            Body=file_content,
            ContentType=content_type
        )
        
        # Generate the URL
        url = f"{R2_PUBLIC_URL}/{filename}"
        return url
    
    except ClientError as e:
        print(f"Error uploading to R2: {e}")
        raise
    finally:
        await file.seek(0)