output "api_gateway_url" {
  description = "API Gateway URL"
  value       = "${aws_api_gateway_deployment.card_api_deployment.invoke_url}"
}

output "s3_dataset_bucket" {
  description = "S3 bucket for card dataset"
  value       = aws_s3_bucket.card_dataset.bucket
}

output "s3_models_bucket" {
  description = "S3 bucket for model artifacts"
  value       = aws_s3_bucket.model_artifacts.bucket
}

output "dynamodb_table" {
  description = "DynamoDB table for card balance scores"
  value       = aws_dynamodb_table.card_balance_scores.name
}

output "sagemaker_role_arn" {
  description = "SageMaker execution role ARN"
  value       = aws_iam_role.sagemaker_role.arn
}

output "batch_compute_environment" {
  description = "Batch compute environment name"
  value       = aws_batch_compute_environment.card_batch.compute_environment_name
}

output "sns_topic_arn" {
  description = "SNS topic ARN for notifications"
  value       = aws_sns_topic.card_notifications.arn
}
