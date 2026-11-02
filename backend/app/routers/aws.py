"""
AWS integration endpoints
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.services.aws_service import AWSService

# Create router
router = APIRouter(
    prefix="/api/aws",
    tags=["AWS Integration"]
)


class AWSConnectionTest(BaseModel):
    """Schema for AWS connection test request"""
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    region: str = "us-east-1"


@router.post("/test-connection")
async def test_aws_connection(credentials: AWSConnectionTest):
    """
    Test AWS connection with provided credentials
    
    If credentials are not provided, will attempt to use environment variables or IAM role.
    """
    aws_service = AWSService(
        access_key_id=credentials.access_key_id,
        secret_access_key=credentials.secret_access_key,
        region=credentials.region
    )
    
    result = aws_service.test_connection()
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"AWS connection failed: {result.get('error')}"
        )
    
    return result


@router.post("/account-summary")
async def get_aws_account_summary(credentials: AWSConnectionTest):
    """
    Get AWS account resource summary
    """
    aws_service = AWSService(
        access_key_id=credentials.access_key_id,
        secret_access_key=credentials.secret_access_key,
        region=credentials.region
    )
    
    result = aws_service.get_account_summary()
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account summary: {result.get('error')}"
        )
    
    return result


@router.get("/ec2-instances")
async def list_ec2_instances(region: str = "us-east-1"):
    """
    List EC2 instances (uses environment credentials)
    """
    aws_service = AWSService(region=region)
    instances = aws_service.list_ec2_instances()
    
    return {
        "count": len(instances),
        "instances": instances
    }


@router.get("/s3-buckets")
async def list_s3_buckets():
    """
    List S3 buckets (uses environment credentials)
    """
    aws_service = AWSService()
    buckets = aws_service.list_s3_buckets()
    
    return {
        "count": len(buckets),
        "buckets": buckets
    }
