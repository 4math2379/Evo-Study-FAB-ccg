"""
Teklovossen Data Science Environment Setup
Automated setup script for the ML pipeline environment
"""

import subprocess
import sys
from pathlib import Path
import json


def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    
    requirements_file = Path("../requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
        print("✅ Python requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False


def create_aws_credentials_template():
    """Create AWS credentials template"""
    print("Creating AWS credentials template...")
    
    credentials_template = {
        "aws_access_key_id": "YOUR_ACCESS_KEY_HERE",
        "aws_secret_access_key": "YOUR_SECRET_KEY_HERE",
        "region": "us-east-1",
        "sagemaker_execution_role": "arn:aws:iam::YOUR_ACCOUNT:role/SageMakerExecutionRole"
    }
    
    config_dir = Path("../config")
    config_dir.mkdir(exist_ok=True)
    
    credentials_file = config_dir / "aws_credentials_template.json"
    
    with open(credentials_file, 'w') as f:
        json.dump(credentials_template, f, indent=2)
    
    print(f"✅ AWS credentials template created at: {credentials_file}")
    print("   Please update with your actual AWS credentials")


def create_jupyter_config():
    """Create Jupyter configuration"""
    print("Setting up Jupyter configuration...")
    
    try:
        # Enable extensions
        subprocess.run([sys.executable, "-m", "jupyter", "nbextension", "enable", "--py", "widgetsnbextension"])
        print("✅ Jupyter widgets enabled")
    except Exception as e:
        print(f"⚠️  Jupyter widget setup failed: {e}")


def run_initial_tests():
    """Run basic tests to ensure everything is working"""
    print("Running initial tests...")
    
    try:
        # Test imports
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns
        import sklearn
        print("✅ Core libraries imported successfully")
        
        # Test data directories
        data_dirs = ["../data/raw", "../data/processed", "../data/simulations"]
        for dir_path in data_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        print("✅ Data directories created/verified")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*60)
    print("🚀 SETUP COMPLETE! Next Steps:")
    print("="*60)
    
    print("\n1. 📝 Configure AWS (if using SageMaker):")
    print("   - Update config/aws_credentials_template.json with your AWS details")
    print("   - Ensure you have proper IAM permissions for SageMaker")
    
    print("\n2. 🎮 Start the simulation:")
    print("   - Run: jupyter notebook notebooks/gameplay_simulator.ipynb")
    print("   - Execute all cells to generate simulation data")
    
    print("\n3. 📊 Analyze results:")
    print("   - Run: python scripts/data_analytics.py")
    print("   - View comprehensive analysis and visualizations")
    
    print("\n4. 🤖 Train ML models (optional):")
    print("   - Configure AWS credentials")
    print("   - Run: python scripts/sagemaker_integration.py")
    
    print("\n5. 🔧 Available notebooks:")
    print("   - notebooks/gameplay_simulator.ipynb - Main simulation notebook")
    print("   - teklostudyv1.ipynb - Original card evaluation notebook")
    
    print("\n6. 📁 Key directories:")
    print("   - data/simulations/ - Generated gameplay data")
    print("   - data/processed/ - ML training data")
    print("   - models/ - Trained models")
    
    print("\n✨ Your Teklovossen ML environment is ready!")
    print("   Visit the README.md for detailed documentation")


def main():
    """Main setup function"""
    print("🔧 Setting up Teklovossen Data Science Environment")
    print("="*55)
    
    success = True
    
    # Install requirements
    if not install_requirements():
        success = False
    
    # Create templates
    create_aws_credentials_template()
    
    # Configure Jupyter
    create_jupyter_config()
    
    # Run tests
    if not run_initial_tests():
        success = False
    
    # Create simulation module init file
    simulation_dir = Path("../simulation")
    if simulation_dir.exists():
        init_file = simulation_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print("✅ Created simulation module __init__.py")
    
    if success:
        print_next_steps()
    else:
        print("\n❌ Setup completed with some errors.")
        print("   Please check the messages above and resolve any issues.")


if __name__ == "__main__":
    main()
