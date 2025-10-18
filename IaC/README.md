# Cost-Optimized Card ML Pipeline - Terraform Infrastructure

## 🎯 Architecture Overview

This Terraform configuration deploys a fully automated, cost-optimized ML pipeline for card balance prediction with the following components:

### 💰 Cost Optimization Features
- **Spot Instances**: Up to 90% savings on training and batch processing
- **Serverless**: Lambda functions with pay-per-use pricing
- **Batch Processing**: Scheduled bulk operations during off-peak hours
- **Auto-scaling**: Resources scale based on actual demand

### 🏗️ Infrastructure Components

#### Data Layer
- **S3 Buckets**: Card dataset and model artifacts storage
- **DynamoDB**: Fast, scalable card balance scores storage

#### Processing Layer
- **Lambda Functions**: Data preprocessing and real-time predictions
- **API Gateway**: Cost-effective API management
- **Batch Processing**: Spot instance-based bulk inference

#### ML Training
- **SageMaker**: Spot training jobs with automatic model registry
- **EventBridge**: Scheduled training and batch jobs

#### Monitoring
- **CloudWatch**: Comprehensive monitoring and logging
- **SNS**: Notifications for important events

## 🚀 Quick Deployment

```bash
# Clone and navigate to terraform directory
cd terraform

# Deploy infrastructure
./deploy.sh
```

## 📋 Manual Deployment Steps

```bash
# 1. Initialize Terraform
terraform init

# 2. Review planned changes
terraform plan

# 3. Deploy infrastructure
terraform apply

# 4. Get outputs
terraform output
```

## 🔧 Configuration

### Variables
- `aws_region`: AWS region (default: eu-central-1)
- `project_name`: Project prefix (default: teklo-card-ml)
- `training_instance_type`: SageMaker instance type (default: ml.m5.large)
- `batch_max_vcpus`: Max vCPUs for batch processing (default: 10)

### Customization
```bash
# Create terraform.tfvars file
cat > terraform.tfvars << EOF
aws_region = "us-west-2"
project_name = "my-card-ml"
batch_max_vcpus = 20
EOF
```

## 💡 Usage Examples

### Upload Dataset
```bash
aws s3 cp card_dataset.csv s3://$(terraform output -raw s3_dataset_bucket)/
```

### Test API
```bash
API_URL=$(terraform output -raw api_gateway_url)
curl -X POST $API_URL/predict -d '{"card_data": {...}}'
```

### Monitor Costs
- Check CloudWatch dashboards
- Review Trusted Advisor recommendations
- Monitor S3 and DynamoDB usage

## 🧹 Cleanup

```bash
# Destroy all resources
terraform destroy
```

## 📊 Expected Costs

### Monthly Estimates (Light Usage)
- **Lambda**: $5-15 (pay-per-request)
- **API Gateway**: $3-10 (per million requests)
- **S3**: $5-20 (storage + requests)
- **DynamoDB**: $5-25 (pay-per-request)
- **Batch/SageMaker**: $10-50 (spot pricing)

**Total**: ~$30-120/month for moderate usage

### Cost Optimization Tips
1. Use spot instances for all training
2. Schedule batch jobs during off-peak hours
3. Set up CloudWatch alarms for cost thresholds
4. Use S3 lifecycle policies for old data
5. Monitor and optimize DynamoDB read/write patterns
