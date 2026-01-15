# Consent Management Infrastructure
# Main Terraform configuration

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "terraform-state-bucket"
    key    = "consent-management/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "consent-management"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# DynamoDB Table for storing consent records
resource "aws_dynamodb_table" "consent_store" {
  name           = "${var.environment}-consent-store"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "consent_type"
  
  attribute {
    name = "user_id"
    type = "S"
  }
  
  attribute {
    name = "consent_type"
    type = "S"
  }
  
  attribute {
    name = "updated_at"
    type = "S"
  }
  
  global_secondary_index {
    name            = "consent-type-index"
    hash_key        = "consent_type"
    range_key       = "updated_at"
    projection_type = "ALL"
  }
  
  point_in_time_recovery {
    enabled = true
  }
  
  tags = {
    Name = "Consent Store"
  }
}

# SQS Queue for consent change events
resource "aws_sqs_queue" "consent_events" {
  name                       = "${var.environment}-consent-events"
  delay_seconds              = 0
  max_message_size           = 262144
  message_retention_seconds  = 1209600  # 14 days
  receive_wait_time_seconds  = 10
  visibility_timeout_seconds = 300
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.consent_events_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "consent_events_dlq" {
  name                      = "${var.environment}-consent-events-dlq"
  message_retention_seconds = 1209600
}

# SNS Topic for consent notifications
resource "aws_sns_topic" "consent_notifications" {
  name = "${var.environment}-consent-notifications"
}

# Subscribe downstream services to consent changes
resource "aws_sns_topic_subscription" "marketing_service" {
  topic_arn = aws_sns_topic.consent_notifications.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.consent_events.arn
}

resource "aws_sns_topic_subscription" "analytics_service" {
  topic_arn = aws_sns_topic.consent_notifications.arn
  protocol  = "https"
  endpoint  = "https://analytics.example.com/webhooks/consent"
}

