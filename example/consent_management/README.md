# Consent Management Service

A microservice for managing user consent preferences (GDPR, CCPA compliance).

## Overview

This service handles:
- User consent collection and storage
- Consent preference retrieval
- Audit logging for compliance
- Integration with downstream services

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   API GW    │────▶│   Lambda    │────▶│  DynamoDB   │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │     SQS     │
                    └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │  Step Func  │
                    └─────────────┘
```

## Getting Started

1. Deploy infrastructure: `cd infrastructure && terraform apply`
2. Deploy Lambda: `cd src && pip install -r requirements.txt`

## API Endpoints

- `POST /consent` - Submit user consent
- `GET /consent/{user_id}` - Get user consent preferences
- `DELETE /consent/{user_id}` - Withdraw all consent (unsubscribe all)

