"""
Lambda Handlers for Consent Management Service

This module contains the Lambda function handlers for:
- API requests (create, read, delete consent)
- Event processing (SQS triggered consent updates)
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

from models import ConsentRecord, ConsentType
from repository import ConsentRepository
from events import ConsentEventPublisher


# Initialize clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
sqs = boto3.client('sqs')

# Get environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'consent-store')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL', '')

# Initialize repository and publisher
repo = ConsentRepository(dynamodb.Table(TABLE_NAME))
publisher = ConsentEventPublisher(sns, SNS_TOPIC_ARN, sqs, SQS_QUEUE_URL)


def api_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main API Gateway handler for consent operations.
    
    Routes:
        POST /consent - Create or update consent
        GET /consent/{user_id} - Get user's consent preferences
        DELETE /consent/{user_id} - Withdraw all consent (unsubscribe all)
    """
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')
    
    try:
        if http_method == 'POST' and path == '/consent':
            return handle_create_consent(event)
        elif http_method == 'GET' and path.startswith('/consent/'):
            return handle_get_consent(event)
        elif http_method == 'DELETE' and path.startswith('/consent/'):
            return handle_delete_consent(event)
        else:
            return _response(404, {'error': 'Not found'})
    
    except Exception as e:
        print(f"Error processing request: {e}")
        return _response(500, {'error': 'Internal server error'})


def handle_create_consent(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /consent - Create or update a consent record.
    
    Request body:
        {
            "user_id": "user-123",
            "consent_type": "marketing",
            "granted": true,
            "source": "web_form"
        }
    """
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return _response(400, {'error': 'Invalid JSON body'})
    
    # Validate required fields
    required = ['user_id', 'consent_type', 'granted']
    missing = [f for f in required if f not in body]
    if missing:
        return _response(400, {'error': f'Missing required fields: {missing}'})
    
    # Validate consent type
    try:
        consent_type = ConsentType(body['consent_type'])
    except ValueError:
        valid_types = [t.value for t in ConsentType]
        return _response(400, {'error': f'Invalid consent_type. Valid types: {valid_types}'})
    
    # Create consent record
    record = ConsentRecord(
        user_id=body['user_id'],
        consent_type=consent_type,
        granted=body['granted'],
        source=body.get('source', 'api'),
        ip_address=event.get('requestContext', {}).get('http', {}).get('sourceIp'),
    )
    
    # Save to database
    repo.save(record)
    
    # Publish event
    publisher.publish_consent_updated(record)
    
    return _response(201, {
        'message': 'Consent recorded successfully',
        'consent': record.to_dict()
    })


def handle_get_consent(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /consent/{user_id} - Get all consent preferences for a user.
    
    Query params:
        consent_type (optional) - Filter by specific consent type
    """
    # Extract user_id from path
    path_params = event.get('pathParameters', {}) or {}
    user_id = path_params.get('user_id')
    
    if not user_id:
        return _response(400, {'error': 'user_id is required'})
    
    # Check for consent_type filter
    query_params = event.get('queryStringParameters', {}) or {}
    consent_type = query_params.get('consent_type')
    
    if consent_type:
        # Get specific consent
        record = repo.get(user_id, consent_type)
        if record:
            return _response(200, {'consent': record.to_dict()})
        else:
            return _response(404, {'error': 'Consent record not found'})
    else:
        # Get all consents for user
        records = repo.get_all_for_user(user_id)
        return _response(200, {
            'user_id': user_id,
            'consents': [r.to_dict() for r in records]
        })


def handle_delete_consent(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle DELETE /consent/{user_id} - Withdraw all consent (unsubscribe from all).
    
    This triggers the bulk consent withdrawal process:
    1. Gets all consent records for the user
    2. Sets all to granted=False
    3. Publishes withdrawal events
    """
    path_params = event.get('pathParameters', {}) or {}
    user_id = path_params.get('user_id')
    
    if not user_id:
        return _response(400, {'error': 'user_id is required'})
    
    # Get all consents for user
    records = repo.get_all_for_user(user_id)
    
    if not records:
        return _response(404, {'error': 'No consent records found for user'})
    
    # Withdraw all consents
    withdrawn_count = 0
    for record in records:
        if record.granted:
            record.granted = False
            record.updated_at = datetime.utcnow()
            record.source = 'bulk_withdrawal'
            repo.save(record)
            publisher.publish_consent_withdrawn(record)
            withdrawn_count += 1
    
    return _response(200, {
        'message': f'Successfully withdrew {withdrawn_count} consent(s)',
        'user_id': user_id
    })


def process_consent_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process consent events from SQS queue.
    
    This handler is triggered by SQS and processes consent change events
    for downstream systems (analytics, marketing, etc.)
    """
    processed = 0
    failed = 0
    
    for record in event.get('Records', []):
        try:
            body = json.loads(record['body'])
            
            # Handle different event types
            event_type = body.get('event_type')
            
            if event_type == 'consent_updated':
                _handle_consent_updated(body)
            elif event_type == 'consent_withdrawn':
                _handle_consent_withdrawn(body)
            else:
                print(f"Unknown event type: {event_type}")
            
            processed += 1
            
        except Exception as e:
            print(f"Error processing record: {e}")
            failed += 1
    
    return {
        'processed': processed,
        'failed': failed
    }


def _handle_consent_updated(event_data: Dict[str, Any]) -> None:
    """Handle a consent updated event."""
    user_id = event_data.get('user_id')
    consent_type = event_data.get('consent_type')
    granted = event_data.get('granted')
    
    print(f"Consent updated: user={user_id}, type={consent_type}, granted={granted}")
    
    # Here you would trigger downstream actions:
    # - Update marketing preferences
    # - Sync with CRM
    # - Update analytics tracking


def _handle_consent_withdrawn(event_data: Dict[str, Any]) -> None:
    """Handle a consent withdrawn event."""
    user_id = event_data.get('user_id')
    consent_type = event_data.get('consent_type')
    
    print(f"Consent withdrawn: user={user_id}, type={consent_type}")
    
    # Trigger cleanup actions:
    # - Remove from marketing lists
    # - Stop data collection
    # - Notify downstream services


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to create API Gateway response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }

