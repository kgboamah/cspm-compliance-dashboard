"""
AWS service wrapper using Boto3
"""
import boto3
from typing import List, Dict, Optional
from botocore.exceptions import ClientError, BotoCoreError
import logging

logger = logging.getLogger(__name__)


class AWSService:
    """
    Wrapper for AWS Boto3 operations
    """
    
    def __init__(self, access_key_id: str = None, secret_access_key: str = None, region: str = "us-east-1"):
        """
        Initialize AWS service
        
        Args:
            access_key_id: AWS Access Key ID (optional, uses environment if not provided)
            secret_access_key: AWS Secret Access Key (optional, uses environment if not provided)
            region: AWS region
        """
        self.region = region
        
        # Create session
        if access_key_id and secret_access_key:
            self.session = boto3.Session(
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region
            )
        else:
            # Use environment variables or IAM role
            self.session = boto3.Session(region_name=region)
    
    def test_connection(self) -> Dict:
        """
        Test AWS connection by getting caller identity
        
        Returns:
            Dict with account info if successful
        """
        try:
            sts = self.session.client('sts')
            response = sts.get_caller_identity()
            
            return {
                "success": True,
                "account_id": response.get('Account'),
                "user_id": response.get('UserId'),
                "arn": response.get('Arn'),
            }
        except (ClientError, BotoCoreError) as e:
            logger.error(f"AWS connection test failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_ec2_instances(self) -> List[Dict]:
        """
        List all EC2 instances in the region
        
        Returns:
            List of instance information
        """
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_instances()
            
            instances = []
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instances.append({
                        'instance_id': instance.get('InstanceId'),
                        'instance_type': instance.get('InstanceType'),
                        'state': instance.get('State', {}).get('Name'),
                        'launch_time': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None,
                    })
            
            return instances
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to list EC2 instances: {str(e)}")
            return []
    
    def list_s3_buckets(self) -> List[Dict]:
        """
        List all S3 buckets
        
        Returns:
            List of bucket information
        """
        try:
            s3 = self.session.client('s3')
            response = s3.list_buckets()
            
            buckets = []
            for bucket in response.get('Buckets', []):
                buckets.append({
                    'name': bucket.get('Name'),
                    'creation_date': bucket.get('CreationDate').isoformat() if bucket.get('CreationDate') else None,
                })
            
            return buckets
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to list S3 buckets: {str(e)}")
            return []
    
    def get_account_summary(self) -> Dict:
        """
        Get AWS account resource summary
        
        Returns:
            Dictionary with counts of various resources
        """
        try:
            # Get EC2 instances
            ec2_instances = self.list_ec2_instances()
            
            # Get S3 buckets
            s3_buckets = self.list_s3_buckets()
            
            # Get IAM summary
            iam = self.session.client('iam')
            iam_summary = iam.get_account_summary()
            
            return {
                "success": True,
                "ec2_instances": len(ec2_instances),
                "s3_buckets": len(s3_buckets),
                "iam_users": iam_summary.get('SummaryMap', {}).get('Users', 0),
                "iam_groups": iam_summary.get('SummaryMap', {}).get('Groups', 0),
                "iam_roles": iam_summary.get('SummaryMap', {}).get('Roles', 0),
            }
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get account summary: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
