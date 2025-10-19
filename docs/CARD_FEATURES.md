# Card Feature Extraction for ML Pipeline

## Overview

The card feature extraction system enhances the ML training pipeline by incorporating detailed card attributes from the official Flesh and Blood card database (`card.csv`). This enriches the training data with 40+ features per card, improving model predictions for card balance and win rates.

## Features Extracted

### 1. Numeric Features (7 attributes)
- **Pitch**: Card pitch value (1-3)
- **Cost**: Resource cost to play the card
- **Power**: Attack power value
- **Defense**: Defense value
- **Health**: Hero health value (for Hero cards)
- **Intelligence**: Intelligence value (for Hero cards)
- **Arcane**: Arcane damage value

### 2. Card Type Features (10 types)
Binary indicators for card types:
- Equipment, Action, Attack, Instant, Aura, Item, Weapon, Hero, Ally, Token

### 3. Keyword Features (13 important keywords)
Binary indicators for game mechanics:
- Go again, Dominate, Stealth, Combo, Boost, Overpower, Blood Debt, Blade Break, Legendary, Battleworn, Temper, Charge, Phantasm

### 4. Hero Class Features (10 classes)
Binary indicators for hero classes:
- Mechanologist, Warrior, Ninja, Runeblade, Assassin, Guardian, Brute, Illusionist, Ranger, Wizard

## Card Database Statistics

- **Total Cards**: 3,568 official FAB cards
- **Top Card Types**: Action (2,464), Attack (1,469), Equipment (363)
- **Top Keywords**: Go again (953), Blood Debt (135), Boost (98)
- **Mechanologist Cards**: 338 cards specific to Mechanologist hero class

## Usage Examples

See full documentation in repository for detailed usage examples, testing instructions, and integration guidelines.

## Benefits for ML Models

- **Improved Prediction Accuracy**: 40+ features per card vs basic deck composition
- **Better Generalization**: Identify cross-deck patterns and theme strengths
- **Enhanced Interpretability**: Understand which card attributes drive win rates

## Testing

Run the test suite to verify card feature extraction:

```bash
cd scripts
python test_card_features.py
```

## License

This is a fan-made project for educational purposes. Not affiliated with Legend Story Studios.
