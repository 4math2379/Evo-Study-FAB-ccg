"""
Hybrid Card Database: Real FAB Base Cards + Custom Teklovossen Cards
Combines the official FAB cards from CSV with your fan-made Teklovossen designs
"""

import pandas as pd
from typing import Dict, List
from .game_engine import Card, CardType, EquipmentSlot, ResourceType


def load_base_fab_cards(csv_path: str = "card.csv") -> Dict[str, Card]:
    """Load relevant base cards from FAB CSV (Teklovossen, base equipment, etc.)"""
    
    base_cards = {}
    
    try:
        df = pd.read_csv(csv_path, sep='\t', encoding='utf-8')
        print(f"📄 Loaded {len(df)} cards from FAB database")
        
        # Filter for relevant base cards
        relevant_cards = []
        
        # 1. Find existing Teklovossen cards
        teklo_cards = df[df['Name'].str.contains('Teklo', na=False, case=False)]
        if len(teklo_cards) > 0:
            relevant_cards.extend(teklo_cards.to_dict('records'))
            print(f"🔧 Found {len(teklo_cards)} existing Teklovossen cards")
        
        # 2. Find Mechanologist cards for base deck building
        mech_cards = df[df['Types'].str.contains('Mechanologist', na=False)]
        if len(mech_cards) > 0:
            # Take a sample of mechanologist cards, not all
            sample_mech = mech_cards.head(20)  # Just get some examples
            relevant_cards.extend(sample_mech.to_dict('records'))
            print(f"⚙️ Found {len(sample_mech)} Mechanologist cards (sampled)")

        

        # Evo cards exclude non mechanologist evos
        evo_cards = df[df['Name'].str.contains('Evo', na=False, case=False)]
        if len(evo_cards) > 0:
            relevant_cards.extend(evo_cards.to_dict('records'))
            print(f"🔄 Found {len(evo_cards)} Evo cards")
            # Exclude non-mechanologist Evo cards
            relevant_cards = [card for card in relevant_cards if 'Mechanologist' in card.get('Types', '')]

        items_cards = df[df['Types'].str.contains('Item', na=False)]
        if len(items_cards) > 0:
            relevant_cards.extend(items_cards.to_dict('records'))
            print(f"🎒 Found {len(items_cards)} Item cards")
            # Exclude non-mechanologist Item cards
            relevant_cards = [card for card in relevant_cards if 'Mechanologist' in card.get('Types', '')]
        
        instant_cards = df[df['Types'].str.contains('Instant', na=False)]
        if len(instant_cards) > 0:
            relevant_cards.extend(instant_cards.to_dict('records'))
            print(f"⚡ Found {len(instant_cards)} Instant cards")
            # Exclude non-mechanologist Instant cards
            relevant_cards = [card for card in relevant_cards if 'Mechanologist' in card.get('Types', '')]


        # 3. Find basic equipment that could be base cards
        basic_equipment = df[
            (df['Types'].str.contains('Equipment', na=False)) &
            (df['Types'].str.contains('Generic', na=False) | 
             df['Name'].str.contains('Basic|Simple|Standard|Evo', na=False, case=False))
        ]
        if len(basic_equipment) > 0:
            relevant_cards.extend(basic_equipment.head(10).to_dict('records'))
            print(f"🛡️ Found {len(basic_equipment.head(10))} basic equipment cards")

        # boost cards
        boost_cards = df[df['Card Keywords'].str.contains('Boost', na=False)]

        if len(boost_cards) > 0:
            relevant_cards.extend(boost_cards.to_dict('records'))
            print(f"🚀 Found {len(boost_cards)} Boost cards")

        # scrap cards
        scrap_cards = df[df['Card Keywords'].str.contains('Scrap', na=False)]

        if len(scrap_cards) > 0:
            relevant_cards.extend(scrap_cards.to_dict('records'))
            print(f"🗑️ Found {len(scrap_cards)} Scrap cards")

        # crank cards
        crank_cards = df[df['Card Keywords'].str.contains('Crank', na=False)]

        if len(crank_cards) > 0:
            relevant_cards.extend(crank_cards.to_dict('records'))
            print(f"🔧 Found {len(crank_cards)} Crank cards")

        # Convert to our Card objects
        print("\n🔄 Converting base cards...")
        for card_data in relevant_cards:
            card = convert_fab_card_to_sim_card(card_data)
            if card:
                base_cards[card.name] = card
        
        print(f"✅ Successfully loaded {len(base_cards)} base FAB cards")
        
    except Exception as e:
        print(f"⚠️ Error loading base cards: {e}")
        print("📦 Creating minimal base cards...")
        base_cards = create_minimal_base_cards()
    
    return base_cards


