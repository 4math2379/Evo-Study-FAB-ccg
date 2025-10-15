"""
AWS SageMaker Integration for Teklovossen Card Balance Prediction
ML model training, deployment, and inference pipeline
"""

import boto3
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import time
import pickle
import os

# SageMaker imports
import sagemaker
from sagemaker import get_execution_role
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.sklearn.model import SKLearnModel
from sagemaker.tensorflow import TensorFlow
from sagemaker.inputs import TrainingInput
from sagemaker.predictor import Predictor

# Local imports
from .data_analytics import TekloDataAnalyzer


class TekloSageMakerOrchestrator:
    """Orchestrates ML workflow on AWS SageMaker for card balance prediction"""
    
    def __init__(self, aws_region: str = 'us-east-1'):
        """Initialize SageMaker client and session"""
        self.aws_region = aws_region
        self.sagemaker_session = sagemaker.Session()
        self.role = self._get_execution_role()
        self.bucket = self.sagemaker_session.default_bucket()
        
        # Model configuration
        self.model_configs = {
            'balance_predictor': {
                'target': 'avg_win_rate',
                'problem_type': 'regression',
                'instance_type': 'ml.m5.large',
                'framework': 'sklearn'
            },
            'card_classifier': {
                'target': 'deck_name',
                'problem_type': 'classification', 
                'instance_type': 'ml.m5.large',
                'framework': 'tensorflow'
            },
            'balance_scorer': {
                'target': 'avg_expert_balance_score',
                'problem_type': 'regression',
                'instance_type': 'ml.m5.large',
                'framework': 'sklearn'
            }
        }
        
        # Tracking
        self.training_jobs = {}
        self.deployed_endpoints = {}
        
    def _get_execution_role(self) -> str:
        """Get SageMaker execution role"""
        try:
            return get_execution_role()
        except:
            # If running outside SageMaker, use IAM role ARN
            return os.environ.get('SAGEMAKER_ROLE', 
                'arn:aws:iam::YOUR_ACCOUNT:role/SageMakerExecutionRole')
    
    def prepare_training_data(self, data_path: str = "../data") -> Dict[str, str]:
        """Prepare and upload training data to S3"""
        analyzer = TekloDataAnalyzer(data_path)
        
        # Load and prepare data for different model types
        try:
            analyzer.load_simulation_data()
            analyzer.load_ml_data()
        except:
            raise ValueError("No simulation data found. Run gameplay simulator first.")
        
        # Export data for different models
        s3_paths = {}
        
        # 1. Balance Predictor (Win Rate Prediction)
        balance_path = analyzer.export_for_sagemaker('avg_win_rate')
        s3_balance_path = self._upload_to_s3(balance_path, 'balance_predictor/training_data.csv')
        s3_paths['balance_predictor'] = s3_balance_path
        
        # 2. Card Classifier (Deck Type Classification)
        if 'deck_name' in analyzer.ml_data.columns:
            # Create classification dataset
            classification_data = analyzer.ml_data.copy()
            # Encode deck names as numbers for classification
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            classification_data['deck_name_encoded'] = le.fit_transform(classification_data['deck_name'])
            
            # Save label encoder for later use
            encoder_path = Path(data_path) / "processed" / f"deck_label_encoder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            with open(encoder_path, 'wb') as f:
                pickle.dump(le, f)
            
            # Export classification data
            feature_columns = [col for col in analyzer.ml_data.columns 
                             if col not in ['deck_name', 'avg_win_rate']]
            
            classification_export = classification_data[['deck_name_encoded'] + feature_columns].fillna(0)
            class_path = Path(data_path) / "processed" / f"classification_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            classification_export.to_csv(class_path, index=False, header=False)
            
            s3_class_path = self._upload_to_s3(str(class_path), 'card_classifier/training_data.csv')
            s3_paths['card_classifier'] = s3_class_path
            
            # Upload label encoder
            s3_encoder_path = self._upload_to_s3(str(encoder_path), 'card_classifier/label_encoder.pkl')
            s3_paths['label_encoder'] = s3_encoder_path
        
        # 3. Balance Scorer (Expert Score Prediction) 
        if 'avg_expert_balance_score' in analyzer.ml_data.columns:
            balance_scorer_path = analyzer.export_for_sagemaker('avg_expert_balance_score')
            s3_scorer_path = self._upload_to_s3(balance_scorer_path, 'balance_scorer/training_data.csv')
            s3_paths['balance_scorer'] = s3_scorer_path
        
        print(f"Training data uploaded to S3 bucket: {self.bucket}")
        for model, path in s3_paths.items():
            print(f"  {model}: {path}")
        
        return s3_paths
    
    def _upload_to_s3(self, local_path: str, s3_key: str) -> str:
        """Upload file to S3 and return S3 URI"""
        s3_client = boto3.client('s3', region_name=self.aws_region)
        s3_client.upload_file(local_path, self.bucket, f"teklovossen-ml/{s3_key}")
        return f"s3://{self.bucket}/teklovossen-ml/{s3_key}"
    
    def create_training_scripts(self) -> Dict[str, str]:
        """Create training scripts for different model types"""
        scripts_dir = Path("../scripts/training_scripts")
        scripts_dir.mkdir(exist_ok=True)
        
        # 1. Balance Predictor Script (SKLearn)
        sklearn_script = '''
import argparse
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
import os

def model_fn(model_dir):
    """Load model for inference"""
    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    return model

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR"))
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAINING"))
    
    args = parser.parse_args()
    
    # Load data
    train_data = pd.read_csv(f"{args.train}/training_data.csv", header=None)
    X = train_data.iloc[:, 1:].values
    y = train_data.iloc[:, 0].values
    
    # Create pipeline with preprocessing and model
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model', GradientBoostingRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        ))
    ])
    
    # Train model
    pipeline.fit(X, y)
    
    # Evaluate
    cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring='r2')
    print(f"Cross-validation R² scores: {cv_scores}")
    print(f"Mean CV R² score: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    
    # Save model
    joblib.dump(pipeline, os.path.join(args.model_dir, "model.joblib"))
    print("Model saved successfully")
'''
        
        sklearn_path = scripts_dir / "balance_predictor_train.py"
        with open(sklearn_path, 'w') as f:
            f.write(sklearn_script)
        
        # 2. Card Classifier Script (TensorFlow)
        tf_script = '''
import argparse
import tensorflow as tf
import pandas as pd
import numpy as np
import os
import json

def create_model(input_dim, num_classes):
    """Create neural network model for classification"""
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=(input_dim,)),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(16, activation='relu'),
        tf.keras.layers.Dense(num_classes, activation='softmax')
    ])
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR"))
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAINING"))
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=32)
    
    args = parser.parse_args()
    
    # Load data
    train_data = pd.read_csv(f"{args.train}/training_data.csv", header=None)
    X = train_data.iloc[:, 1:].values.astype(np.float32)
    y = train_data.iloc[:, 0].values.astype(np.int32)
    
    # Create and train model
    num_classes = len(np.unique(y))
    model = create_model(X.shape[1], num_classes)
    
    # Train
    history = model.fit(
        X, y,
        epochs=args.epochs,
        batch_size=args.batch_size,
        validation_split=0.2,
        verbose=1
    )
    
    # Save model
    model.save(os.path.join(args.model_dir, "1"))
    
    # Save training history
    with open(os.path.join(args.model_dir, "training_history.json"), "w") as f:
        json.dump(history.history, f)
    
    print("Model training completed and saved")
'''
        
        tf_path = scripts_dir / "card_classifier_train.py"
        with open(tf_path, 'w') as f:
            f.write(tf_script)
        
        return {
            'balance_predictor': str(sklearn_path),
            'card_classifier': str(tf_path),
            'balance_scorer': str(sklearn_path)  # Reuse sklearn script
        }
    
    def train_models(self, s3_data_paths: Dict[str, str]) -> Dict[str, str]:
        """Train all models on SageMaker"""
        training_scripts = self.create_training_scripts()
        
        for model_name, config in self.model_configs.items():
            if model_name not in s3_data_paths:
                print(f"Skipping {model_name} - no training data available")
                continue
            
            print(f"\\nStarting training for {model_name}...")
            
            if config['framework'] == 'sklearn':
                estimator = SKLearn(
                    entry_point=training_scripts[model_name],
                    role=self.role,
                    instance_type=config['instance_type'],
                    framework_version='1.0-1',
                    py_version='py3',
                    script_mode=True,
                    sagemaker_session=self.sagemaker_session
                )
            
            elif config['framework'] == 'tensorflow':
                estimator = TensorFlow(
                    entry_point=training_scripts[model_name],
                    role=self.role,
                    instance_type=config['instance_type'],
                    framework_version='2.8',
                    py_version='py39',
                    script_mode=True,
                    sagemaker_session=self.sagemaker_session,
                    hyperparameters={
                        'epochs': 100,
                        'batch-size': 16
                    }
                )
            
            # Start training
            job_name = f"teklovossen-{model_name}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
            
            training_input = TrainingInput(
                s3_data=s3_data_paths[model_name],
                content_type='text/csv'
            )
            
            estimator.fit({'training': training_input}, job_name=job_name)
            self.training_jobs[model_name] = estimator
            
            print(f"Training job started for {model_name}: {job_name}")
        
        return self.training_jobs
    
    def deploy_models(self, wait_for_training: bool = True) -> Dict[str, str]:
        """Deploy trained models to SageMaker endpoints"""
        if wait_for_training:
            print("Waiting for all training jobs to complete...")
            for model_name, estimator in self.training_jobs.items():
                print(f"  Waiting for {model_name}...")
                # Training job completion is handled automatically by estimator.fit()
                
        # Deploy models
        for model_name, estimator in self.training_jobs.items():
            print(f"\\nDeploying {model_name}...")
            
            endpoint_name = f"teklovossen-{model_name}-endpoint"
            
            try:
                predictor = estimator.deploy(
                    initial_instance_count=1,
                    instance_type='ml.t2.medium',
                    endpoint_name=endpoint_name
                )
                
                self.deployed_endpoints[model_name] = {
                    'endpoint_name': endpoint_name,
                    'predictor': predictor
                }
                
                print(f"Successfully deployed {model_name} to endpoint: {endpoint_name}")
                
            except Exception as e:
                print(f"Failed to deploy {model_name}: {e}")
        
        return {name: info['endpoint_name'] for name, info in self.deployed_endpoints.items()}
    
    def predict_card_balance(self, card_features: Dict[str, Any]) -> Dict[str, float]:
        """Make predictions for card balance using deployed models"""
        if not self.deployed_endpoints:
            raise ValueError("No models deployed. Run deploy_models() first.")
        
        predictions = {}
        
        # Convert card features to array format expected by models
        feature_array = self._features_to_array(card_features)
        
        for model_name, endpoint_info in self.deployed_endpoints.items():
            try:
                predictor = endpoint_info['predictor']
                result = predictor.predict(feature_array)
                predictions[model_name] = float(result[0]) if isinstance(result, (list, np.ndarray)) else float(result)
                
            except Exception as e:
                print(f"Prediction failed for {model_name}: {e}")
                predictions[model_name] = None
        
        return predictions
    
    def _features_to_array(self, card_features: Dict[str, Any]) -> np.ndarray:
        """Convert card features dictionary to numpy array for prediction"""
        # This should match the feature order used in training
        expected_features = [
            'AI', 'Nano', 'Quantum', 'Base',
            '0_cost', '1_cost', '2_cost', '3_cost', '4_plus_cost',
            'equipment', 'item', 'action',
            'avg_turns', 'avg_evos', 'avg_teklo_energy',
            'avg_nanite_counters', 'avg_quantum_charges',
            'consistency_score', 'avg_expert_balance_score'
        ]
        
        feature_vector = []
        for feature in expected_features:
            value = card_features.get(feature, 0.0)
            feature_vector.append(float(value))
        
        return np.array([feature_vector])
    
    def batch_predict_deck_performance(self, deck_configurations: List[Dict[str, Any]]) -> pd.DataFrame:
        """Batch prediction for multiple deck configurations"""
        results = []
        
        for i, deck_config in enumerate(deck_configurations):
            predictions = self.predict_card_balance(deck_config)
            result = {
                'deck_id': i,
                'deck_config': deck_config,
                **predictions
            }
            results.append(result)
        
        return pd.DataFrame(results)
    
    def generate_balance_recommendations(self, card_features: Dict[str, Any]) -> Dict[str, Any]:
        """Generate automated balance recommendations"""
        predictions = self.predict_card_balance(card_features)
        
        recommendations = {
            'predicted_win_rate': predictions.get('balance_predictor', 0.5),
            'predicted_balance_score': predictions.get('balance_scorer', 5.0),
            'recommendations': []
        }
        
        # Generate specific recommendations based on predictions
        win_rate = predictions.get('balance_predictor', 0.5)
        balance_score = predictions.get('balance_scorer', 5.0)
        
        if win_rate > 0.65:
            recommendations['recommendations'].append(
                "⚠️ High win rate predicted - consider increasing costs by 1 Teklo Energy"
            )
        elif win_rate < 0.35:
            recommendations['recommendations'].append(
                "📈 Low win rate predicted - consider reducing costs or adding card draw"
            )
        
        if balance_score < 4.0:
            recommendations['recommendations'].append(
                "🔧 Low balance score - significant adjustments needed"
            )
        elif balance_score > 8.0:
            recommendations['recommendations'].append(
                "✅ High balance score - minor tweaks may improve competitive viability"
            )
        
        # Resource efficiency recommendations
        if card_features.get('avg_teklo_energy', 0) > 3.0:
            recommendations['recommendations'].append(
                "⚡ High Teklo Energy generation - monitor for combo potential"
            )
        
        return recommendations
    
    def cleanup_resources(self, delete_endpoints: bool = False):
        """Clean up AWS resources"""
        if delete_endpoints:
            for model_name, endpoint_info in self.deployed_endpoints.items():
                try:
                    endpoint_name = endpoint_info['endpoint_name']
                    predictor = endpoint_info['predictor']
                    predictor.delete_endpoint()
                    print(f"Deleted endpoint: {endpoint_name}")
                except Exception as e:
                    print(f"Failed to delete endpoint {endpoint_name}: {e}")
        
        print("Cleanup completed")


