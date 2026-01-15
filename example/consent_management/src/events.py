"""
Event Publishing for Consent Management

Handles publishing consent change events to SNS/SQS for downstream consumers.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional

from models import ConsentRecord


class ConsentEventPublisher:
    """
    Publishes consent events to SNS topic and SQS queue.
    
    Events are published when:
    - Consent is granted
    - Consent is withdrawn
    - Consent is updated
    """
    
    def __init__(self, sns_client, topic_arn: str, sqs_client, queue_url: str):
        """
        Initialize publisher with AWS clients and resource ARNs.
        
        Args:
            sns_client: boto3 SNS client
            topic_arn: SNS topic ARN for broadcasting
            sqs_client: boto3 SQS client
            queue_url: SQS queue URL for processing
        """
        self.sns = sns_client
        self.topic_arn = topic_arn
        self.sqs = sqs_client
        self.queue_url = queue_url
    
    def publish_consent_updated(self, record: ConsentRecord) -> str:
        """
        Publish a consent updated event.
        
        Args:
            record: The updated ConsentRecord
            
        Returns:
            Message ID from SNS
        """
        event = self._build_event('consent_updated', record)
        return self._publish_to_sns(event)
    
    def publish_consent_withdrawn(self, record: ConsentRecord) -> str:
        """
        Publish a consent withdrawn event.
        
        This is a special case of update where granted=False.
        Triggers additional cleanup in downstream systems.
        
        Args:
            record: The withdrawn ConsentRecord
            
        Returns:
            Message ID from SNS
        """
        event = self._build_event('consent_withdrawn', record)
        
        # Also send to SQS for immediate processing
        self._send_to_sqs(event)
        
        return self._publish_to_sns(event)
    
    def publish_consent_granted(self, record: ConsentRecord) -> str:
        """
        Publish a consent granted event.
        
        Args:
            record: The granted ConsentRecord
            
        Returns:
            Message ID from SNS
        """
        event = self._build_event('consent_granted', record)
        return self._publish_to_sns(event)
    
    def publish_bulk_withdrawal_started(
        self, 
        user_id: str, 
        consent_types: list
    ) -> str:
        """
        Publish event when bulk withdrawal begins.
        
        Args:
            user_id: User initiating bulk withdrawal
            consent_types: List of consent types being withdrawn
            
        Returns:
            Message ID from SNS
        """
        event = {
            'event_type': 'bulk_withdrawal_started',
            'user_id': user_id,
            'consent_types': consent_types,
            'timestamp': datetime.utcnow().isoformat(),
        }
        return self._publish_to_sns(event)
    
    def publish_bulk_withdrawal_completed(
        self, 
        user_id: str, 
        withdrawn_count: int
    ) -> str:
        """
        Publish event when bulk withdrawal completes.
        
        Args:
            user_id: User who withdrew consent
            withdrawn_count: Number of consents withdrawn
            
        Returns:
            Message ID from SNS
        """
        event = {
            'event_type': 'bulk_withdrawal_completed',
            'user_id': user_id,
            'withdrawn_count': withdrawn_count,
            'timestamp': datetime.utcnow().isoformat(),
        }
        return self._publish_to_sns(event)
    
    def _build_event(self, event_type: str, record: ConsentRecord) -> Dict[str, Any]:
        """Build event payload from consent record."""
        return {
            'event_type': event_type,
            'user_id': record.user_id,
            'consent_type': record.consent_type.value if hasattr(record.consent_type, 'value') else record.consent_type,
            'granted': record.granted,
            'source': record.source,
            'timestamp': datetime.utcnow().isoformat(),
            'record_version': record.version,
        }
    
    def _publish_to_sns(self, event: Dict[str, Any]) -> str:
        """Publish event to SNS topic."""
        if not self.topic_arn:
            print(f"SNS topic not configured, skipping publish: {event}")
            return ""
        
        response = self.sns.publish(
            TopicArn=self.topic_arn,
            Message=json.dumps(event),
            MessageAttributes={
                'event_type': {
                    'DataType': 'String',
                    'StringValue': event['event_type']
                },
                'user_id': {
                    'DataType': 'String',
                    'StringValue': event['user_id']
                }
            }
        )
        
        return response['MessageId']
    
    def _send_to_sqs(self, event: Dict[str, Any]) -> str:
        """Send event directly to SQS for immediate processing."""
        if not self.queue_url:
            print(f"SQS queue not configured, skipping send: {event}")
            return ""
        
        response = self.sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(event),
            MessageAttributes={
                'event_type': {
                    'DataType': 'String',
                    'StringValue': event['event_type']
                }
            }
        )
        
        return response['MessageId']


class ConsentEventConsumer:
    """
    Consumes and processes consent events from SQS.
    
    Used by downstream services to react to consent changes.
    """
    
    def __init__(self, sqs_client, queue_url: str):
        self.sqs = sqs_client
        self.queue_url = queue_url
        self.handlers = {}
    
    def register_handler(self, event_type: str, handler):
        """Register a handler for a specific event type."""
        self.handlers[event_type] = handler
    
    def poll(self, max_messages: int = 10, wait_time: int = 20):
        """
        Poll for messages and process them.
        
        Args:
            max_messages: Maximum messages to receive per poll
            wait_time: Long polling wait time in seconds
        """
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time,
            MessageAttributeNames=['All']
        )
        
        for message in response.get('Messages', []):
            self._process_message(message)
    
    def _process_message(self, message: Dict[str, Any]):
        """Process a single SQS message."""
        try:
            body = json.loads(message['Body'])
            event_type = body.get('event_type')
            
            handler = self.handlers.get(event_type)
            if handler:
                handler(body)
            else:
                print(f"No handler for event type: {event_type}")
            
            # Delete message after successful processing
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
            
        except Exception as e:
            print(f"Error processing message: {e}")
            # Message will be retried or sent to DLQ