def convert_fab_card_to_sim_card(card_data: dict) -> Card:
    """Convert FAB card data to simulation Card"""
    try:
        name = str(card_data.get('Name', 'Unknown'))
        types = str(card_data.get('Types', ''))
        
        # Determine card type
        if 'Equipment' in types:
            card_type = CardType.EQUIPMENT
        elif 'Attack' in types:
            card_type = CardType.ATTACK
        elif 'Instant' in types:
            card_type = CardType.REACTION
        elif 'Action' in types:
            card_type = CardType.ACTION
        else:
            card_type = CardType.ACTION  # Default
        
        # Parse basic stats
        cost = {}
        cost_val = card_data.get('Cost', '')
        if cost_val and str(cost_val).isdigit():
            cost[ResourceType.TEKLO_ENERGY] = int(cost_val)
        
        pitch = int(card_data.get('Pitch', 0)) if pd.notna(card_data.get('Pitch')) else 0
        power = int(card_data.get('Power', 0)) if pd.notna(card_data.get('Power')) else 0
        defense = int(card_data.get('Defense', 0)) if pd.notna(card_data.get('Defense')) else 0
        
        # Determine equipment slot
        equipment_slot = None
        if 'Equipment' in types:
            if 'Head' in types or 'Helm' in types:
                equipment_slot = EquipmentSlot.HEAD
            elif 'Chest' in types:
                equipment_slot = EquipmentSlot.CHEST
            elif 'Arms' in types:
                equipment_slot = EquipmentSlot.ARMS
            elif 'Legs' in types:
                equipment_slot = EquipmentSlot.LEGS
            elif 'Weapon' in types:
                equipment_slot = EquipmentSlot.WEAPON
        
        # Determine theme - prioritize custom themes from Types field
        if 'AI' in types:
            theme = 'AI'
        elif 'Nano' in types:
            theme = 'Nano'
        elif 'Quantum' in types:
            theme = 'Quantum'
        elif 'Bio' in types:
            theme = 'Bio'
        elif 'Mechanologist' in types:
            theme = 'Mechanologist'
        elif 'Teklo' in name:
            theme = 'Teklovossen'
        else:
            theme = 'Generic'
        
        # Parse keywords
        keywords = []
        card_keywords = str(card_data.get('Card Keywords', ''))
        if 'Go again' in card_keywords:
            keywords.append('go_again')
        if 'Battleworn' in card_keywords:
            keywords.append('battleworn')
        if 'Legendary' in card_keywords:
            keywords.append('legendary')
        if 'Scrap' in card_keywords:
            keywords.append('scrap')
        if 'Boost' in card_keywords:
            keywords.append('boost')
        
        # Basic abilities based on functional text
        abilities = []
        functional_text = str(card_data.get('Functional Text', ''))
        if 'draw' in functional_text.lower():
            abilities.append('draw_card')
        if 'gain' in functional_text.lower() and 'resource' in functional_text.lower():
            abilities.append('gain_resource')
        
        return Card(
            name=name,
            card_type=card_type,
            cost=cost,
            pitch_value=pitch,
            attack_value=power,
            defense_value=defense,
            equipment_slot=equipment_slot,
            keywords=keywords,
            abilities=abilities,
            theme=theme,
            rarity='common'
        )
        
    except Exception as e:
        print(f"⚠️ Error converting {card_data.get('Name', 'Unknown')}: {e}")
        return None


def create_minimal_base_cards() -> Dict[str, Card]:
    """Create minimal base cards if CSV loading fails"""
    return {
        "Basic Equipment": Card(
            "Basic Equipment", CardType.EQUIPMENT, 
            {ResourceType.TEKLO_ENERGY: 1}, defense_value=2, 
            equipment_slot=EquipmentSlot.CHEST, theme="Generic"
        ),
        "Basic Weapon": Card(
            "Basic Weapon", CardType.EQUIPMENT,
            {ResourceType.TEKLO_ENERGY: 2}, attack_value=3,
            equipment_slot=EquipmentSlot.WEAPON, theme="Generic"
        )
    }


