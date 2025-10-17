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
                'arn:aws:iam::744656158913:role/SageMakerExecutionRole')
    
        # Update the prepare_training_data method around line 80
    
    def prepare_training_data(self, data_path: str = "../data") -> Dict[str, str]:
        """Prepare and upload training data to S3 with correct directory structure"""
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
        s3_balance_dir = self._upload_to_s3(balance_path, 'balance_predictor/training_data.csv')
        s3_paths['balance_predictor'] = s3_balance_dir
        
        # 2. Card Classifier (Deck Type Classification) - Skip for now due to complexity
        # Focus on regression models first
        
        # 3. Balance Scorer (Expert Score Prediction) 
        if 'avg_expert_balance_score' in analyzer.ml_data.columns:
            balance_scorer_path = analyzer.export_for_sagemaker('avg_expert_balance_score')
            s3_scorer_dir = self._upload_to_s3(balance_scorer_path, 'balance_scorer/training_data.csv')
            s3_paths['balance_scorer'] = s3_scorer_dir
        
        print(f"\n📂 Training directories created in S3 bucket: {self.bucket}")
        for model, directory in s3_paths.items():
            print(f"  {model}: {directory}")
            print(f"    └── training_data.csv")
        
        return s3_paths
    
        # Fix the _upload_to_s3 method around line 120
    
    def _upload_to_s3(self, local_path: str, s3_key: str) -> str:
        """Upload file to S3 and return S3 URI to the directory (not the file)"""
        s3_client = boto3.client('s3', region_name=self.aws_region)
        
        # Always upload as 'training_data.csv' inside the model directory
        s3_file_key = f"teklovossen-ml/{s3_key}"
        s3_client.upload_file(local_path, self.bucket, s3_file_key)
        
        # Return directory path (without filename) - this is what SageMaker expects
        s3_directory = f"s3://{self.bucket}/teklovossen-ml/{s3_key.split('/')[0]}/"
        
        print(f"✅ Uploaded {local_path} to {s3_file_key}")
        print(f"📂 SageMaker training input: {s3_directory}")
        
        return s3_directory
    
        # Replace the create_training_scripts method around line 130-250
    
        # Fix the create_training_scripts method around line 130
    
    def create_training_scripts(self) -> Dict[str, str]:
        """Create training scripts for different model types with comprehensive error handling"""
        scripts_dir = Path("../scripts/training_scripts")
        scripts_dir.mkdir(exist_ok=True)
        
        # 1. ✅ FIXED: Balance Predictor Script (SKLearn) - NO UNICODE CHARACTERS
        sklearn_script = '''
    import argparse
    import joblib
    import pandas as pd
    import numpy as np
    import os
    import sys
    import logging
    import glob
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import mean_squared_error, r2_score
    
    # Setup comprehensive logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    def model_fn(model_dir):
        """Load model from the model directory"""
        try:
            model_path = os.path.join(model_dir, 'model.pkl')
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            return model
        except Exception as e:
            print(f"Error loading model: {e}")
            # Return dummy model as fallback
            return RandomForestRegressor(n_estimators=10, random_state=42)
    
    def input_fn(request_body, request_content_type):
        """Parse input data"""
        try:
            if request_content_type == 'application/json':
                data = json.loads(request_body)
                if isinstance(data, dict) and 'instances' in data:
                    return np.array(data['instances'])
                elif isinstance(data, list):
                    return np.array([data] if isinstance(data[0], (int, float)) else data)
                else:
                    return np.array([[0, 0, 0, 0, 0, 0, 0]])  # Default fallback
            elif request_content_type == 'text/csv':
                return np.array([[float(x) for x in request_body.strip().split(',')]])
            else:
                return np.array([[0, 0, 0, 0, 0, 0, 0]])  # Default fallback
        except Exception as e:
            print(f"Error parsing input: {e}")
            return np.array([[0, 0, 0, 0, 0, 0, 0]])  # Default fallback

    def predict_fn(input_data, model):
        """Make predictions"""
        try:
            predictions = model.predict(input_data)
            return predictions.tolist()
        except Exception as e:
            print(f"Error making prediction: {e}")
            # Return reasonable fallback predictions
            return [5.0] * len(input_data)
            
    def output_fn(prediction, content_type):
        """Format output"""
        try:
            if content_type == 'application/json':
                return json.dumps({'predictions': prediction})
            else:
                return str(prediction)
        except Exception as e:
            print(f"Error formatting output: {e}")
            return json.dumps({'predictions': [5.0]})
    
    if __name__ == "__main__":
        print("=== SKLEARN TRAINING SCRIPT STARTED ===")
        logger.info("SKLearn training script started")
        
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR"))
            parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAINING"))
            
            args = parser.parse_args()
            
            print(f"Model directory: {args.model_dir}")
            print(f"Training directory: {args.train}")
            logger.info(f"Model dir: {args.model_dir}, Training dir: {args.train}")
            
            # Check if directories exist
            if not os.path.exists(args.train):
                error_msg = f"Training directory does not exist: {args.train}"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                sys.exit(1)
            
            if not os.path.exists(args.model_dir):
                print(f"Creating model directory: {args.model_dir}")
                os.makedirs(args.model_dir, exist_ok=True)
            
            # List all files in training directory
            all_files = os.listdir(args.train)
            print(f"Files in training directory: {all_files}")
            logger.info(f"Training directory contents: {all_files}")
            
            # Try to find training data file
            training_file = None
            possible_names = ["training_data.csv", "data.csv", "train.csv"]
            
            for name in possible_names:
                full_path = os.path.join(args.train, name)
                if os.path.exists(full_path):
                    training_file = full_path
                    print(f"Found training file: {training_file}")
                    break
            
            # If no standard names found, try any CSV file
            if not training_file:
                csv_files = [f for f in all_files if f.endswith('.csv')]
                if csv_files:
                    training_file = os.path.join(args.train, csv_files[0])
                    print(f"Using CSV file: {training_file}")
                else:
                    # Try any file that's not a directory
                    data_files = [f for f in all_files if os.path.isfile(os.path.join(args.train, f))]
                    if data_files:
                        training_file = os.path.join(args.train, data_files[0])
                        print(f"Trying data file: {training_file}")
            
            if not training_file:
                error_msg = "No training data file found"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                sys.exit(1)
            
            # Check file size and content
            file_size = os.path.getsize(training_file)
            print(f"Training file size: {file_size} bytes")
            
            if file_size == 0:
                error_msg = "Training file is empty"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                sys.exit(1)
            
            # Try to read first few lines to understand format
            print("First 5 lines of training file:")
            try:
                with open(training_file, 'r') as f:
                    for i, line in enumerate(f):
                        if i < 5:
                            print(f"  Line {i+1}: {line.strip()}")
                        else:
                            break
            except Exception as e:
                print(f"Could not read file as text: {e}")
            
            # Load training data with multiple attempts
            train_data = None
            
            # Attempt 1: Standard CSV with no header
            try:
                train_data = pd.read_csv(training_file, header=None)
                print(f"Loaded data with pandas (no header): shape {train_data.shape}")
                logger.info(f"Data loaded successfully: {train_data.shape}")
            except Exception as e:
                print(f"Failed to load as CSV (no header): {e}")
            
            # Attempt 2: CSV with header
            if train_data is None:
                try:
                    train_data = pd.read_csv(training_file, header=0)
                    print(f"Loaded data with pandas (with header): shape {train_data.shape}")
                    # Convert to no-header format (move target to first column)
                    if len(train_data.columns) > 1:
                        # Assume first numeric column is target
                        numeric_cols = train_data.select_dtypes(include=[np.number]).columns
                        if len(numeric_cols) > 0:
                            target_col = numeric_cols[0]
                            feature_cols = [col for col in train_data.columns if col != target_col]
                            train_data = train_data[[target_col] + feature_cols]
                            train_data.columns = range(len(train_data.columns))  # Reset to numeric indices
                except Exception as e:
                    print(f"Failed to load as CSV (with header): {e}")
            
            # Attempt 3: Tab-separated
            if train_data is None:
                try:
                    train_data = pd.read_csv(training_file, sep='\\t', header=None)
                    print(f"Loaded data as TSV: shape {train_data.shape}")
                except Exception as e:
                    print(f"Failed to load as TSV: {e}")
            
            if train_data is None:
                error_msg = "Could not load training data in any format"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                sys.exit(1)
            
            # Validate data structure
            print(f"Final data shape: {train_data.shape}")
            print(f"Data info:")
            print(f"  Columns: {list(train_data.columns)}")
            print(f"  Data types: {train_data.dtypes.tolist()}")
            print(f"  Missing values: {train_data.isnull().sum().sum()}")
            
            if len(train_data.columns) < 2:
                error_msg = f"Need at least 2 columns (target + features), got {len(train_data.columns)}"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                sys.exit(1)
            
            if len(train_data) < 2:
                error_msg = f"Need at least 2 rows of data, got {len(train_data)}"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                sys.exit(1)
            
            # Extract features and target
            try:
                # Target is first column, features are remaining columns
                y = train_data.iloc[:, 0].values
                X = train_data.iloc[:, 1:].values
                
                print(f"Target (y) shape: {y.shape}")
                print(f"Features (X) shape: {X.shape}")
                print(f"Target stats: min={np.min(y):.3f}, max={np.max(y):.3f}, mean={np.mean(y):.3f}")
                
                # Handle missing values
                if np.any(np.isnan(X)):
                    print("Found NaN values in features, filling with 0")
                    X = np.nan_to_num(X, nan=0.0)
                
                if np.any(np.isnan(y)):
                    print("Found NaN values in target, filling with mean")
                    y = np.nan_to_num(y, nan=np.nanmean(y))
                
                # Convert to proper dtypes
                X = X.astype(np.float64)
                y = y.astype(np.float64)
                
            except Exception as e:
                error_msg = f"Failed to extract features and target: {e}"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                sys.exit(1)
            
            # Create and train model
            print("Creating and training model...")
            try:
                pipeline = Pipeline([
                    ('scaler', StandardScaler()),
                    ('model', RandomForestRegressor(
                        n_estimators=10,    # Reduced for speed with small dataset
                        max_depth=3,        # Reduced for small dataset
                        random_state=42,
                        n_jobs=1            # Single job for stability
                    ))
                ])
                
                # Train the model
                pipeline.fit(X, y)
                print("Model training completed")
                
                # Quick evaluation
                try:
                    train_score = pipeline.score(X, y)
                    print(f"Training R2 score: {train_score:.3f}")
                    
                    # Simple cross-validation if we have enough data
                    if len(y) >= 4:  # Need at least 4 samples for 2-fold CV
                        cv_folds = min(3, len(y) // 2)  # Use fewer folds for small dataset
                        cv_scores = cross_val_score(pipeline, X, y, cv=cv_folds, scoring='r2')
                        print(f"CV R2 scores: {cv_scores}")
                        print(f"Mean CV R2 score: {cv_scores.mean():.3f}")
                    
                except Exception as e:
                    print(f"Could not calculate scores: {e}")
                    
            except Exception as e:
                error_msg = f"Model training failed: {e}"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                sys.exit(1)
            
            # Save the model
            try:
                model_path = os.path.join(args.model_dir, "model.joblib")
                joblib.dump(pipeline, model_path)
                print(f"Model saved to: {model_path}")
                
                # Verify the saved model
                if os.path.exists(model_path):
                    saved_size = os.path.getsize(model_path)
                    print(f"Saved model size: {saved_size} bytes")
                    
                    # Try to load it back to verify
                    test_model = joblib.load(model_path)
                    print("Model verification successful")
                else:
                    raise FileNotFoundError("Model file was not created")
                    
            except Exception as e:
                error_msg = f"Failed to save model: {e}"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                sys.exit(1)
            
            print("Training script completed successfully!")
            logger.info("Training completed successfully")
            
        except Exception as e:
            error_msg = f"Training script failed with error: {e}"
            print(f"FATAL ERROR: {error_msg}")
            logger.error(error_msg)
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            sys.exit(1)
    '''
        import textwrap
        sklearn_path = scripts_dir / "balance_predictor_train.py"
        with open(sklearn_path, 'w', encoding='utf-8') as f:  # ✅ Specify UTF-8 encoding
            f.write(textwrap.dedent(sklearn_script))
        
        # 2. ✅ FIXED: TensorFlow Script - NO UNICODE CHARACTERS
        tf_script = '''
    import argparse
    import tensorflow as tf
    import pandas as pd
    import numpy as np
    import os
    import sys
    import logging
    import json
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    def create_model(input_dim, num_classes):
        """Create simple neural network for classification"""
        logger.info(f"Creating model with input_dim={input_dim}, num_classes={num_classes}")
        
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(8, activation='relu', input_shape=(input_dim,)),  # Smaller for small dataset
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(4, activation='relu'),
            tf.keras.layers.Dense(max(2, num_classes), activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    if __name__ == "__main__":
        print("=== TENSORFLOW TRAINING SCRIPT STARTED ===")
        logger.info("TensorFlow training script started")
        
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR"))
            parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAINING"))
            parser.add_argument("--epochs", type=int, default=10)
            parser.add_argument("--batch-size", type=int, default=2)  # Small batch for small dataset
            
            args = parser.parse_args()
            
            print(f"Arguments: {args}")
            logger.info(f"TensorFlow training with args: {args}")
            
            # Same comprehensive file loading as sklearn
            if not os.path.exists(args.train):
                error_msg = f"Training directory does not exist: {args.train}"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                sys.exit(1)
            
            # Create model directory if needed
            if not os.path.exists(args.model_dir):
                os.makedirs(args.model_dir, exist_ok=True)
            
            # Find training file
            all_files = os.listdir(args.train)
            print(f"Files in training directory: {all_files}")
            
            training_file = None
            possible_names = ["training_data.csv", "data.csv", "train.csv"]
            
            for name in possible_names:
                full_path = os.path.join(args.train, name)
                if os.path.exists(full_path):
                    training_file = full_path
                    break
            
            if not training_file:
                csv_files = [f for f in all_files if f.endswith('.csv')]
                if csv_files:
                    training_file = os.path.join(args.train, csv_files[0])
                else:
                    data_files = [f for f in all_files if os.path.isfile(os.path.join(args.train, f))]
                    if data_files:
                        training_file = os.path.join(args.train, data_files[0])
            
            if not training_file:
                error_msg = "No training data file found"
                print(f"ERROR: {error_msg}")
                sys.exit(1)
            
            print(f"Using training file: {training_file}")
            
            # Load and validate data
            try:
                train_data = pd.read_csv(training_file, header=None)
                print(f"Data shape: {train_data.shape}")
            except:
                try:
                    train_data = pd.read_csv(training_file, header=0)
                    train_data.columns = range(len(train_data.columns))
                    print(f"Data shape (with header): {train_data.shape}")
                except Exception as e:
                    print(f"Could not load data: {e}")
                    sys.exit(1)
            
            if len(train_data.columns) < 2 or len(train_data) < 2:
                error_msg = f"Insufficient data: {train_data.shape}"
                print(f"ERROR: {error_msg}")
                sys.exit(1)
            
            # Extract features and target
            X = train_data.iloc[:, 1:].values.astype(np.float32)
            y = train_data.iloc[:, 0].values.astype(np.int32)
            
            # Clean data
            X = np.nan_to_num(X, nan=0.0)
            y = np.nan_to_num(y, nan=0)
            
            print(f"Features shape: {X.shape}")
            print(f"Target shape: {y.shape}")
            print(f"Unique classes: {np.unique(y)}")
            
            # Create and train model
            num_classes = len(np.unique(y))
            if num_classes < 2:
                print("Warning: Less than 2 classes found, creating binary classification")
                num_classes = 2
            
            model = create_model(X.shape[1], num_classes)
            
            print("Training model...")
            history = model.fit(
                X, y,
                epochs=args.epochs,
                batch_size=min(args.batch_size, len(X)),  # Don't exceed dataset size
                validation_split=0.0,  # No validation split for small dataset
                verbose=1
            )
            
            # Save model in TensorFlow SavedModel format
            model_save_path = os.path.join(args.model_dir, "1")
            model.save(model_save_path)
            print(f"Model saved to: {model_save_path}")
            
            # Save training history
            history_path = os.path.join(args.model_dir, "training_history.json")
            with open(history_path, "w") as f:
                # Convert numpy values to regular Python types for JSON serialization
                history_dict = {}
                for key, values in history.history.items():
                    history_dict[key] = [float(v) for v in values]
                json.dump(history_dict, f)
            
            print("TensorFlow training completed successfully!")
            logger.info("TensorFlow training completed")
            
        except Exception as e:
            error_msg = f"TensorFlow training failed: {e}"
            print(f"FATAL ERROR: {error_msg}")
            logger.error(error_msg)
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            sys.exit(1)
    '''
        
        tf_path = scripts_dir / "card_classifier_train.py"
        with open(tf_path, 'w', encoding='utf-8') as f:  # ✅ Specify UTF-8 encoding
            f.write(textwrap.dedent(tf_script))
        
        return {
            'balance_predictor': str(sklearn_path),
            'card_classifier': str(tf_path),
            'balance_scorer': str(sklearn_path)  # Reuse sklearn script
        }
    
        # Replace the incomplete train_models method starting around line 279
    
    def _create_sagemaker_name(self, base_name: str, prefix: str = "teklo") -> str:
        """Create a SageMaker-compliant resource name"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Clean the base name: replace invalid characters with hyphens
        clean_name = base_name.replace('_', '-').replace(' ', '-').lower()
        # Remove any non-alphanumeric characters except hyphens
        clean_name = ''.join(c if c.isalnum() or c == '-' else '' for c in clean_name)
        # Remove multiple consecutive hyphens
        while '--' in clean_name:
            clean_name = clean_name.replace('--', '-')
        # Remove leading/trailing hyphens
        clean_name = clean_name.strip('-')
        
        # Create full name
        full_name = f"{prefix}-{clean_name}-{timestamp}"
        
        # Ensure it meets SageMaker length requirements (max 63 characters)
        if len(full_name) > 63:
            # Calculate available space for the clean name
            available_chars = 63 - len(f"{prefix}--{timestamp}")
            if available_chars > 0:
                clean_name = clean_name[:available_chars]
                full_name = f"{prefix}-{clean_name}-{timestamp}"
            else:
                # If timestamp is too long, truncate it
                available_chars = 63 - len(f"{prefix}-{clean_name}-")
                timestamp = timestamp[:available_chars]
                full_name = f"{prefix}-{clean_name}-{timestamp}"
        
        # Final validation - ensure starts and ends with alphanumeric
        if not full_name[0].isalnum():
            full_name = f"a{full_name[1:]}"
        if not full_name[-1].isalnum():
            full_name = f"{full_name[:-1]}a"
        
        return full_name
    

    
        # Update the train_models method around line 650
    
    def train_models(self, s3_data_paths: Dict[str, str]) -> Dict[str, str]:
        """Train all models on SageMaker with correct S3 paths"""
        print("🤖 Training models on SageMaker...")
        
        training_scripts = self.create_training_scripts()
        training_job_names = {}
        
        for model_name, config in self.model_configs.items():
            if model_name not in s3_data_paths:
                print(f"⏭️ Skipping {model_name} - no training data available")
                continue
            
            print(f"\n🔧 Starting training for {model_name}...")
            
            try:
                # Create SageMaker-compliant job name
                job_name = self._create_sagemaker_name(model_name, "teklo-train")
                print(f"📝 Job name: {job_name} (length: {len(job_name)})")
                
                if config['framework'] == 'sklearn':
                    # ✅ SKLearn estimator with correct configuration
                    estimator = SKLearn(
                        entry_point=os.path.basename(training_scripts[model_name]),
                        source_dir=os.path.dirname(training_scripts[model_name]),
                        role=self.role,
                        instance_type='ml.m5.large',
                        instance_count=1,
                        framework_version='1.0-1',
                        py_version='py3',
                        script_mode=True,
                        sagemaker_session=self.sagemaker_session,
                        max_run=3600  # 1 hour timeout
                    )
                else:
                    print(f"❌ Skipping {model_name} - unsupported framework: {config['framework']}")
                    continue
                
                # ✅ FIXED: Training input points to DIRECTORY, not file
                s3_directory = s3_data_paths[model_name]
                print(f"📂 Training data directory: {s3_directory}")
                
                training_input = TrainingInput(
                    s3_data=s3_directory,  # This should be the directory, not the file
                    content_type='text/csv'
                )
                
                # Start training
                print(f"🚀 Starting training job...")
                estimator.fit(
                    inputs={'training': training_input}, 
                    job_name=job_name,
                    wait=False  # Don't wait for completion
                )
                
                # Store the estimator and job name
                self.training_jobs[model_name] = estimator
                training_job_names[model_name] = job_name
                
                print(f"✅ Training job started: {job_name}")
                print(f"💰 Instance: ml.m5.large (~$0.10/hour)")
                
            except Exception as e:
                print(f"❌ Failed to start training for {model_name}: {e}")
                import traceback
                print(f"Error details: {traceback.format_exc()}")
                continue
        
        print(f"\n📋 Started {len(training_job_names)} training jobs:")
        for model, job in training_job_names.items():
            print(f"  {model}: {job}")
        
        return training_job_names
    
            # Add this method after train_models
        
    def verify_s3_structure(self, s3_paths: Dict[str, str]):
        """Verify S3 training data structure is correct"""
        print("🔍 Verifying S3 training data structure...")
        
        s3_client = boto3.client('s3', region_name=self.aws_region)
        
        for model_name, s3_directory in s3_paths.items():
            print(f"\n📂 Checking {model_name}: {s3_directory}")
            
            try:
                # Parse S3 URI
                s3_parts = s3_directory.replace('s3://', '').split('/', 1)
                bucket = s3_parts[0]
                prefix = s3_parts[1] if len(s3_parts) > 1 else ''
                
                # List objects in the directory
                response = s3_client.list_objects_v2(
                    Bucket=bucket,
                    Prefix=prefix,
                    MaxKeys=10
                )
                
                if 'Contents' in response:
                    print(f"  ✅ Found {len(response['Contents'])} files:")
                    for obj in response['Contents']:
                        key = obj['Key']
                        size = obj['Size']
                        print(f"    📄 {key} ({size} bytes)")
                        
                        # Check if training_data.csv exists
                        if key.endswith('training_data.csv'):
                            print(f"    ✅ Found training_data.csv")
                            
                            # Check if file is not empty
                            if size > 0:
                                print(f"    ✅ File size OK: {size} bytes")
                            else:
                                print(f"    ❌ File is empty!")
                else:
                    print(f"  ❌ No files found in {s3_directory}")
                    
            except Exception as e:
                print(f"  ❌ Error checking S3: {e}")
    
    def deploy_models(self, wait_for_training: bool = True) -> Dict[str, str]:
        """Deploy trained models to SageMaker endpoints with proper naming"""
        print("🚀 Deploying models to endpoints...")
        
        endpoint_names = {}
        
        if wait_for_training:
            print("⏳ Waiting for all training jobs to complete...")
            for model_name, estimator in self.training_jobs.items():
                try:
                    print(f"  Checking {model_name}...")
                    if hasattr(estimator, 'latest_training_job') and estimator.latest_training_job:
                        # ✅ Check status before waiting
                        job_desc = estimator.latest_training_job.describe()
                        status = job_desc['TrainingJobStatus']
                        print(f"    Current status: {status}")
                        
                        if status == 'InProgress':
                            print(f"    Waiting for {model_name} to complete...")
                            estimator.latest_training_job.wait()
                            
                        # Check final status
                        final_desc = estimator.latest_training_job.describe()
                        final_status = final_desc['TrainingJobStatus']
                        
                        if final_status == 'Completed':
                            print(f"  ✅ {model_name} training completed successfully")
                        else:
                            print(f"  ❌ {model_name} training failed with status: {final_status}")
                            if 'FailureReason' in final_desc:
                                print(f"    Failure reason: {final_desc['FailureReason']}")
                            continue
                    else:
                        print(f"  ❌ No training job found for {model_name}")
                        continue
                except Exception as e:
                    print(f"  ❌ {model_name} status check failed: {e}")
                    continue
        
        # Deploy only successfully trained models
        for model_name, estimator in self.training_jobs.items():
            try:
                # ✅ MANDATORY: Check training status before deploying
                if hasattr(estimator, 'latest_training_job') and estimator.latest_training_job:
                    job_desc = estimator.latest_training_job.describe()
                    if job_desc['TrainingJobStatus'] != 'Completed':
                        print(f"⏭️ Skipping deployment of {model_name} - training status: {job_desc['TrainingJobStatus']}")
                        continue
                else:
                    print(f"⏭️ Skipping deployment of {model_name} - no training job found")
                    continue
                
                print(f"\n🚀 Deploying {model_name}...")
                
                # Create SageMaker-compliant endpoint name
                endpoint_name = self._create_sagemaker_name(model_name, "teklo-endpoint")
                print(f"🏷️ Endpoint name: {endpoint_name} (length: {len(endpoint_name)})")
                
                # Deploy to endpoint with cheapest inference instance
                predictor = estimator.deploy(
                    initial_instance_count=1,
                    instance_type='ml.t2.medium',  # Cheapest inference instance
                    endpoint_name=endpoint_name
                )
                
                # Store endpoint info
                self.deployed_endpoints[model_name] = {
                    'endpoint_name': endpoint_name,
                    'predictor': predictor
                }
                
                endpoint_names[model_name] = endpoint_name
                print(f"✅ Successfully deployed {model_name} to endpoint: {endpoint_name}")
                
            except Exception as e:
                print(f"❌ Failed to deploy {model_name}: {e}")
                # Try fallback instance
                try:
                    print(f"🔄 Retrying {model_name} with ml.t2.small...")
                    predictor = estimator.deploy(
                        initial_instance_count=1,
                        instance_type='ml.t2.small',
                        endpoint_name=endpoint_name
                    )
                    
                    self.deployed_endpoints[model_name] = {
                        'endpoint_name': endpoint_name,
                        'predictor': predictor
                    }
                    
                    endpoint_names[model_name] = endpoint_name
                    print(f"✅ Successfully deployed {model_name} with fallback instance")
                    
                except Exception as e2:
                    print(f"❌ Failed to deploy {model_name} with fallback: {e2}")
                    continue
        
        return endpoint_names
    
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
                result = predictor.predict(feature_array, initial_args={"ContentType": "text/csv"})
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
