# Lambda Functions for Consent Management

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.environment}-consent-lambda-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "dynamodb-access"
  role = aws_iam_role.lambda_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.consent_store.arn,
          "${aws_dynamodb_table.consent_store.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.consent_notifications.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.consent_events.arn
      }
    ]
  })
}

# Lambda function for handling consent API requests
resource "aws_lambda_function" "consent_api" {
  function_name = "${var.environment}-consent-api"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handlers.api_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256
  
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  
  environment {
    variables = {
      DYNAMODB_TABLE    = aws_dynamodb_table.consent_store.name
      SNS_TOPIC_ARN     = aws_sns_topic.consent_notifications.arn
      SQS_QUEUE_URL     = aws_sqs_queue.consent_events.url
      ENVIRONMENT       = var.environment
    }
  }
  
  tracing_config {
    mode = "Active"
  }
}

# Lambda for processing consent events (triggered by SQS)
resource "aws_lambda_function" "consent_processor" {
  function_name = "${var.environment}-consent-processor"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handlers.process_consent_event"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 512
  
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  
  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.consent_store.name
      ENVIRONMENT    = var.environment
    }
  }
}

# SQS trigger for processor Lambda
resource "aws_lambda_event_source_mapping" "consent_sqs_trigger" {
  event_source_arn = aws_sqs_queue.consent_events.arn
  function_name    = aws_lambda_function.consent_processor.arn
  batch_size       = 10
}

# Lambda package
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/lambda.zip"
}