def create_custom_teklovossen_cards(custom_csv_path: str = "custom_cards.csv") -> Dict[str, Card]:
    """Load your custom fan-made Teklovossen cards from CSV"""
    
    cards = {}
    
    try:
        df = pd.read_csv(custom_csv_path, sep='\t', encoding='utf-8')
        print(f"📄 Loaded {len(df)} custom cards from {custom_csv_path}")
        
        for _, card_data in df.iterrows():
            card = convert_fab_card_to_sim_card(card_data.to_dict())
            if card:
                cards[card.name] = card
        
        print(f"✅ Successfully converted {len(cards)} custom Teklovossen cards")
        
    except Exception as e:
        print(f"⚠️ Error loading custom cards CSV: {e}")
        print("📦 Falling back to hardcoded custom cards...")
        cards = create_hardcoded_custom_cards()
    
    return cards


def create_hardcoded_custom_cards() -> Dict[str, Card]:
    """Fallback: Create hardcoded custom cards if CSV loading fails"""
    
    cards = {}
    
    # AI Items (your custom designs)
    cards["AI - Overclock Core"] = Card(
        name="AI - Overclock Core",
        card_type=CardType.ITEM,
        cost={ResourceType.TEKLO_ENERGY: 1},
        abilities=["gain_attack_boost", "overpower_synergy"],
        theme="AI",
        rarity="common",
        keywords=["ai_item"]
    )
    
    cards["AI - Predator Logic"] = Card(
        name="AI - Predator Logic",
        card_type=CardType.ITEM,
        cost={ResourceType.TEKLO_ENERGY: 2},
        abilities=["dominate_and_go_again"],
        theme="AI",
        rarity="rare",
        keywords=["ai_item", "reaction", "modular"]
    )
    
    cards["AI - Singularity Cannon"] = Card(
        name="AI - Singularity Cannon",
        card_type=CardType.ITEM,
        cost={ResourceType.TEKLO_ENERGY: 2},
        attack_value=6,
        abilities=["scaling_attack", "banish_for_power"],
        theme="AI",
        rarity="legendary",
        keywords=["ai_item", "attack_construct"]
    )
    
    cards["AI - Nemesis Driver"] = Card(
        name="AI - Nemesis Driver",
        card_type=CardType.ITEM,
        cost={ResourceType.TEKLO_ENERGY: 1},
        abilities=["area_damage", "entropy_synergy"],
        theme="AI",
        rarity="rare",
        keywords=["ai_item", "aggressor_unit"]
    )
    
    # Nano Equipment - Core Evos (your custom designs)
    cards["Evo - Nanite Core Reactor"] = Card(
        name="Evo - Nanite Core Reactor",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 3},
        equipment_slot=EquipmentSlot.CHEST,
        defense_value=3,
        abilities=["gain_nanite_counter", "teklo_energy_conversion"],
        theme="Nano",
        rarity="rare",
        keywords=["battleworn", "evo_nano"],
        is_evo=True
    )
    
    cards["Evo - NeuroWeave Visor"] = Card(
        name="Evo - NeuroWeave Visor",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 2},
        equipment_slot=EquipmentSlot.HEAD,
        defense_value=3,
        abilities=["draw_card", "nanite_card_draw"],
        theme="Nano",
        rarity="common",
        keywords=["battleworn", "evo_nano"],
        is_evo=True
    )
    
    cards["Evo - Phage Arms"] = Card(
        name="Evo - Phage Arms",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 2},
        equipment_slot=EquipmentSlot.ARMS,
        defense_value=3,
        abilities=["attack_boost", "nanite_defense"],
        theme="Nano",
        rarity="common",
        keywords=["battleworn", "evo_nano", "go_again"],
        is_evo=True
    )
    
    cards["Evo - Swarm-Forged Tower"] = Card(
        name="Evo - Swarm-Forged Tower",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 2},
        equipment_slot=EquipmentSlot.LEGS,
        defense_value=3,
        abilities=["gain_nanite_counter", "go_again_synergy"],
        theme="Nano",
        rarity="common",
        keywords=["battleworn", "evo_nano"],
        is_evo=True
    )
    
    # Nano Items (your custom designs)
    cards["Item - Nanite Forge"] = Card(
        name="Item - Nanite Forge",
        card_type=CardType.ITEM,
        cost={ResourceType.TEKLO_ENERGY: 2},
        abilities=["gain_nanite_counter", "evo_synergy"],
        theme="Nano",
        rarity="common",
        keywords=["nano_item"]
    )
    
    cards["Item - Cloakfield Generator"] = Card(
        name="Item - Cloakfield Generator",
        card_type=CardType.ITEM,
        cost={ResourceType.TEKLO_ENERGY: 1},
        abilities=["adaptive_defense", "arcane_barrier"],
        theme="Nano",
        rarity="rare",
        keywords=["nano_item", "instant"]
    )
    
    # Quantum Equipment (your custom designs)
    cards["Evo - Quantum Processor"] = Card(
        name="Evo - Quantum Processor",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 4},
        equipment_slot=EquipmentSlot.CHEST,
        defense_value=3,
        abilities=["gain_quantum_charge", "quantum_conversion", "damage_ability"],
        theme="Quantum",
        rarity="legendary",
        keywords=["battleworn", "evo_quantum", "teklovossen_specialization"],
        is_evo=True,
        base_card="Evo Steel Soul Processor",
        pitch_value=1
    )
    
    cards["Evo - Quantum Nexus"] = Card(
        name="Evo - Quantum Nexus",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 4},
        equipment_slot=EquipmentSlot.HEAD,
        defense_value=3,
        abilities=["collapse_draw", "quantum_synergy"],
        theme="Quantum",
        rarity="rare",
        keywords=["battleworn", "evo_quantum"],
        is_evo=True,
        pitch_value=1
    )
    
    # Weapons (your custom designs)
    cards["Nanite Devastator"] = Card(
        name="Nanite Devastator",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 4},
        equipment_slot=EquipmentSlot.WEAPON,
        attack_value=7,
        abilities=["unredirectable", "nanite_scaling", "equipment_destruction"],
        theme="Nano",
        rarity="legendary",
        keywords=["two_handed", "gun", "nano"],
        is_evo=True,
        base_card="Teklo Leveler",
        pitch_value=1
    )
    
    # Action Cards (your custom designs)
    cards["Self-Assembly Protocol"] = Card(
        name="Self-Assembly Protocol",
        card_type=CardType.ACTION,
        cost={ResourceType.TEKLO_ENERGY: 1},
        abilities=["choose_two", "equip_evo", "nanite_counter", "cost_reduction", "graveyard_recursion"],
        theme="Nano",
        rarity="common",
        keywords=["nano", "instant"]
    )
    
    cards["Teklo Genesis Matrix"] = Card(
        name="Teklo Genesis Matrix",
        card_type=CardType.ACTION,
        cost={ResourceType.TEKLO_ENERGY: 2},
        pitch_value=2,
        abilities=["action_point", "equip_base", "nanite_generation", "search_and_equip"],
        theme="Nano",
        rarity="legendary",
        keywords=["nano"]
    )
    
    return cards


