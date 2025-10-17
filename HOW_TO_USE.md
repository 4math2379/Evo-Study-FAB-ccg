# How to Use the Teklovossen ML Pipeline

This guide walks you through using the simulation notebook and SageMaker features step by step.

## 🚀 Quick Start (5 minutes)

### Step 1: Environment Setup
```powershell
# Navigate to your project directory
cd D:\tekloStudy

# Run the automated setup
python scripts\setup_environment.py
```

This will:
- Install all required Python packages
- Create necessary directories
- Set up Jupyter configuration
- Create AWS credential templates

### Step 2: Start Jupyter
```powershell
jupyter notebook
```
This opens Jupyter in your browser. Navigate to `notebooks/gameplay_simulator.ipynb`

---

## 📊 Using the Simulation Notebook

### Opening the Notebook
1. In Jupyter, click on `notebooks/gameplay_simulator.ipynb`
2. The notebook will open with multiple sections

### Running Your First Simulation

#### Section 1: Basic Setup
```python
# This cell imports everything you need
# Just click "Run" or press Shift+Enter
```

#### Section 2: Card Database Setup
```python
# This creates your card database with all Teklovossen cards
# Shows you how many cards are loaded by theme
```

#### Section 3: Single Game Test
```python
# Runs one test game to make sure everything works
# You'll see output like:
# "Test game completed:"
# "  Deck: nano_focused"
# "  Winner: Teklovossen"
```

#### Section 4: Batch Simulation (The Main Event!)
```python
# This is where the magic happens
# Runs 25 games per deck type (100 total games)
# Takes about 2-3 minutes
simulation_results = run_batch_simulation(games_per_deck=25)
```

**What you'll see:**
```
Running batch simulation: 25 games per deck type...
  Simulating nano_focused...
    Game 1/25
    Game 11/25
    Game 21/25
  Simulating ai_focused...
    Game 1/25
...
Simulation completed with 100 games total
```

#### Section 5: Data Analysis and Visualizations
This creates beautiful charts showing:
- **Win rates by deck type** (bar charts and box plots)
- **Resource generation efficiency** (multi-series bar chart)
- **Game length vs win rate** (scatter plot)
- **Evo equipment usage** (violin plots)

#### Section 6: Advanced Analysis
- **Correlation matrix** showing relationships between metrics
- **Performance trends** over multiple games
- **Theme synergy heatmaps**

### Understanding the Results

**Key Metrics to Watch:**
- **Win Rate**: Higher is better (0.5 = 50% win rate)
- **Resource Efficiency**: Resources generated per turn
- **Consistency**: Lower variation in game length = more consistent
- **Evo Usage**: How many Evo cards were equipped per game

**Example Output:**
```
Deck Performance Summary:
                     win_rate  turns_played  evos_equipped
deck_name                                                 
ai_focused              0.64          8.2            1.4
balanced_mix            0.52          9.1            2.1
nano_focused            0.68          7.8            2.8
quantum_focused         0.44         10.3            1.9
```

---

## 🤖 Using AWS SageMaker (Advanced)

### Prerequisites
1. AWS Account with SageMaker access
2. IAM role with SageMaker permissions
3. S3 bucket for data storage

### Step 1: AWS Credentials Setup

#### Option A: Using AWS CLI (Recommended)
```powershell
# Install AWS CLI if you haven't
pip install awscli

# Configure your credentials
aws configure
```

#### Option B: Manual Configuration
1. Edit `config/aws_credentials_template.json`:
```json
{
  "aws_access_key_id": "YOUR_ACTUAL_ACCESS_KEY",
  "aws_secret_access_key": "YOUR_ACTUAL_SECRET_KEY", 
  "region": "us-east-1",
  "sagemaker_execution_role": "arn:aws:iam::YOUR_ACCOUNT_ID:role/SageMakerExecutionRole"
}
```

2. Rename it to `aws_credentials.json`

### Step 2: Create SageMaker Execution Role

In AWS Console:
1. Go to **IAM** → **Roles** → **Create Role**
2. Select **SageMaker** service
3. Attach policies:
   - `AmazonSageMakerFullAccess`
   - `AmazonS3FullAccess`
4. Name it `SageMakerExecutionRole`
5. Copy the ARN for your config file

### Step 3: Running SageMaker Training

```python
# In a new notebook or Python script
from scripts.sagemaker_integration import TekloSageMakerOrchestrator

# Initialize the orchestrator
orchestrator = TekloSageMakerOrchestrator(aws_region='us-east-1')

# Step 1: Prepare and upload training data
print("Uploading training data to S3...")
s3_paths = orchestrator.prepare_training_data()

# Step 2: Train models (this takes 10-20 minutes)
print("Starting model training...")
training_jobs = orchestrator.train_models(s3_paths)

# Step 3: Deploy models for predictions (5-10 minutes)
print("Deploying models...")
endpoints = orchestrator.deploy_models()
```

### Step 4: Making Predictions

