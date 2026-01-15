# API Gateway for Consent Management

resource "aws_apigatewayv2_api" "consent_api" {
  name          = "${var.environment}-consent-api"
  protocol_type = "HTTP"
  
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_stage" "consent_api" {
  api_id      = aws_apigatewayv2_api.consent_api.id
  name        = var.environment
  auto_deploy = true
  
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.environment}-consent-api"
  retention_in_days = 30
}

# Lambda integration
resource "aws_apigatewayv2_integration" "consent_lambda" {
  api_id                 = aws_apigatewayv2_api.consent_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.consent_api.invoke_arn
  payload_format_version = "2.0"
}

# Routes
resource "aws_apigatewayv2_route" "post_consent" {
  api_id    = aws_apigatewayv2_api.consent_api.id
  route_key = "POST /consent"
  target    = "integrations/${aws_apigatewayv2_integration.consent_lambda.id}"
}

resource "aws_apigatewayv2_route" "get_consent" {
  api_id    = aws_apigatewayv2_api.consent_api.id
  route_key = "GET /consent/{user_id}"
  target    = "integrations/${aws_apigatewayv2_integration.consent_lambda.id}"
}

resource "aws_apigatewayv2_route" "delete_consent" {
  api_id    = aws_apigatewayv2_api.consent_api.id
  route_key = "DELETE /consent/{user_id}"
  target    = "integrations/${aws_apigatewayv2_integration.consent_lambda.id}"
}

# Permission for API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.consent_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.consent_api.execution_arn}/*/*"
}

