
import argparse
import joblib
import pandas as pd
import numpy as np
import os
import sys
import logging
import json
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score

# Setup comprehensive logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def model_fn(model_dir):
    """Load model from the model directory - FIXED VERSION"""
    try:
        print(f"Loading model from directory: {model_dir}")

        # Check all files in model directory
        if os.path.exists(model_dir):
            files = os.listdir(model_dir)
            print(f"Files in model directory: {files}")
        else:
            print(f"Model directory does not exist: {model_dir}")
            raise FileNotFoundError(f"Model directory not found: {model_dir}")

        # Try multiple possible model file names and formats
        model_files = [
            'model.joblib',
            'model.pkl', 
            'model.pickle',
            'trained_model.joblib',
            'trained_model.pkl'
        ]

        model = None
        for model_file in model_files:
            model_path = os.path.join(model_dir, model_file)
            if os.path.exists(model_path):
                print(f"Found model file: {model_path}")
                try:
                    if model_file.endswith('.joblib'):
                        model = joblib.load(model_path)
                        print(f"Successfully loaded model with joblib from {model_path}")
                    else:
                        with open(model_path, 'rb') as f:
                            model = pickle.load(f)
                        print(f"Successfully loaded model with pickle from {model_path}")
                    break
                except Exception as e:
                    print(f"Failed to load {model_path}: {e}")
                    continue

        if model is None:
            raise FileNotFoundError("No valid model file found in model directory")

        # Verify the model is trained
        if hasattr(model, 'named_steps'):
            # It's a pipeline
            rf_model = model.named_steps.get('model')
            if rf_model and hasattr(rf_model, 'n_features_in_'):
                print(f"Model is trained with {rf_model.n_features_in_} features")
            else:
                raise ValueError("Pipeline model is not properly trained")
        elif hasattr(model, 'n_features_in_'):
            print(f"Model is trained with {model.n_features_in_} features")
        else:
            raise ValueError("Model appears to be untrained (no n_features_in_ attribute)")

        return model

    except Exception as e:
        print(f"CRITICAL ERROR loading model: {e}")
        print("This will cause prediction failures!")
        # Instead of returning dummy model, raise the error
        raise e

def input_fn(request_body, request_content_type):
    """Parse input data - IMPROVED VERSION"""
    try:
        print(f"Parsing input with content type: {request_content_type}")
        print(f"Request body: {request_body}")

        if request_content_type == 'application/json':
            data = json.loads(request_body)
            print(f"Parsed JSON data: {data}")

            if isinstance(data, dict) and 'instances' in data:
                input_array = np.array(data['instances'])
            elif isinstance(data, dict) and 'data' in data:
                input_array = np.array([data['data']])
            elif isinstance(data, list):
                if len(data) > 0 and isinstance(data[0], (int, float)):
                    # Single instance
                    input_array = np.array([data])
                else:
                    # Multiple instances
                    input_array = np.array(data)
            else:
                raise ValueError(f"Unexpected JSON format: {data}")

        elif request_content_type == 'text/csv':
            # Parse CSV input
            lines = request_body.strip().split('\n')
            data_rows = []
            for line in lines:
                if line.strip():
                    row = [float(x.strip()) for x in line.split(',')]
                    data_rows.append(row)
            input_array = np.array(data_rows)

        else:
            raise ValueError(f"Unsupported content type: {request_content_type}")

        print(f"Final input array shape: {input_array.shape}")
        return input_array

    except Exception as e:
        print(f"ERROR parsing input: {e}")
        print(f"Content type: {request_content_type}")
        print(f"Request body: {request_body}")
        raise e

def predict_fn(input_data, model):
    """Make predictions - IMPROVED VERSION"""
    try:
        print(f"Making prediction with input shape: {input_data.shape}")

        # Verify model is trained
        if hasattr(model, 'named_steps'):
            rf_model = model.named_steps.get('model')
            if rf_model and not hasattr(rf_model, 'n_features_in_'):
                raise ValueError("Pipeline model is not trained")
        elif not hasattr(model, 'n_features_in_'):
            raise ValueError("Model is not trained")

        predictions = model.predict(input_data)
        print(f"Raw predictions: {predictions}")

        # Convert to list for JSON serialization
        pred_list = predictions.tolist()
        print(f"Converted predictions: {pred_list}")

        return pred_list

    except Exception as e:
        print(f"ERROR making prediction: {e}")
        print(f"Model type: {type(model)}")
        print(f"Input data shape: {input_data.shape}")
        print(f"Model attributes: {dir(model)}")
        raise e

def output_fn(prediction, content_type):
    """Format output - IMPROVED VERSION"""
    try:
        print(f"Formatting output: {prediction} with content type: {content_type}")

        if content_type == 'application/json':
            result = {'predictions': prediction}
            output = json.dumps(result)
        else:
            output = str(prediction)

        print(f"Final output: {output}")
        return output

    except Exception as e:
        print(f"ERROR formatting output: {e}")
        raise e

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
                train_data = pd.read_csv(training_file, sep='\t', header=None)
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
                    n_estimators=20,    # Increased slightly for better performance
                    max_depth=5,        # Increased for better fit
                    random_state=42,
                    n_jobs=1            # Single job for stability
                ))
            ])

            # Train the model
            print("Fitting model...")
            pipeline.fit(X, y)
            print("Model training completed successfully!")

            # Verify the model is trained
            rf_model = pipeline.named_steps['model']
            print(f"Model trained with {rf_model.n_features_in_} features")
            print(f"Model has {rf_model.n_estimators} estimators")

            # Quick evaluation
            try:
                train_score = pipeline.score(X, y)
                print(f"Training R2 score: {train_score:.3f}")

                # Test a prediction to make sure everything works
                test_pred = pipeline.predict(X[:1])
                print(f"Test prediction: {test_pred}")

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

        # Save the model with BOTH formats for maximum compatibility
        try:
            # Primary save format: joblib
            model_path_joblib = os.path.join(args.model_dir, "model.joblib")
            joblib.dump(pipeline, model_path_joblib)
            print(f"Model saved with joblib to: {model_path_joblib}")

            # Backup save format: pickle
            model_path_pickle = os.path.join(args.model_dir, "model.pkl")
            with open(model_path_pickle, 'wb') as f:
                pickle.dump(pipeline, f)
            print(f"Model saved with pickle to: {model_path_pickle}")

            # Verify both saved models work
            for path, loader in [(model_path_joblib, joblib.load), (model_path_pickle, lambda p: pickle.load(open(p, 'rb')))]:
                if os.path.exists(path):
                    saved_size = os.path.getsize(path)
                    print(f"Saved model size ({os.path.basename(path)}): {saved_size} bytes")

                    if saved_size > 0:
                        # Try to load it back to verify
                        test_model = loader(path)
                        test_pred = test_model.predict(X[:1])
                        print(f"Model verification successful for {os.path.basename(path)}: {test_pred}")
                    else:
                        print(f"WARNING: {os.path.basename(path)} is empty!")
                else:
                    print(f"ERROR: {os.path.basename(path)} was not created")

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