def create_base_equipment_cards(base_fab_cards: Dict[str, Card]) -> Dict[str, Card]:
    """Create base equipment cards (either from FAB CSV or fallback)"""
    
    base_equipment = {}
    
    # Try to use base cards from CSV first
    for name, card in base_fab_cards.items():
        if card.card_type == CardType.EQUIPMENT and not card.is_evo:
            base_equipment[name] = card
    
    # If we don't have enough base equipment, create some
    if len([c for c in base_equipment.values() if c.equipment_slot == EquipmentSlot.HEAD]) == 0:
        base_equipment["Base Head"] = Card(
            name="Base Head",
            card_type=CardType.EQUIPMENT,
            cost={ResourceType.TEKLO_ENERGY: 1},
            equipment_slot=EquipmentSlot.HEAD,
            defense_value=1,
            theme="Base",
            rarity="common"
        )
    
    if len([c for c in base_equipment.values() if c.equipment_slot == EquipmentSlot.CHEST]) == 0:
        base_equipment["Base Chest"] = Card(
            name="Base Chest",
            card_type=CardType.EQUIPMENT,
            cost={ResourceType.TEKLO_ENERGY: 1},
            equipment_slot=EquipmentSlot.CHEST,
            defense_value=1,
            theme="Base",
            rarity="common"
        )
    
    if len([c for c in base_equipment.values() if c.equipment_slot == EquipmentSlot.ARMS]) == 0:
        base_equipment["Base Arms"] = Card(
            name="Base Arms",
            card_type=CardType.EQUIPMENT,
            cost={ResourceType.TEKLO_ENERGY: 1},
            equipment_slot=EquipmentSlot.ARMS,
            defense_value=1,
            theme="Base",
            rarity="common"
        )
    
    if len([c for c in base_equipment.values() if c.equipment_slot == EquipmentSlot.LEGS]) == 0:
        base_equipment["Base Legs"] = Card(
            name="Base Legs",
            card_type=CardType.EQUIPMENT,
            cost={ResourceType.TEKLO_ENERGY: 1},
            equipment_slot=EquipmentSlot.LEGS,
            defense_value=1,
            theme="Base",
            rarity="common"
        )
    
    if len([c for c in base_equipment.values() if c.equipment_slot == EquipmentSlot.WEAPON]) == 0:
        base_equipment["Teklo Leveler"] = Card(
            name="Teklo Leveler",
            card_type=CardType.EQUIPMENT,
            cost={ResourceType.TEKLO_ENERGY: 2},
            equipment_slot=EquipmentSlot.WEAPON,
            attack_value=4,
            defense_value=2,
            theme="Base",
            rarity="common",
            keywords=["gun"]
        )
    
    return base_equipment


