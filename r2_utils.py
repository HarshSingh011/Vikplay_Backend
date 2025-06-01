import boto3
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", f"https://{R2_BUCKET_NAME}.{R2_ACCOUNT_ID}.r2.cloudflarestorage.com")

s3_client = boto3.client(
    's3',
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto" 
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
        
        url = f"{R2_PUBLIC_URL}/{filename}"
        return url
    
    except ClientError as e:
        print(f"Error uploading to R2: {e}")
        raise
    finally:
        await file.seek(0)

async def cleanup_incomplete_uploads():
    """Clean up incomplete multipart uploads in the R2 bucket"""
    try:
        # List all multipart uploads
        response = s3_client.list_multipart_uploads(
            Bucket=R2_BUCKET_NAME
        )
        
        cleaned = 0
        # Abort each multipart upload
        if 'Uploads' in response:
            for upload in response['Uploads']:
                s3_client.abort_multipart_upload(
                    Bucket=R2_BUCKET_NAME,
                    Key=upload['Key'],
                    UploadId=upload['UploadId']
                )
                cleaned += 1
                print(f"Aborted multipart upload: {upload['Key']}")
        
        return {"message": f"Cleaned up {cleaned} incomplete uploads"}
    
    except Exception as e:
        print(f"Error cleaning up bucket: {e}")
        raise e
