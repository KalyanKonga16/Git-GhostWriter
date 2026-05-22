import boto3
import uuid
from config import *

s3 = boto3.client(
    service_name='s3',
    endpoint_url = R2_ENDPOINT,
    aws_access_key_id = R2_ACCESS_KEY,
    aws_secret_access_key = R2_SECRET_KEY,
    region_name = 'auto'
)

def upload_docs(github_url, files):
    job_id = str(uuid.uuid4())[:12]
    
    for path, content in files.items():
        s3.put_object(
            Bucket=R2_BUCKET,
            Key=f"{job_id}/{path}",
            Body=content,
            ContentType='text/markdown',
            CacheControl='public, max-age=31536000'
        )
    
    return f"{R2_PUBLIC_DOMAIN}/{job_id}/README.md"