def create_hybrid_card_database(csv_path: str = "card.csv", custom_csv_path: str = "custom_cards.csv") -> Dict[str, Card]:
    """Create the complete hybrid database: Base FAB + Custom Teklovossen cards"""
    
    print("🏗️ Creating Hybrid Card Database")
    print("=" * 50)
    
    # 1. Load base FAB cards from CSV
    print("📖 Loading base FAB cards...")
    base_fab_cards = load_base_fab_cards(csv_path)
    
    # 2. Create your custom Teklovossen cards from CSV
    print("\n🎨 Loading custom Teklovossen cards from CSV...")
    custom_cards = create_custom_teklovossen_cards(custom_csv_path)
    print(f"✅ Created {len(custom_cards)} custom cards")
    
    # 3. Create base equipment
    print("\n⚙️ Setting up base equipment...")
    base_equipment = create_base_equipment_cards(base_fab_cards)
    print(f"✅ Created {len(base_equipment)} base equipment cards")
    
    # 4. Combine everything
    all_cards = {}
    all_cards.update(base_fab_cards)    # Base FAB cards
    all_cards.update(custom_cards)      # Your custom cards
    all_cards.update(base_equipment)    # Base equipment
    
    # 5. Show summary
    print(f"\n📊 Final Database Summary:")
    print(f"  Base FAB cards: {len(base_fab_cards)}")
    print(f"  Custom Teklovossen cards: {len(custom_cards)}")
    print(f"  Base equipment: {len(base_equipment)}")
    print(f"  Total cards: {len(all_cards)}")
    
    # Show theme distribution
    themes = {}
    for card in all_cards.values():
        themes[card.theme] = themes.get(card.theme, 0) + 1
    
    print(f"\n🎭 Theme Distribution:")
    for theme, count in sorted(themes.items()):
        print(f"  {theme}: {count} cards")
    
    print(f"\n✅ Hybrid database ready!")
    return all_cards