```python
# Example: Predict balance for a new card combination
card_features = {
    'AI': 2,                    # 2 AI-themed cards
    'Nano': 3,                  # 3 Nano-themed cards  
    'Quantum': 0,               # 0 Quantum cards
    'Base': 5,                  # 5 base equipment cards
    '1_cost': 4,                # 4 cards costing 1 energy
    '2_cost': 3,                # 3 cards costing 2 energy
    '3_cost': 2,                # etc.
    'equipment': 7,             # 7 equipment cards
    'item': 3,                  # 3 item cards
    'avg_teklo_energy': 1.5,    # Expected energy generation
    'avg_expert_balance_score': 6.5
}

# Get predictions
predictions = orchestrator.predict_card_balance(card_features)

print("ML Predictions:")
print(f"Expected Win Rate: {predictions['balance_predictor']:.1%}")
print(f"Balance Score: {predictions['balance_scorer']:.1f}/10")

# Get recommendations
recommendations = orchestrator.generate_balance_recommendations(card_features)
print("\nRecommendations:")
for rec in recommendations['recommendations']:
    print(f"• {rec}")
```

**Example Output:**
```
ML Predictions:
Expected Win Rate: 62.3%
Balance Score: 7.2/10

Recommendations:
• ✅ High balance score - minor tweaks may improve competitive viability
• ⚡ High Teklo Energy generation - monitor for combo potential
```

---

## 🎯 Practical Use Cases

### Use Case 1: Testing a New Card Design

**Scenario**: You've designed a new Nano card and want to test its impact.

```python
# 1. First, run baseline simulation
baseline_results = run_batch_simulation(games_per_deck=50)

# 2. Add your new card to the database (modify card_database.py)
# 3. Run simulation again
new_results = run_batch_simulation(games_per_deck=50)

# 4. Compare win rates
print("Impact Analysis:")
print(f"Nano deck win rate change: {new_results['nano_focused'].mean() - baseline_results['nano_focused'].mean():.1%}")
```

### Use Case 2: Optimizing Deck Composition

```python
# Test different deck configurations
deck_variants = [
    {'AI': 4, 'Nano': 2, 'Base': 6},    # AI-heavy
    {'AI': 2, 'Nano': 4, 'Base': 6},    # Nano-heavy  
    {'AI': 3, 'Nano': 3, 'Base': 6},    # Balanced
]

for i, variant in enumerate(deck_variants):
    prediction = orchestrator.predict_card_balance(variant)
    print(f"Variant {i+1}: {prediction['balance_predictor']:.1%} win rate")
```

### Use Case 3: Balance Testing Pipeline

```python
def test_card_balance(card_name, modifications):
    """Complete balance testing pipeline"""
    
    # 1. Baseline measurement
    print(f"Testing {card_name} modifications...")
    
    # 2. Simulation analysis
    results = run_batch_simulation(games_per_deck=100)
    
    # 3. ML prediction
    ml_prediction = orchestrator.predict_card_balance(modifications)
    
    # 4. Statistical analysis
    analyzer = TekloDataAnalyzer()
    analyzer.load_simulation_data()
    metrics = analyzer.calculate_advanced_metrics()
    
    # 5. Generate report
    report = {
        'simulation_win_rate': results.groupby('deck_name')['win_rate'].mean(),
        'ml_prediction': ml_prediction,
        'statistical_significance': metrics['statistical_tests'],
        'recommendations': orchestrator.generate_balance_recommendations(modifications)
    }
    
    return report
```

---

## 🔧 Troubleshooting

### Common Issues

#### "Module not found" errors
```powershell
# Make sure you're in the right directory
cd D:\tekloStudy

# Install requirements again
pip install -r requirements.txt
```

#### Jupyter notebook won't start
```powershell
# Try installing Jupyter explicitly
pip install jupyter notebook

# Or use JupyterLab
pip install jupyterlab
jupyter lab
```

#### AWS/SageMaker errors
- Check your AWS credentials are correct
- Verify your IAM role has proper permissions
- Make sure you have SageMaker quotas available
- Check the AWS region is correct

#### "No simulation data found" 
- Run the simulation notebook first
- Check that files are created in `data/simulations/`
- Make sure the CSV files aren't empty

### Performance Tips

#### For faster simulations:
```python
# Reduce games per deck for testing
simulation_results = run_batch_simulation(games_per_deck=10)  # Instead of 25+

# Focus on specific deck types
# Modify the deck_presets dictionary to test fewer variants
```

#### For SageMaker cost optimization:
- Use smaller instance types: `ml.t2.medium` instead of `ml.m5.large`
- Delete endpoints when not in use: `orchestrator.cleanup_resources(delete_endpoints=True)`
- Use spot instances for training (advanced)

---

## 📈 Next Steps

Once you're comfortable with the basics:

1. **Expand the card database** with more cards from your designs
2. **Create custom deck presets** for specific strategies
3. **Modify game rules** in the simulation engine for new mechanics
4. **Add more ML models** for specific predictions (mana curve optimization, etc.)
5. **Set up automated testing** pipelines for continuous balance monitoring

## 🎓 Learning Resources

- **Jupyter Notebooks**: [Official Jupyter Documentation](https://jupyter.org/documentation)
- **AWS SageMaker**: [SageMaker Developer Guide](https://docs.aws.amazon.com/sagemaker/)
- **Data Science with Python**: [Pandas Documentation](https://pandas.pydata.org/docs/)

Happy card balancing! 🎯
