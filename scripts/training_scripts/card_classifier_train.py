
import argparse
import tensorflow as tf
import pandas as pd
import numpy as np
import os
import sys
import logging
import json
import pickle

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
