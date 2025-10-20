#!/usr/bin/env python3
"""
Simple Card Proposal Tool - Uses existing SageMaker endpoint
"""
import boto3
import numpy as np
import json
from typing import Dict, List, Any

class SimpleCardProposal:
    def __init__(self):
        self.sagemaker_runtime = boto3.client('sagemaker-runtime', region_name='eu-central-1')
        self.endpoint_name = ""
        
        # Card properties
        self.name = ""
        self.card_type = ""  # 'equipment', 'action', 'item'
        self.cost = 0
        self.archetype = ""  # 'AI', 'Nano', 'Quantum', 'Base'
        self.description = ""
        self.abilities = []
        
        # Features for ML prediction (matching your model's expected input)
        self.features = {
            'AI': 0, 'Nano': 0, 'Quantum': 0, 'Base': 0,
            '0_cost': 0, '1_cost': 0, '2_cost': 0, '3_cost': 0, '4_plus_cost': 0,
            'equipment': 0, 'item': 0, 'action': 0,
            'avg_turns': 0.0, 'avg_evos': 0.0, 'avg_teklo_energy': 0.0,
            'avg_nanite_counters': 0.0, 'avg_quantum_charges': 0.0,
            'consistency_score': 0.0, 'avg_expert_balance_score': 5.0
        }
    
    def set_card_properties(self, name: str, card_type: str, cost: int, archetype: str, description: str = ""):
        """Set basic card properties and update features automatically"""
        self.name = name
        self.description = description
        
        # Reset all categorical features
        for key in ['AI', 'Nano', 'Quantum', 'Base']:
            self.features[key] = 0
        for key in ['0_cost', '1_cost', '2_cost', '3_cost', '4_plus_cost']:
            self.features[key] = 0
        for key in ['equipment', 'item', 'action']:
            self.features[key] = 0
        
        # Set archetype
        if archetype in ['AI', 'Nano', 'Quantum', 'Base']:
            self.archetype = archetype
            self.features[archetype] = 1
        
        # Set cost
        self.cost = cost
        if cost == 0:
            self.features['0_cost'] = 1
        elif cost == 1:
            self.features['1_cost'] = 1
        elif cost == 2:
            self.features['2_cost'] = 1
        elif cost == 3:
            self.features['3_cost'] = 1
        else:
            self.features['4_plus_cost'] = 1
        
        # Set type
        if card_type.lower() in ['equipment', 'item', 'action']:
            self.card_type = card_type.lower()
            self.features[card_type.lower()] = 1
    
    def set_gameplay_impact(self, turns: float = 0.0, evos: float = 0.0, 
                           energy: float = 0.0, nanites: float = 0.0, 
                           quantum: float = 0.0, consistency: float = 0.0):
        """Set estimated gameplay impact values"""
        self.features.update({
            'avg_turns': turns,
            'avg_evos': evos,
            'avg_teklo_energy': energy,
            'avg_nanite_counters': nanites,
            'avg_quantum_charges': quantum,
            'consistency_score': consistency
        })
    
    def predict_balance(self) -> Dict[str, Any]:
        """Use SageMaker endpoint to predict card balance"""
        try:
            # Convert features to the format expected by your model
            # The model expects features in a specific order
            feature_order = [
                'AI', 'Nano', 'Quantum', 'Base',
                '0_cost', '1_cost', '2_cost', '3_cost', '4_plus_cost',
                'equipment', 'item', 'action',
                'avg_turns', 'avg_evos', 'avg_teklo_energy',
                'avg_nanite_counters', 'avg_quantum_charges'
            ]
            
            # Create feature vector in correct order
            feature_vector = [self.features[key] for key in feature_order]
            
            print(f"🔮 Predicting balance for '{self.name}'...")
            print(f"📊 Using endpoint: {self.endpoint_name}")
            print(f"🔧 Feature vector: {feature_vector}")
            
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
                'endpoint_used': self.endpoint_name,
                'feature_vector': feature_vector
            }
            
        except Exception as e:
            print(f"❌ Prediction failed: {e}")
            return {
                'prediction': 5.0,  # Default neutral score
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
    
    def display_card(self):
        """Display card information"""
        print(f"\n{'='*60}")
        print(f"CARD: {self.name}")
        print(f"{'='*60}")
        print(f"Type: {self.card_type.title()}")
        print(f"Cost: {self.cost}")
        print(f"Archetype: {self.archetype}")
        if self.description:
            print(f"Description: {self.description}")
        if self.abilities:
            print("Abilities:")
            for ability in self.abilities:
                print(f"  • {ability}")
        print(f"{'='*60}")

def main():
    """Example usage"""
    print("🎯 Teklo Card Proposal Tool")
    print("Uses your existing SageMaker endpoint for balance prediction\n")
    
    # Create a new card proposal
    card = SimpleCardProposal()
    
    # Example 1: Quantum Equipment Card
    card.set_card_properties(
        name="Quantum Resonator",
        card_type="equipment",
        cost=2,
        archetype="Quantum",
        description="An advanced quantum device that amplifies resonance patterns"
    )
    
    card.abilities = [
        "When played: Gain 1 Quantum Charge",
        "Activated: Pay 2 Quantum Charges to draw a card"
    ]
    
    # Set estimated gameplay impact
    card.set_gameplay_impact(
        turns=0.5,      # Slightly speeds up games
        evos=0.2,       # Minor evolution impact
        energy=0.1,     # Small energy impact
        nanites=0.0,    # No nanite impact
        quantum=1.2,    # Strong quantum synergy
        consistency=0.3 # Improves deck consistency
    )
    
    # Display the card
    card.display_card()
    
    # Get balance prediction
    result = card.predict_balance()
    
    # Show results
    print(f"\n📊 BALANCE ANALYSIS")
    print(f"Predicted Balance Score: {result['prediction']:.2f}/10")
    print(f"Assessment: {result['assessment']}")
    if 'endpoint_used' in result:
        print(f"Endpoint: {result['endpoint_used']}")
    
    print(f"\n🔧 Active Features:")
    active_features = {k: v for k, v in card.features.items() if v > 0}
    for feature, value in active_features.items():
        print(f"  {feature}: {value}")
    
    # Example 2: AI Action Card
    print(f"\n{'='*60}")
    print("SECOND EXAMPLE - AI ACTION CARD")
    
    card2 = SimpleCardProposal()
    card2.set_card_properties(
        name="Neural Network Override",
        card_type="action",
        cost=1,
        archetype="AI",
        description="Hack into opponent's systems"
    )
    
    card2.abilities = [
        "Target opponent discards a card",
        "If they discard an equipment, gain 1 Teklo Energy"
    ]
    
    card2.set_gameplay_impact(
        turns=-0.3,     # Disrupts opponent
        evos=0.0,
        energy=0.5,     # Potential energy gain
        nanites=0.0,
        quantum=0.0,
        consistency=-0.2  # Disrupts opponent consistency
    )
    
    card2.display_card()
    result2 = card2.predict_balance()
    
    print(f"\n📊 BALANCE ANALYSIS")
    print(f"Predicted Balance Score: {result2['prediction']:.2f}/10")
    print(f"Assessment: {result2['assessment']}")

if __name__ == "__main__":
    main()