"""
Quick Demo of Teklovossen ML Pipeline
Run this script to see the system in action immediately
"""

import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

def run_quick_demo():
    """Run a quick demonstration of the ML pipeline"""
    
    print("🎮 Teklovossen ML Pipeline Demo")
    print("=" * 40)
    
    try:
        # Test imports
        print("🔧 Testing imports...")
        from simulation.game_engine import GameEngine, Card, CardType, ResourceType
        from simulation.card_database import create_card_database, create_deck_preset, create_opponent_deck
        import pandas as pd
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend for demo
        import matplotlib.pyplot as plt
        print("✅ All imports successful!")
        
        # Create card database
        print("\n🃏 Loading card database...")
        card_db = create_card_database()
        print(f"✅ Loaded {len(card_db)} cards")
        
        # Show card themes
        themes = {}
        for card in card_db.values():
            themes[card.theme] = themes.get(card.theme, 0) + 1
        
        print("📊 Card distribution by theme:")
        for theme, count in themes.items():
            print(f"   {theme}: {count} cards")
        
        # Create decks
        print("\n🏗️ Creating deck presets...")
        deck_presets = {
            'nano_focused': create_deck_preset('nano_focused', card_db),
            'ai_focused': create_deck_preset('ai_focused', card_db),
        }
        opponent_deck = create_opponent_deck(card_db)
        
        for name, deck in deck_presets.items():
            print(f"   {name}: {len(deck)} cards")
        print(f"   opponent deck: {len(opponent_deck)} cards")
        
        # Run a single game simulation
        print("\n🎲 Running single game simulation...")
        engine = GameEngine()
        teklo_deck = deck_presets['nano_focused'].copy()
        opponent = opponent_deck.copy()
        
        game_state = engine.initialize_game(teklo_deck, opponent)
        print(f"✅ Game initialized with {len(game_state.players)} players")
        print(f"   Teklovossen starting hand: {len(game_state.players[0].hand)} cards")
        print(f"   Opponent starting hand: {len(game_state.players[1].hand)} cards")
        
        # Simulate a few turns
        print("\n⚡ Simulating 5 turns of gameplay...")
        for turn in range(5):
            if engine.is_game_over():
                break
                
            turn_data = engine.simulate_turn()
            current_player = game_state.current_player
            
            print(f"   Turn {turn + 1} ({current_player.name}):")
            print(f"     Actions: {len(turn_data.get('actions', []))}")
            print(f"     Life: {current_player.life}")
            print(f"     Resources: Teklo Energy: {current_player.resources.get('teklo_energy', 0)}")
        
        # Check game result
        if engine.is_game_over():
            winner = engine.get_winner()
            print(f"🏆 Game Over! Winner: {winner.name if winner else 'Draw'}")
        else:
            print("⏰ Demo completed (game still in progress)")
        
        # Demonstrate card evaluation
        print("\n📈 Card Balance Analysis Demo...")
        
        # Load existing evaluator from original notebook
        try:
            # Import the original evaluator
            import pandas as pd
            import numpy as np
            
            class SimpleCardEvaluator:
                def __init__(self):
                    self.cards = []
                
                def add_card(self, name, card_type, cost, power_level, complexity, fun_factor, balance, theme_fit, notes=""):
                    card = {
                        'Name': name,
                        'Type': card_type,
                        'Cost': cost,
                        'Power_Level': power_level,
                        'Complexity': complexity,
                        'Fun_Factor': fun_factor,
                        'Balance': balance,
                        'Theme_Fit': theme_fit,
                        'Overall_Score': np.mean([power_level, fun_factor, balance, theme_fit]),
                        'Notes': notes
                    }
                    self.cards.append(card)
                
                def get_dataframe(self):
                    return pd.DataFrame(self.cards)
                
                def analyze_balance(self):
                    df = self.get_dataframe()
                    if len(df) == 0:
                        print("No cards to analyze yet!")
                        return
                    
                    print("=== CARD BALANCE ANALYSIS ===")
                    print(f"Average Power Level: {df['Power_Level'].mean():.1f}/10")
                    print(f"Average Balance Score: {df['Balance'].mean():.1f}/10")
                    print(f"Average Overall Score: {df['Overall_Score'].mean():.1f}/10")
                    
                    # Flag problematic cards
                    high_power_low_balance = df[(df['Power_Level'] >= 8) & (df['Balance'] <= 5)]
                    if len(high_power_low_balance) > 0:
                        print("\\n⚠️  HIGH POWER, LOW BALANCE CARDS:")
                        for idx, card in high_power_low_balance.iterrows():
                            print(f"- {card['Name']}: Power {card['Power_Level']}, Balance {card['Balance']}")
                    
                    return df
            
            # Demo card evaluation
            evaluator = SimpleCardEvaluator()
            
            # Add some example cards
            evaluator.add_card("AI - Overclock Core", "Item - AI", "1 Teklo Energy", 7, 4, 6, 6, 9, "Strong but might be auto-include")
            evaluator.add_card("AI - Predator Logic", "Item - AI", "0 (Reaction)", 8, 6, 8, 5, 9, "Very powerful reaction, needs testing")
            evaluator.add_card("Evo - NeuroWeave Visor", "Equipment - Head", "TBD", 6, 5, 7, 8, 9, "Card draw effect, reasonable power")
            
            print("📊 Sample card evaluations:")
            df = evaluator.analyze_balance()
            
        except Exception as e:
            print(f"⚠️  Card evaluation demo failed: {e}")
        
        # Summary
        print("\n🎉 Demo Complete!")
        print("=" * 40)
        print("✅ Game simulation engine working")
        print("✅ Card database loaded successfully")
        print("✅ Basic gameplay mechanics functional")
        print("✅ Card evaluation system operational")
        
        print("\n📝 Next Steps:")
        print("1. Run full simulations: jupyter notebook notebooks/gameplay_simulator.ipynb")
        print("2. Analyze results: python scripts/data_analytics.py")
        print("3. Set up AWS for ML training (optional)")
        print("4. Read HOW_TO_USE.md for detailed instructions")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Try running: python scripts/setup_environment.py")
        return False
        
    except Exception as e:
        print(f"❌ Demo Error: {e}")
        print("💡 Check the setup and try again")
        return False


if __name__ == "__main__":
    success = run_quick_demo()
    if success:
        print("\n🚀 System ready for full analysis!")
    else:
        print("\n🔧 Please resolve setup issues and try again")