def create_hybrid_deck_presets(card_db: Dict[str, Card]) -> Dict[str, List[Card]]:
    """Create deck presets focusing on your custom cards with base support"""
    
    # Categorize cards
    custom_ai = [c for c in card_db.values() if c.theme == "AI"]
    custom_nano = [c for c in card_db.values() if c.theme == "Nano"]
    custom_quantum = [c for c in card_db.values() if c.theme == "Quantum"]
    base_cards = [c for c in card_db.values() if c.theme in ["Base", "Generic", "Mechanologist", "Teklovossen"]]
    
    presets = {}
    
    # AI-Focused Deck (your custom AI cards + base support)
    ai_deck = []
    ai_deck.extend(custom_ai)  # All your AI cards
    
    # Add base equipment
    for slot in EquipmentSlot:
        slot_cards = [c for c in base_cards if c.equipment_slot == slot and c.card_type == CardType.EQUIPMENT]
        if slot_cards:
            ai_deck.append(slot_cards[0])  # Add one base equipment per slot
    
    # Fill with base actions/attacks
    base_actions = [c for c in base_cards if c.card_type in [CardType.ACTION, CardType.ATTACK]]
    ai_deck.extend(base_actions[:6])  # Add some base cards for deck balance
    
    presets['ai_focused'] = ai_deck[:20]
    
    # Nano-Focused Deck (your custom Nano cards + base support)  
    nano_deck = []
    nano_deck.extend(custom_nano)  # All your Nano cards
    
    # Add base equipment
    for slot in EquipmentSlot:
        slot_cards = [c for c in base_cards if c.equipment_slot == slot and c.card_type == CardType.EQUIPMENT]
        if slot_cards:
            nano_deck.append(slot_cards[0])
    
    # Fill with base support
    nano_deck.extend(base_actions[:5])
    
    presets['nano_focused'] = nano_deck[:20]
    
    # Quantum-Focused Deck
    quantum_deck = []
    quantum_deck.extend(custom_quantum)
    
    # Add base support
    for slot in EquipmentSlot:
        slot_cards = [c for c in base_cards if c.equipment_slot == slot and c.card_type == CardType.EQUIPMENT]
        if slot_cards:
            quantum_deck.append(slot_cards[0])
    
    quantum_deck.extend(base_actions[:6])
    
    presets['quantum_focused'] = quantum_deck[:20]
    
    # Balanced Mix (mix of your custom cards)
    balanced_deck = []
    balanced_deck.extend(custom_ai[:2])      # 2 AI cards
    balanced_deck.extend(custom_nano[:3])    # 3 Nano cards  
    balanced_deck.extend(custom_quantum[:2]) # 2 Quantum cards
    
    # Fill with base cards
    for slot in EquipmentSlot:
        slot_cards = [c for c in base_cards if c.equipment_slot == slot and c.card_type == CardType.EQUIPMENT]
        if slot_cards:
            balanced_deck.append(slot_cards[0])
    
    balanced_deck.extend(base_actions[:8])
    
    presets['balanced_mix'] = balanced_deck[:20]
    
    print(f"\n🃏 Created hybrid deck presets:")
    for name, deck in presets.items():
        custom_count = len([c for c in deck if c.theme in ["AI", "Nano", "Quantum"]])
        base_count = len(deck) - custom_count
        print(f"  {name}: {len(deck)} total ({custom_count} custom + {base_count} base)")
    
    return presets


# Compatibility functions for the existing simulation
def create_card_database(csv_path: str = "card.csv", custom_csv_path: str = "custom_cards.csv") -> Dict[str, Card]:
    """Main function to create the hybrid database (replaces original)"""
    return create_hybrid_card_database(csv_path, custom_csv_path)


def create_deck_preset(preset_name: str, card_db: Dict[str, Card]) -> List[Card]:
    """Create a specific deck preset (replaces original)"""
    presets = create_hybrid_deck_presets(card_db)
    return presets.get(preset_name, list(card_db.values())[:20])


def create_opponent_deck(card_db: Dict[str, Card]) -> List[Card]:
    """Create opponent deck using base FAB cards"""
    base_cards = [c for c in card_db.values() if c.theme in ["Generic", "Mechanologist", "Base"]]
    
    # Basic opponent deck
    opponent_deck = []
    
    # Add equipment
    for slot in EquipmentSlot:
        slot_cards = [c for c in base_cards if c.equipment_slot == slot and c.card_type == CardType.EQUIPMENT]
        if slot_cards:
            opponent_deck.append(slot_cards[0])
    
    # Add actions/attacks
    actions = [c for c in base_cards if c.card_type in [CardType.ACTION, CardType.ATTACK]]
    opponent_deck.extend(actions[:10])
    
    # Fill with basic cards if needed
    while len(opponent_deck) < 15:
        opponent_deck.append(Card(
            name=f"Basic Card {len(opponent_deck)}",
            card_type=CardType.ACTION,
            cost={ResourceType.TEKLO_ENERGY: 1},
            attack_value=2,
            theme="Generic"
        ))
    
    return opponent_deck[:20]


# Your balance scores (unchanged)
CARD_BALANCE_SCORES = {
    "AI - Overclock Core": {
        "power_level": 7, "complexity": 4, "fun_factor": 6, "balance": 6, "theme_fit": 9
    },
    "AI - Predator Logic": {
        "power_level": 8, "complexity": 6, "fun_factor": 8, "balance": 5, "theme_fit": 9
    },
    "AI - Singularity Cannon": {
        "power_level": 9, "complexity": 7, "fun_factor": 9, "balance": 4, "theme_fit": 10
    },
    "Evo - Nanite Core Reactor": {
        "power_level": 8, "complexity": 6, "fun_factor": 8, "balance": 5, "theme_fit": 10
    },
    "Evo - NeuroWeave Visor": {
        "power_level": 6, "complexity": 5, "fun_factor": 7, "balance": 8, "theme_fit": 9
    },
    "Self-Assembly Protocol": {
        "power_level": 6, "complexity": 4, "fun_factor": 7, "balance": 7, "theme_fit": 9
    }
}
