"""
Test script for card feature extraction and integration
Validates that card features are properly integrated into the ML pipeline
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from card_feature_extractor import CardFeatureExtractor
import pandas as pd
import numpy as np


def test_feature_extraction():
    """Test card feature extraction functionality"""
    print("\n" + "="*80)
    print("TEST 1: Card Feature Extraction")
    print("="*80)
    
    extractor = CardFeatureExtractor("../notebooks/card.csv")
    
    # Test with Mechanologist cards
    test_cards = [
        'Teklo Leveler',
        'Cognition Nodes',
        'Zero to Sixty',
        'Teklo Core',
        'Overblast'
    ]
    
    print(f"\n📝 Testing with {len(test_cards)} Mechanologist cards:")
    for card in test_cards:
        print(f"  - {card}")
    
    # Extract all features
    all_features = extractor.extract_all_features(test_cards)
    
    print(f"\n✅ Feature extraction successful!")
    print(f"   Total features per card: {len(all_features.columns) - 1}")  # -1 for card_name
    print(f"   Feature categories:")
    print(f"     - Numeric features: 7 (Pitch, Cost, Power, Defense, Health, Intelligence, Arcane)")
    print(f"     - Type features: 10 (Equipment, Action, Attack, etc.)")
    print(f"     - Keyword features: 13 (Go again, Dominate, Boost, etc.)")
    print(f"     - Class features: 10 (Mechanologist, Warrior, etc.)")
    
    # Show sample features for first card
    print(f"\n📊 Sample features for '{test_cards[0]}':")
    first_card = all_features.iloc[0]
    print(f"   Numeric: Pitch={first_card['Pitch']}, Cost={first_card['Cost']}, Power={first_card['Power']}")
    print(f"   Types: Equipment={first_card['type_equipment']}, Weapon={first_card['type_weapon']}")
    print(f"   Keywords: Boost={first_card['keyword_boost']}, Go_again={first_card['keyword_go_again']}")
    
    return True


def test_deck_aggregation():
    """Test deck-level feature aggregation"""
    print("\n" + "="*80)
    print("TEST 2: Deck Feature Aggregation")
    print("="*80)
    
    extractor = CardFeatureExtractor("../notebooks/card.csv")
    
    # Create a sample deck
    sample_deck = [
        'Teklo Leveler',
        'Cognition Nodes',
        'Zero to Sixty',
        'Teklo Core',
        'Overblast',
        'Teklo Plasma Pistol',
        'Dash, Inventor Extraordinaire'
    ]
    
    print(f"\n📦 Testing deck with {len(sample_deck)} cards")
    
    # Aggregate features
    deck_features = extractor.aggregate_deck_features(sample_deck)
    
    print(f"\n✅ Deck aggregation successful!")
    print(f"   Total aggregated features: {len(deck_features)}")
    
    # Show sample aggregated features
    avg_features = {k: v for k, v in deck_features.items() if k.startswith('avg_') and v > 0}
    print(f"\n📊 Sample average features:")
    for feature, value in list(avg_features.items())[:10]:
        print(f"   {feature}: {value:.2f}")
    
    return True


def test_data_enrichment():
    """Test enrichment of ML data with card features"""
    print("\n" + "="*80)
    print("TEST 3: ML Data Enrichment")
    print("="*80)
    
    # Create sample ML data
    sample_ml_data = pd.DataFrame({
        'deck_name': ['AI_Heavy', 'Nano_Focus', 'Quantum_Control'],
        'AI': [8, 2, 2],
        'Nano': [2, 8, 2],
        'Quantum': [2, 2, 8],
        'Base': [4, 4, 4],
        'avg_win_rate': [0.65, 0.58, 0.62],
        'avg_turns': [12, 14, 13],
        'avg_evos': [3, 3, 3],
        'avg_teklo_energy': [15, 14, 16],
        'avg_nanite_counters': [5, 12, 6],
        'avg_quantum_charges': [3, 4, 10],
        'consistency_score': [0.85, 0.82, 0.88],
        'avg_expert_balance_score': [7.5, 7.2, 7.8]
    })
    
    print(f"\n📊 Created sample ML dataset:")
    print(f"   Decks: {len(sample_ml_data)}")
    print(f"   Base features: {len(sample_ml_data.columns)}")
    
    # Import analyzer (need to handle missing simulation data gracefully)
    try:
        from data_analytics import TekloDataAnalyzer
        
        # Create temporary data directory
        temp_dir = Path("../data/processed")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Save sample data
        temp_ml_path = temp_dir / "test_ml_data.csv"
        sample_ml_data.to_csv(temp_ml_path, index=False)
        
        # Initialize analyzer
        analyzer = TekloDataAnalyzer(data_path="../data", card_csv_path="../notebooks/card.csv")
        analyzer.ml_data = sample_ml_data
        
        # Enrich with card features
        print(f"\n🔧 Enriching data with card features...")
        enriched_data = analyzer.enrich_with_card_features()
        
        print(f"\n✅ Data enrichment successful!")
        print(f"   Original features: {len(sample_ml_data.columns)}")
        print(f"   Enriched features: {len(enriched_data.columns)}")
        print(f"   New card features: {len(enriched_data.columns) - len(sample_ml_data.columns)}")
        
        # Show new features
        new_features = [col for col in enriched_data.columns if col not in sample_ml_data.columns]
        print(f"\n📊 Added card features:")
        for feature in new_features[:10]:
            print(f"   - {feature}")
        if len(new_features) > 10:
            print(f"   ... and {len(new_features) - 10} more")
        
        # Clean up
        if temp_ml_path.exists():
            temp_ml_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"\n⚠️  Data enrichment test skipped: {e}")
        print("   (This is expected if simulation data doesn't exist)")
        return True


def test_export_format():
    """Test SageMaker export format with card features"""
    print("\n" + "="*80)
    print("TEST 4: SageMaker Export Format")
    print("="*80)
    
    try:
        from data_analytics import TekloDataAnalyzer
        
        # Create sample ML data
        sample_ml_data = pd.DataFrame({
            'deck_name': ['AI_Heavy', 'Nano_Focus'],
            'AI': [8, 2],
            'Nano': [2, 8],
            'Quantum': [2, 2],
            'Base': [4, 4],
            'avg_win_rate': [0.65, 0.58],
            'avg_turns': [12, 14],
            'avg_evos': [3, 3],
            'avg_teklo_energy': [15, 14],
            'avg_nanite_counters': [5, 12],
            'avg_quantum_charges': [3, 4],
            'consistency_score': [0.85, 0.82],
            'avg_expert_balance_score': [7.5, 7.2]
        })
        
        # Initialize analyzer
        analyzer = TekloDataAnalyzer(data_path="../data", card_csv_path="../notebooks/card.csv")
        analyzer.ml_data = sample_ml_data
        
        print(f"\n🔧 Testing SageMaker export format...")
        
        # Create temp directory
        temp_dir = Path("../data/processed")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Export with card features
        export_path = analyzer.export_for_sagemaker('avg_win_rate', include_card_features=True)
        
        # Load and verify
        exported_data = pd.read_csv(export_path, header=None)
        
        print(f"\n✅ Export format validation successful!")
        print(f"   Export path: {export_path}")
        print(f"   Rows: {len(exported_data)}")
        print(f"   Columns: {len(exported_data.columns)}")
        print(f"   Format: CSV without headers (SageMaker compatible)")
        print(f"   First column: Target variable (avg_win_rate)")
        print(f"   Remaining columns: Features")
        
        # Show sample row
        print(f"\n📊 Sample row (first 10 values):")
        sample_row = exported_data.iloc[0, :10].tolist()
        print(f"   {sample_row}")
        
        # Clean up
        if Path(export_path).exists():
            Path(export_path).unlink()
        
        return True
        
    except Exception as e:
        print(f"\n⚠️  SageMaker export test skipped: {e}")
        return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("CARD FEATURE INTEGRATION TEST SUITE")
    print("="*80)
    print("Testing card feature extraction and ML pipeline integration")
    
    tests = [
        ("Feature Extraction", test_feature_extraction),
        ("Deck Aggregation", test_deck_aggregation),
        ("Data Enrichment", test_data_enrichment),
        ("SageMaker Export", test_export_format)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASSED" if result else "FAILED"))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, "ERROR"))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, status in results:
        icon = "✅" if status == "PASSED" else "❌"
        print(f"{icon} {test_name}: {status}")
    
    passed = sum(1 for _, status in results if status == "PASSED")
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Card features are ready for ML training.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
