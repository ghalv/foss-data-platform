"""
Unified Storage API Client for MinIO/S3 Operations
Provides programmatic access to object storage without needing the web console
"""

import boto3
import os
from typing import List, Dict, Optional, BinaryIO
import logging

logger = logging.getLogger(__name__)

class StorageAPI:
    """Unified API for MinIO/S3 storage operations"""
    
    def __init__(self, endpoint_url: str = "http://localhost:9002", 
                 access_key: str = "admin", secret_key: str = "admin123"):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='us-east-1'  # MinIO default
        )
        
    def list_buckets(self) -> List[Dict]:
        """List all buckets"""
        try:
            response = self.s3_client.list_buckets()
            return [
                {
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate'].isoformat(),
                    'size': self._get_bucket_size(bucket['Name'])
                }
                for bucket in response['Buckets']
            ]
        except Exception as e:
            logger.error(f"Error listing buckets: {e}")
            return []
    
    def create_bucket(self, bucket_name: str) -> bool:
        """Create a new bucket"""
        try:
            self.s3_client.create_bucket(Bucket=bucket_name)
            logger.info(f"Bucket {bucket_name} created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating bucket {bucket_name}: {e}")
            return False
    
    def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete a bucket"""
        try:
            if force:
                # Delete all objects first
                objects = self.list_objects(bucket_name)
                for obj in objects:
                    self.s3_client.delete_object(Bucket=bucket_name, Key=obj['key'])
            
            self.s3_client.delete_bucket(Bucket=bucket_name)
            logger.info(f"Bucket {bucket_name} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting bucket {bucket_name}: {e}")
            return False
    
    def list_objects(self, bucket_name: str, prefix: str = "") -> List[Dict]:
        """List objects in a bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix
            )
            
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"')
                })
            
            return objects
        except Exception as e:
            logger.error(f"Error listing objects in bucket {bucket_name}: {e}")
            return []
    
    def upload_file(self, bucket_name: str, object_key: str, 
                   file_path: str, content_type: str = None) -> bool:
        """Upload a file to storage"""
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
                
            self.s3_client.upload_file(
                file_path, bucket_name, object_key,
                ExtraArgs=extra_args
            )
            logger.info(f"File {file_path} uploaded to {bucket_name}/{object_key}")
            return True
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            return False
    
    def download_file(self, bucket_name: str, object_key: str, 
                     file_path: str) -> bool:
        """Download a file from storage"""
        try:
            self.s3_client.download_file(bucket_name, object_key, file_path)
            logger.info(f"File {bucket_name}/{object_key} downloaded to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading file {object_key}: {e}")
            return False
    
    def delete_object(self, bucket_name: str, object_key: str) -> bool:
        """Delete an object from storage"""
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            logger.info(f"Object {bucket_name}/{object_key} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting object {object_key}: {e}")
            return False
    
    def get_object_info(self, bucket_name: str, object_key: str) -> Optional[Dict]:
        """Get metadata for an object"""
        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
            return {
                'key': object_key,
                'size': response['ContentLength'],
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'last_modified': response['LastModified'].isoformat(),
                'etag': response['ETag'].strip('"'),
                'metadata': response.get('Metadata', {})
            }
        except Exception as e:
            logger.error(f"Error getting object info for {object_key}: {e}")
            return None
    
    def _get_bucket_size(self, bucket_name: str) -> int:
        """Calculate total size of a bucket"""
        try:
            objects = self.list_objects(bucket_name)
            return sum(obj['size'] for obj in objects)
        except:
            return 0
    
    def get_storage_stats(self) -> Dict:
        """Get overall storage statistics"""
        try:
            buckets = self.list_buckets()
            total_size = sum(bucket['size'] for bucket in buckets)
            total_objects = sum(len(self.list_objects(bucket['name'])) for bucket in buckets)
            
            return {
                'total_buckets': len(buckets),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
                'total_objects': total_objects
            }
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}

# Global storage API instance
storage_api = StorageAPI()
