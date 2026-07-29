import uuid
import boto3
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from typing import Annotated
from botocore.exceptions import ClientError
from botocore.client import BaseClient
from app.core.minio import get_s3_client
from app.core.config import settings
from app.auth.dependency import get_current_user
from app.users.models import User, UserRole

router = APIRouter(tags=["Uploads"])

ALLOWED_CONTENT_TYPES = ["application/pdf"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

@router.post("/upload/resume")
def upload_resume(
    file: Annotated[UploadFile, File(description="PDF resume file")],
    current_user: Annotated[User, Depends(get_current_user)],
    s3: BaseClient = Depends(get_s3_client)
):
    # 1. RBAC — only job seekers upload resumes
    if current_user.role != UserRole.JOB_SEEKER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only job seekers can upload resumes"
        )
    
    # 2. Validate file type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # 3. Validate file size
    file_content = file.file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must not exceed 5MB"
        )
    
    # 4. Generate unique filename
    if file.filename is None:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing."
        )
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{current_user.id}_{uuid.uuid4()}.{file_extension}"
    
    # 5. Upload to MinIO
    try:
        s3.put_object(
            Bucket=settings.MINIO_BUCKET_NAME,
            Key=unique_filename,
            Body=file_content,
            ContentType=file.content_type
        )
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    
    # 6. Return just the filename (as you decided)
    return {"filename": unique_filename}