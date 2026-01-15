# Outputs for Consent Management Infrastructure

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_api.consent_api.api_endpoint
}

output "dynamodb_table_name" {
  description = "DynamoDB table name for consent storage"
  value       = aws_dynamodb_table.consent_store.name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.consent_store.arn
}

output "sns_topic_arn" {
  description = "SNS topic ARN for consent notifications"
  value       = aws_sns_topic.consent_notifications.arn
}

output "sqs_queue_url" {
  description = "SQS queue URL for consent events"
  value       = aws_sqs_queue.consent_events.url
}

output "lambda_api_arn" {
  description = "Consent API Lambda ARN"
  value       = aws_lambda_function.consent_api.arn
}

output "lambda_processor_arn" {
  description = "Consent Processor Lambda ARN"
  value       = aws_lambda_function.consent_processor.arn
}

output "step_function_arn" {
  description = "Step Function ARN for bulk operations"
  value       = aws_sfn_state_machine.bulk_consent_processor.arn
}

