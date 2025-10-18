terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# S3 Buckets
resource "aws_s3_bucket" "card_dataset" {
  bucket = "${var.project_name}-card-dataset-${random_id.bucket_suffix.hex}"
}

resource "aws_s3_bucket" "model_artifacts" {
  bucket = "${var.project_name}-model-artifacts-${random_id.bucket_suffix.hex}"
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# DynamoDB Table
resource "aws_dynamodb_table" "card_balance_scores" {
  name           = "${var.project_name}-card-balance-scores"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "card_id"

  attribute {
    name = "card_id"
    type = "S"
  }

  tags = {
    Name = "Card Balance Scores"
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "s3:GetObject",
          "s3:PutObject",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "sagemaker:InvokeEndpoint"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda Functions
resource "aws_lambda_function" "data_preprocessing" {
  filename         = "preprocessing.zip"
  function_name    = "${var.project_name}-data-preprocessing"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      S3_BUCKET = aws_s3_bucket.card_dataset.bucket
    }
  }
}

resource "aws_lambda_function" "prediction_service" {
  filename         = "prediction.zip"
  function_name    = "${var.project_name}-prediction-service"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.card_balance_scores.name
      S3_MODELS_BUCKET = aws_s3_bucket.model_artifacts.bucket
    }
  }
}

# API Gateway
resource "aws_api_gateway_rest_api" "card_api" {
  name = "${var.project_name}-card-api"
}

resource "aws_api_gateway_resource" "preprocess" {
  rest_api_id = aws_api_gateway_rest_api.card_api.id
  parent_id   = aws_api_gateway_rest_api.card_api.root_resource_id
  path_part   = "preprocess"
}

resource "aws_api_gateway_resource" "predict" {
  rest_api_id = aws_api_gateway_rest_api.card_api.id
  parent_id   = aws_api_gateway_rest_api.card_api.root_resource_id
  path_part   = "predict"
}

resource "aws_api_gateway_method" "preprocess_post" {
  rest_api_id   = aws_api_gateway_rest_api.card_api.id
  resource_id   = aws_api_gateway_resource.preprocess.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "predict_post" {
  rest_api_id   = aws_api_gateway_rest_api.card_api.id
  resource_id   = aws_api_gateway_resource.predict.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "preprocess_integration" {
  rest_api_id = aws_api_gateway_rest_api.card_api.id
  resource_id = aws_api_gateway_resource.preprocess.id
  http_method = aws_api_gateway_method.preprocess_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.data_preprocessing.invoke_arn
}

resource "aws_api_gateway_integration" "predict_integration" {
  rest_api_id = aws_api_gateway_rest_api.card_api.id
  resource_id = aws_api_gateway_resource.predict.id
  http_method = aws_api_gateway_method.predict_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.prediction_service.invoke_arn
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "preprocess_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_preprocessing.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.card_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "predict_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.prediction_service.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.card_api.execution_arn}/*/*"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "card_api_deployment" {
  depends_on = [
    aws_api_gateway_integration.preprocess_integration,
    aws_api_gateway_integration.predict_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.card_api.id
  stage_name  = "prod"
}

# SageMaker IAM Role
resource "aws_iam_role" "sagemaker_role" {
  name = "${var.project_name}-sagemaker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "sagemaker_execution_role" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# Batch Compute Environment
resource "aws_batch_compute_environment" "card_batch" {
  compute_environment_name = "${var.project_name}-batch-env"
  type                    = "MANAGED"
  state                   = "ENABLED"

  compute_resources {
    type                = "EC2"
    allocation_strategy = "SPOT_CAPACITY_OPTIMIZED"
    min_vcpus          = 0
    max_vcpus          = 10
    desired_vcpus      = 0
    
    instance_types = ["optimal"]
    
    spot_iam_fleet_request_role = aws_iam_role.batch_spot_fleet_role.arn
    
    subnets = [aws_subnet.batch_subnet.id]
    security_group_ids = [aws_security_group.batch_sg.id]
    
    tags = {
      Name = "Card ML Batch"
    }
  }

  service_role = aws_iam_role.batch_service_role.arn
}

# EventBridge Rule for Scheduling
resource "aws_cloudwatch_event_rule" "training_schedule" {
  name                = "${var.project_name}-training-schedule"
  description         = "Trigger training job daily"
  schedule_expression = "cron(0 2 * * ? *)"  # Daily at 2 AM
}

resource "aws_cloudwatch_event_rule" "batch_schedule" {
  name                = "${var.project_name}-batch-schedule"
  description         = "Trigger batch inference"
  schedule_expression = "cron(0 4 * * ? *)"  # Daily at 4 AM
}

# SNS Topic for Notifications
resource "aws_sns_topic" "card_notifications" {
  name = "${var.project_name}-notifications"
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_preprocessing_logs" {
  name              = "/aws/lambda/${aws_lambda_function.data_preprocessing.function_name}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "lambda_prediction_logs" {
  name              = "/aws/lambda/${aws_lambda_function.prediction_service.function_name}"
  retention_in_days = 7
}
