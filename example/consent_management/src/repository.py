"""
Repository Layer for Consent Management

Handles all database operations for consent records.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from botocore.exceptions import ClientError

from models import ConsentRecord, ConsentType


class ConsentRepository:
    """
    Repository for managing consent records in DynamoDB.
    
    Provides CRUD operations with proper error handling and
    optimistic locking for concurrent updates.
    """
    
    def __init__(self, table):
        """
        Initialize repository with DynamoDB table.
        
        Args:
            table: boto3 DynamoDB Table resource
        """
        self.table = table
    
    def save(self, record: ConsentRecord) -> ConsentRecord:
        """
        Save a consent record to the database.
        
        Uses conditional write for optimistic locking.
        
        Args:
            record: ConsentRecord to save
            
        Returns:
            Updated ConsentRecord with new version
            
        Raises:
            ConflictError: If version conflict occurs
        """
        record.updated_at = datetime.utcnow()
        
        item = {
            'user_id': record.user_id,
            'consent_type': record.consent_type.value if isinstance(record.consent_type, ConsentType) else record.consent_type,
            'granted': record.granted,
            'source': record.source,
            'created_at': record.created_at.isoformat(),
            'updated_at': record.updated_at.isoformat(),
            'version': record.version + 1,
        }
        
        if record.ip_address:
            item['ip_address'] = record.ip_address
        
        try:
            # Use conditional write for optimistic locking
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(version) OR version = :v',
                ExpressionAttributeValues={':v': record.version}
            )
            record.version += 1
            return record
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ConflictError(f"Version conflict for {record.user_id}:{record.consent_type}")
            raise
    
    def get(self, user_id: str, consent_type: str) -> Optional[ConsentRecord]:
        """
        Get a specific consent record.
        
        Args:
            user_id: User identifier
            consent_type: Type of consent to retrieve
            
        Returns:
            ConsentRecord if found, None otherwise
        """
        try:
            response = self.table.get_item(
                Key={
                    'user_id': user_id,
                    'consent_type': consent_type
                }
            )
            
            item = response.get('Item')
            if item:
                return ConsentRecord.from_dict(item)
            return None
            
        except ClientError as e:
            print(f"Error getting consent: {e}")
            raise
    
    def get_all_for_user(self, user_id: str) -> List[ConsentRecord]:
        """
        Get all consent records for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of ConsentRecord objects
        """
        try:
            response = self.table.query(
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id}
            )
            
            records = []
            for item in response.get('Items', []):
                records.append(ConsentRecord.from_dict(item))
            
            return records
            
        except ClientError as e:
            print(f"Error querying consents: {e}")
            raise
    
    def delete(self, user_id: str, consent_type: str) -> bool:
        """
        Delete a consent record.
        
        Note: In practice, you should never delete consent records
        for audit purposes. Instead, set granted=False.
        
        Args:
            user_id: User identifier
            consent_type: Type of consent to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            self.table.delete_item(
                Key={
                    'user_id': user_id,
                    'consent_type': consent_type
                },
                ConditionExpression='attribute_exists(user_id)'
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return False
            raise
    
    def get_by_consent_type(
        self, 
        consent_type: str, 
        granted: Optional[bool] = None,
        limit: int = 100
    ) -> List[ConsentRecord]:
        """
        Get all records of a specific consent type.
        
        Uses GSI: consent-type-index
        
        Args:
            consent_type: Type of consent to query
            granted: Optional filter for granted status
            limit: Maximum records to return
            
        Returns:
            List of ConsentRecord objects
        """
        try:
            query_params = {
                'IndexName': 'consent-type-index',
                'KeyConditionExpression': 'consent_type = :ct',
                'ExpressionAttributeValues': {':ct': consent_type},
                'Limit': limit
            }
            
            if granted is not None:
                query_params['FilterExpression'] = 'granted = :g'
                query_params['ExpressionAttributeValues'][':g'] = granted
            
            response = self.table.query(**query_params)
            
            records = []
            for item in response.get('Items', []):
                records.append(ConsentRecord.from_dict(item))
            
            return records
            
        except ClientError as e:
            print(f"Error querying by consent type: {e}")
            raise
    
    def batch_get(self, keys: List[Dict[str, str]]) -> List[ConsentRecord]:
        """
        Batch get multiple consent records.
        
        Args:
            keys: List of {'user_id': ..., 'consent_type': ...} dicts
            
        Returns:
            List of ConsentRecord objects
        """
        # DynamoDB batch_get has a limit of 100 items
        records = []
        
        for i in range(0, len(keys), 100):
            batch_keys = keys[i:i+100]
            
            response = self.table.meta.client.batch_get_item(
                RequestItems={
                    self.table.name: {
                        'Keys': batch_keys
                    }
                }
            )
            
            for item in response.get('Responses', {}).get(self.table.name, []):
                records.append(ConsentRecord.from_dict(item))
        
        return records


class ConflictError(Exception):
    """Raised when there's a version conflict during save."""
    pass

