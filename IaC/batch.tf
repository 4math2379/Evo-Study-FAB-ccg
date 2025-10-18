# Batch Job Queue
resource "aws_batch_job_queue" "card_batch_queue" {
  name     = "${var.project_name}-batch-queue"
  state    = "ENABLED"
  priority = 1

  compute_environment_order {
    order               = 1
    compute_environment = aws_batch_compute_environment.card_batch.arn
  }
}

# Batch Job Definition
resource "aws_batch_job_definition" "card_inference_job" {
  name = "${var.project_name}-inference-job"
  type = "container"

  container_properties = jsonencode({
    image  = "python:3.9-slim"
    vcpus  = 1
    memory = 2048

    jobRoleArn = aws_iam_role.batch_job_role.arn

    environment = [
      {
        name  = "S3_MODELS_BUCKET"
        value = aws_s3_bucket.model_artifacts.bucket
      },
      {
        name  = "DYNAMODB_TABLE"
        value = aws_dynamodb_table.card_balance_scores.name
      }
    ]

    command = [
      "python",
      "-c",
      "print('Batch inference job placeholder')"
    ]
  })

  retry_strategy {
    attempts = 3
  }

  timeout {
    attempt_duration_seconds = 3600
  }
}

# Batch Job Role
resource "aws_iam_role" "batch_job_role" {
  name = "${var.project_name}-batch-job-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "batch_job_policy" {
  name = "${var.project_name}-batch-job-policy"
  role = aws_iam_role.batch_job_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Scan",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# EventBridge Targets
resource "aws_cloudwatch_event_target" "batch_target" {
  rule      = aws_cloudwatch_event_rule.batch_schedule.name
  target_id = "BatchInferenceTarget"
  arn       = aws_batch_job_queue.card_batch_queue.arn
  role_arn  = aws_iam_role.eventbridge_role.arn

  batch_target {
    job_definition = aws_batch_job_definition.card_inference_job.arn
    job_name       = "${var.project_name}-scheduled-inference"
    job_queue      = aws_batch_job_queue.card_batch_queue.arn
  }
}
