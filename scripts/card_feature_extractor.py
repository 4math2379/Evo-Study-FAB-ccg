"""
Card Feature Extractor for FAB Card Analysis
Extracts features from card.csv to enhance ML model predictions
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class CardFeatureExtractor:
    """Extract and engineer features from Flesh and Blood card data"""
    
    def __init__(self, card_csv_path: str = "../notebooks/card.csv"):
        """Initialize the feature extractor with card data"""
        self.card_csv_path = Path(card_csv_path)
        self.card_data: Optional[pd.DataFrame] = None
        self.feature_cache: Dict[str, Any] = {}
        
    def load_card_data(self) -> pd.DataFrame:
        """Load card data from CSV file"""
        try:
            self.card_data = pd.read_csv(self.card_csv_path, sep='\t')
            print(f"Loaded {len(self.card_data)} cards from {self.card_csv_path.name}")
            return self.card_data
        except Exception as e:
            print(f"Error loading card data: {e}")
            raise
    
    def extract_numeric_features(self, card_names: List[str]) -> pd.DataFrame:
        """Extract numeric features (Pitch, Cost, Power, Defense, etc.) for given cards"""
        if self.card_data is None:
            self.load_card_data()
        
        # Define numeric columns to extract
        numeric_cols = ['Pitch', 'Cost', 'Power', 'Defense', 'Health', 'Intelligence', 'Arcane']
        
        features = []
        for card_name in card_names:
            card_info = self.card_data[self.card_data['Name'] == card_name]
            
            if len(card_info) == 0:
                # Card not found, use default values
                features.append({col: 0.0 for col in numeric_cols})
            else:
                # Use first match if multiple versions exist
                card_row = card_info.iloc[0]
                feature_dict = {}
                
                for col in numeric_cols:
                    try:
                        val = card_row[col]
                        if pd.isna(val) or val == '*':
                            feature_dict[col] = 0.0
                        else:
                            feature_dict[col] = float(val)
                    except (ValueError, TypeError):
                        feature_dict[col] = 0.0
                
                features.append(feature_dict)
        
        return pd.DataFrame(features)
    
    def extract_type_features(self, card_names: List[str]) -> pd.DataFrame:
        """Extract card type features (Equipment, Action, Attack, etc.)"""
        if self.card_data is None:
            self.load_card_data()
        
        # Define important card types
        important_types = [
            'Equipment', 'Action', 'Attack', 'Instant', 'Aura', 'Item',
            'Weapon', 'Hero', 'Ally', 'Token'
        ]
        
        features = []
        for card_name in card_names:
            card_info = self.card_data[self.card_data['Name'] == card_name]
            
            if len(card_info) == 0:
                features.append({f'type_{t.lower()}': 0 for t in important_types})
            else:
                card_row = card_info.iloc[0]
                types_str = card_row['Types'] if pd.notna(card_row['Types']) else ''
                types_list = [t.strip() for t in str(types_str).split(',')]
                
                type_dict = {}
                for t in important_types:
                    type_dict[f'type_{t.lower()}'] = 1 if t in types_list else 0
                
                features.append(type_dict)
        
        return pd.DataFrame(features)
    
    def extract_keyword_features(self, card_names: List[str]) -> pd.DataFrame:
        """Extract keyword features (Go again, Dominate, Stealth, etc.)"""
        if self.card_data is None:
            self.load_card_data()
        
        # Define important keywords
        important_keywords = [
            'Go again', 'Dominate', 'Stealth', 'Combo', 'Boost',
            'Overpower', 'Blood Debt', 'Blade Break', 'Legendary',
            'Battleworn', 'Temper', 'Charge', 'Phantasm'
        ]
        
        features = []
        for card_name in card_names:
            card_info = self.card_data[self.card_data['Name'] == card_name]
            
            if len(card_info) == 0:
                features.append({f'keyword_{k.lower().replace(" ", "_")}': 0 for k in important_keywords})
            else:
                card_row = card_info.iloc[0]
                keywords_str = card_row['Card Keywords'] if pd.notna(card_row['Card Keywords']) else ''
                keywords_list = [k.strip() for k in str(keywords_str).split(',')]
                
                keyword_dict = {}
                for k in important_keywords:
                    keyword_dict[f'keyword_{k.lower().replace(" ", "_")}'] = 1 if k in keywords_list else 0
                
                features.append(keyword_dict)
        
        return pd.DataFrame(features)
    
    def extract_class_features(self, card_names: List[str]) -> pd.DataFrame:
        """Extract hero class features (Mechanologist, Warrior, Ninja, etc.)"""
        if self.card_data is None:
            self.load_card_data()
        
        # Define hero classes
        hero_classes = [
            'Mechanologist', 'Warrior', 'Ninja', 'Runeblade', 'Assassin',
            'Guardian', 'Brute', 'Illusionist', 'Ranger', 'Wizard'
        ]
        
        features = []
        for card_name in card_names:
            card_info = self.card_data[self.card_data['Name'] == card_name]
            
            if len(card_info) == 0:
                features.append({f'class_{c.lower()}': 0 for c in hero_classes})
            else:
                card_row = card_info.iloc[0]
                types_str = card_row['Types'] if pd.notna(card_row['Types']) else ''
                types_list = [t.strip() for t in str(types_str).split(',')]
                
                class_dict = {}
                for c in hero_classes:
                    class_dict[f'class_{c.lower()}'] = 1 if c in types_list else 0
                
                features.append(class_dict)
        
        return pd.DataFrame(features)
    
    def extract_all_features(self, card_names: List[str]) -> pd.DataFrame:
        """Extract all features for given card names"""
        # Extract different feature types
        numeric_features = self.extract_numeric_features(card_names)
        type_features = self.extract_type_features(card_names)
        keyword_features = self.extract_keyword_features(card_names)
        class_features = self.extract_class_features(card_names)
        
        # Combine all features
        all_features = pd.concat([
            numeric_features,
            type_features,
            keyword_features,
            class_features
        ], axis=1)
        
        # Add card names for reference
        all_features.insert(0, 'card_name', card_names)
        
        return all_features
    
    def aggregate_deck_features(self, deck_cards: List[str]) -> Dict[str, float]:
        """Aggregate features for a deck of cards"""
        if not deck_cards:
            return {}
        
        # Extract features for all cards in deck
        deck_features = self.extract_all_features(deck_cards)
        
        # Remove card_name column for aggregation
        feature_cols = [col for col in deck_features.columns if col != 'card_name']
        
        # Calculate aggregate statistics
        aggregated = {
            # Average of numeric features
            **{f'avg_{col}': deck_features[col].mean() for col in feature_cols},
            # Maximum values
            **{f'max_{col}': deck_features[col].max() for col in feature_cols},
            # Count of non-zero features (for binary features)
            **{f'count_{col}': deck_features[col].sum() for col in feature_cols}
        }
        
        return aggregated
    
    def get_feature_summary(self) -> Dict[str, Any]:
        """Get summary statistics of available features"""
        if self.card_data is None:
            self.load_card_data()
        
        return {
            'total_cards': len(self.card_data),
            'numeric_features': ['Pitch', 'Cost', 'Power', 'Defense', 'Health', 'Intelligence', 'Arcane'],
            'card_types': self.card_data['Types'].str.split(', ').explode().value_counts().head(10).to_dict(),
            'card_keywords': self.card_data['Card Keywords'].str.split(', ').explode().value_counts().head(10).to_dict(),
            'feature_coverage': {
                col: self.card_data[col].notna().sum() / len(self.card_data)
                for col in ['Pitch', 'Cost', 'Power', 'Defense', 'Health', 'Intelligence', 'Arcane']
            }
        }


def test_feature_extraction():
    """Test feature extraction functionality"""
    extractor = CardFeatureExtractor()
    
    # Test with some sample card names
    test_cards = [
        'Teklo Leveler',
        'Cognition Nodes',
        'Dash, Inventor Extraordinaire'
    ]
    
    print("\n=== Testing Feature Extraction ===")
    print(f"\nTest cards: {test_cards}")
    
    # Extract numeric features
    print("\n1. Numeric Features:")
    numeric_features = extractor.extract_numeric_features(test_cards)
    print(numeric_features)
    
    # Extract type features
    print("\n2. Type Features:")
    type_features = extractor.extract_type_features(test_cards)
    print(type_features.head())
    
    # Extract keyword features
    print("\n3. Keyword Features:")
    keyword_features = extractor.extract_keyword_features(test_cards)
    print(keyword_features.head())
    
    # Extract all features
    print("\n4. All Features Combined:")
    all_features = extractor.extract_all_features(test_cards)
    print(f"Total features extracted: {len(all_features.columns)}")
    print(all_features.head())
    
    # Get feature summary
    print("\n5. Feature Summary:")
    summary = extractor.get_feature_summary()
    print(f"Total cards in database: {summary['total_cards']}")
    print(f"Numeric features: {summary['numeric_features']}")
    print(f"\nTop card types:")
    for card_type, count in list(summary['card_types'].items())[:5]:
        print(f"  {card_type}: {count}")
    
    print("\n=== Feature Extraction Test Complete ===")


if __name__ == "__main__":
    test_feature_extraction()
