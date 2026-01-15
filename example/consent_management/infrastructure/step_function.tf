# Step Function for bulk consent operations

resource "aws_sfn_state_machine" "bulk_consent_processor" {
  name     = "${var.environment}-bulk-consent-processor"
  role_arn = aws_iam_role.step_function_role.arn
  
  definition = jsonencode({
    Comment = "Process bulk consent operations (e.g., unsubscribe all)"
    StartAt = "ValidateRequest"
    States = {
      ValidateRequest = {
        Type = "Task"
        Resource = aws_lambda_function.consent_api.arn
        Parameters = {
          "action" = "validate"
          "payload.$" = "$"
        }
        Next = "GetUserConsents"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next = "HandleError"
        }]
      }
      
      GetUserConsents = {
        Type = "Task"
        Resource = "arn:aws:states:::dynamodb:query"
        Parameters = {
          TableName = aws_dynamodb_table.consent_store.name
          KeyConditionExpression = "user_id = :uid"
          ExpressionAttributeValues = {
            ":uid" = { "S.$" = "$.user_id" }
          }
        }
        Next = "ProcessEachConsent"
      }
      
      ProcessEachConsent = {
        Type = "Map"
        ItemsPath = "$.Items"
        MaxConcurrency = 5
        Iterator = {
          StartAt = "WithdrawConsent"
          States = {
            WithdrawConsent = {
              Type = "Task"
              Resource = aws_lambda_function.consent_processor.arn
              Parameters = {
                "action" = "withdraw"
                "consent.$" = "$"
              }
              End = true
            }
          }
        }
        Next = "NotifyCompletion"
      }
      
      NotifyCompletion = {
        Type = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn = aws_sns_topic.consent_notifications.arn
          Message = {
            "event" = "bulk_consent_withdrawal_complete"
            "user_id.$" = "$.user_id"
            "timestamp.$" = "$$.State.EnteredTime"
          }
        }
        End = true
      }
      
      HandleError = {
        Type = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn = aws_sns_topic.consent_notifications.arn
          Message = {
            "event" = "bulk_consent_error"
            "error.$" = "$.Error"
          }
        }
        End = true
      }
    }
  })
}

# IAM Role for Step Function
resource "aws_iam_role" "step_function_role" {
  name = "${var.environment}-consent-sfn-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "step_function_policy" {
  name = "step-function-execution"
  role = aws_iam_role.step_function_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["lambda:InvokeFunction"]
        Resource = [
          aws_lambda_function.consent_api.arn,
          aws_lambda_function.consent_processor.arn
        ]
      },
      {
        Effect = "Allow"
        Action = ["dynamodb:Query"]
        Resource = aws_dynamodb_table.consent_store.arn
      },
      {
        Effect = "Allow"
        Action = ["sns:Publish"]
        Resource = aws_sns_topic.consent_notifications.arn
      }
    ]
  })
}