def create_sagemaker_config_template():
    """Create configuration template for AWS credentials"""
    config_template = {
        "aws_region": "us-east-1",
        "sagemaker_role": "arn:aws:iam::YOUR_ACCOUNT:role/SageMakerExecutionRole",
        "s3_bucket": "your-sagemaker-bucket",
        "model_settings": {
            "balance_predictor": {
                "instance_type": "ml.m5.large",
                "max_runtime_seconds": 3600
            },
            "card_classifier": {
                "instance_type": "ml.m5.large",
                "max_runtime_seconds": 3600
            }
        }
    }
    
    config_path = Path("../config/sagemaker_config_template.json")
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config_template, f, indent=2)
    
    print(f"SageMaker configuration template created at: {config_path}")
    print("Please update with your AWS account details before using.")


if __name__ == "__main__":
    # Example usage
    print("Teklovossen SageMaker Integration")
    print("=================================")
    
    # Create config template
    create_sagemaker_config_template()
    
    # Note: Actual training requires AWS credentials and simulation data
    print("\\nTo use this integration:")
    print("1. Configure AWS credentials")
    print("2. Update sagemaker_config_template.json with your settings") 
    print("3. Run gameplay simulations to generate training data")
    print("4. Execute the ML training pipeline")
    print("\\nExample workflow:")
    print("  orchestrator = TekloSageMakerOrchestrator()")
    print("  s3_paths = orchestrator.prepare_training_data()")
    print("  training_jobs = orchestrator.train_models(s3_paths)")
    print("  endpoints = orchestrator.deploy_models()")
    print("  predictions = orchestrator.predict_card_balance(card_features)")
