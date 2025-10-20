#!/usr/bin/env python3
"""
Interactive Teklo Card Designer - Create and test cards with SageMaker predictions
"""
import boto3
import json
from typing import Dict, List, Any

class InteractiveCardDesigner:
    def __init__(self):
        self.sagemaker_runtime = boto3.client('sagemaker-runtime', region_name='eu-central-1')
        self.endpoint_name = ""
        
        # Card properties
        self.name = ""
        self.card_type = ""
        self.cost = 0
        self.archetype = ""
        self.description = ""
        self.abilities = []
        
        # Features for ML prediction (17 features total)
        self.features = {
            'AI': 0, 'Nano': 0, 'Quantum': 0, 'Base': 0,
            '0_cost': 0, '1_cost': 0, '2_cost': 0, '3_cost': 0, '4_plus_cost': 0,
            'equipment': 0, 'item': 0, 'action': 0,
            'avg_turns': 0.0, 'avg_evos': 0.0, 'avg_teklo_energy': 0.0,
            'avg_nanite_counters': 0.0, 'avg_quantum_charges': 0.0
        }
    
    def get_user_input(self):
        """Get card details from user input"""
        print("🎯 Welcome to the Interactive Teklo Card Designer!")
        print("Let's create your card step by step...\n")
        
        # Get basic properties
        self.name = input("📝 Card Name: ").strip()
        if not self.name:
            self.name = "Unnamed Card"
        
        # Get card type
        print("\n🎴 Card Type:")
        print("1. Equipment")
        print("2. Action")
        print("3. Item")
        while True:
            choice = input("Choose type (1-3): ").strip()
            if choice == "1":
                self.card_type = "equipment"
                break
            elif choice == "2":
                self.card_type = "action"
                break
            elif choice == "3":
                self.card_type = "item"
                break
            else:
                print("Please enter 1, 2, or 3")
        
        # Get archetype
        print(f"\n⚡ Archetype:")
        print("1. AI")
        print("2. Nano")
        print("3. Quantum")
        print("4. Base")
        while True:
            choice = input("Choose archetype (1-4): ").strip()
            if choice == "1":
                self.archetype = "AI"
                break
            elif choice == "2":
                self.archetype = "Nano"
                break
            elif choice == "3":
                self.archetype = "Quantum"
                break
            elif choice == "4":
                self.archetype = "Base"
                break
            else:
                print("Please enter 1-4")
        
        # Get cost
        while True:
            try:
                cost_input = input(f"\n💰 Resource Cost (0-5+): ").strip()
                self.cost = int(cost_input)
                if self.cost >= 0:
                    break
                else:
                    print("Cost must be 0 or higher")
            except ValueError:
                print("Please enter a valid number")
        
        # Get description
        self.description = input(f"\n📖 Description (optional): ").strip()
        
        # Get abilities
        print(f"\n✨ Abilities (press Enter on empty line to finish):")
        self.abilities = []
        ability_count = 1
        while True:
            ability = input(f"Ability {ability_count}: ").strip()
            if not ability:
                break
            self.abilities.append(ability)
            ability_count += 1
        
        # Update features based on input
        self.update_features()
        
        # Get gameplay impact estimates
        self.get_gameplay_impact()
    
    def update_features(self):
        """Update feature vector based on card properties"""
        # Reset all categorical features
        for key in ['AI', 'Nano', 'Quantum', 'Base']:
            self.features[key] = 0
        for key in ['0_cost', '1_cost', '2_cost', '3_cost', '4_plus_cost']:
            self.features[key] = 0
        for key in ['equipment', 'item', 'action']:
            self.features[key] = 0
        
        # Set archetype
        self.features[self.archetype] = 1
        
        # Set cost
        if self.cost == 0:
            self.features['0_cost'] = 1
        elif self.cost == 1:
            self.features['1_cost'] = 1
        elif self.cost == 2:
            self.features['2_cost'] = 1
        elif self.cost == 3:
            self.features['3_cost'] = 1
        else:
            self.features['4_plus_cost'] = 1
        
        # Set type
        self.features[self.card_type] = 1
    
    def get_gameplay_impact(self):
        """Get estimated gameplay impact from user"""
        print(f"\n🎮 Gameplay Impact Estimates")
        print("Rate the expected impact of this card (-2.0 to +2.0, 0 = no impact):")
        
        impacts = [
            ("avg_turns", "Game Speed", "Negative = slows down games, Positive = speeds up games"),
            ("avg_evos", "Evolution Impact", "How much this affects evolution strategies"),
            ("avg_teklo_energy", "Energy Generation", "How much energy this generates/costs"),
            ("avg_nanite_counters", "Nanite Synergy", "How much this works with nanite mechanics"),
            ("avg_quantum_charges", "Quantum Synergy", "How much this works with quantum mechanics")
        ]
        
        for feature, name, description in impacts:
            while True:
                try:
                    print(f"\n{name}: {description}")
                    value = input(f"Impact (-2.0 to +2.0, default 0): ").strip()
                    if not value:
                        self.features[feature] = 0.0
                        break
                    else:
                        impact = float(value)
                        if -2.0 <= impact <= 2.0:
                            self.features[feature] = impact
                            break
                        else:
                            print("Please enter a value between -2.0 and +2.0")
                except ValueError:
                    print("Please enter a valid number")
    
    def predict_balance(self) -> Dict[str, Any]:
        """Use SageMaker endpoint to predict card balance"""
        try:
            # Create feature vector in correct order (17 features)
            feature_order = [
                'AI', 'Nano', 'Quantum', 'Base',
                '0_cost', '1_cost', '2_cost', '3_cost', '4_plus_cost',
                'equipment', 'item', 'action',
                'avg_turns', 'avg_evos', 'avg_teklo_energy',
                'avg_nanite_counters', 'avg_quantum_charges'
            ]
            
            feature_vector = [self.features[key] for key in feature_order]
            
            print(f"\n🔮 Getting balance prediction from AI model...")
            
            # Prepare input data for SageMaker (CSV format)
            csv_input = ','.join(map(str, feature_vector))
            
            # Call the endpoint
            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType='text/csv',
                Body=csv_input
            )
            
            # Parse response
            result = json.loads(response['Body'].read().decode())
            prediction = result.get('predictions', [0.0])[0] if isinstance(result.get('predictions'), list) else result.get('predictions', 0.0)
            
            # Assess balance based on prediction
            assessment = self.assess_balance(prediction)
            
            return {
                'prediction': prediction,
                'assessment': assessment,
                'feature_vector': feature_vector
            }
            
        except Exception as e:
            print(f"❌ Prediction failed: {e}")
            return {
                'prediction': 5.0,
                'assessment': "🔄 Could not get prediction - using default",
                'error': str(e)
            }
    
    def assess_balance(self, score: float) -> str:
        """Assess card balance based on prediction score"""
        if score > 8:
            return "🔴 OVERPOWERED - Consider reducing power level"
        elif score < 2:
            return "🔵 UNDERPOWERED - Consider increasing power level"
        elif 4 <= score <= 6:
            return "🟢 WELL BALANCED - Good design!"
        else:
            return "🟡 MODERATE - Minor adjustments may be needed"
    
    def display_card_and_results(self, results: Dict[str, Any]):
        """Display the final card design and balance analysis"""
        print(f"\n{'='*80}")
        print(f"🎴 FINAL CARD DESIGN")
        print(f"{'='*80}")
        
        print(f"Name: {self.name}")
        print(f"Type: {self.card_type.title()}")
        print(f"Cost: {self.cost}")
        print(f"Archetype: {self.archetype}")
        
        if self.description:
            print(f"Description: {self.description}")
        
        if self.abilities:
            print(f"\nAbilities:")
            for i, ability in enumerate(self.abilities, 1):
                print(f"  {i}. {ability}")
        
        print(f"\n{'='*80}")
        print(f"🤖 AI BALANCE ANALYSIS")
        print(f"{'='*80}")
        
        print(f"Balance Score: {results['prediction']:.2f}/10")
        print(f"Assessment: {results['assessment']}")
        
        # Show active gameplay impacts
        active_impacts = {k: v for k, v in self.features.items() 
                         if k.startswith('avg_') and v != 0}
        if active_impacts:
            print(f"\n🎮 Gameplay Impacts:")
            for impact, value in active_impacts.items():
                impact_name = impact.replace('avg_', '').replace('_', ' ').title()
                print(f"  {impact_name}: {value:+.1f}")
        
        # Suggestions based on score
        print(f"\n💡 Suggestions:")
        score = results['prediction']
        if score > 8:
            print("  • Consider increasing the cost")
            print("  • Consider adding restrictions to abilities")
            print("  • Consider reducing numerical values")
        elif score < 2:
            print("  • Consider reducing the cost")
            print("  • Consider adding more powerful abilities")
            print("  • Consider increasing numerical benefits")
        else:
            print("  • Card appears balanced for playtesting!")
            print("  • Test in actual games to validate predictions")
    
    def save_card(self):
        """Save the card design to a file"""
        from datetime import datetime
        
        card_data = {
            'name': self.name,
            'type': self.card_type,
            'cost': self.cost,
            'archetype': self.archetype,
            'description': self.description,
            'abilities': self.abilities,
            'features': self.features,
            'created_at': datetime.now().isoformat()
        }
        
        safe_name = self.name.lower().replace(' ', '_').replace('/', '_')
        filename = f"{safe_name}_card.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(card_data, f, indent=2)
            print(f"\n💾 Card saved to: {filename}")
        except Exception as e:
            print(f"❌ Could not save card: {e}")

def main():
    """Main interactive loop"""
    designer = InteractiveCardDesigner()
    
    while True:
        # Get card details from user
        designer.get_user_input()
        
        # Get balance prediction
        results = designer.predict_balance()
        
        # Show results
        designer.display_card_and_results(results)
        
        # Ask if user wants to save
        save = input(f"\n💾 Save this card design? (y/n): ").strip().lower()
        if save in ['y', 'yes']:
            designer.save_card()
        
        # Ask if user wants to create another card
        another = input(f"\n🎯 Create another card? (y/n): ").strip().lower()
        if another not in ['y', 'yes']:
            break
        
        print(f"\n{'='*80}\n")
    
    print(f"\n🎉 Thanks for using the Teklo Card Designer!")
    print(f"Remember to playtest your cards to validate the AI predictions!")

if __name__ == "__main__":
    main()