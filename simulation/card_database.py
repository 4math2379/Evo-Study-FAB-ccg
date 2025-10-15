"""
Teklovossen Card Database
Defines all the cards from the teklostudy.md documentation for simulation
"""

from .game_engine import Card, CardType, EquipmentSlot, ResourceType


def create_card_database():
    """Create and return a database of all Teklovossen cards"""
    
    cards = {}
    
    # AI Items
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
    
    # Nano Equipment - Core Evos
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
    
    # Nano Items
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
    
    cards["Item - Teklo Fabricator"] = Card(
        name="Item - Teklo Fabricator",
        card_type=CardType.ITEM,
        cost={ResourceType.TEKLO_ENERGY: 0},
        abilities=["repair_equipment", "nanite_cost"],
        theme="Nano",
        rarity="common",
        keywords=["nano_item", "end_phase"]
    )
    
    # Quantum Equipment
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
    
    cards["Evo - Quantum Controller"] = Card(
        name="Evo - Quantum Controller",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 4},
        equipment_slot=EquipmentSlot.ARMS,
        defense_value=3,
        abilities=["attack_boost", "teklo_energy_on_hit"],
        theme="Quantum",
        rarity="legendary",
        keywords=["battleworn", "evo_quantum", "teklovossen_specialization"],
        is_evo=True,
        base_card="Evo Steel Soul Controller",
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
    
    cards["Evo - Quantum Tower"] = Card(
        name="Evo - Quantum Tower",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 4},
        equipment_slot=EquipmentSlot.LEGS,
        defense_value=3,
        abilities=["transform_bonus", "draw_card"],
        theme="Quantum",
        rarity="legendary",
        keywords=["battleworn", "evo_quantum", "teklovossen_specialization"],
        is_evo=True,
        base_card="Evo Steel Soul Tower",
        pitch_value=1
    )
    
    # Weapons
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
    
    # Action Cards
    cards["Self-Assembly Protocol"] = Card(
        name="Self-Assembly Protocol",
        card_type=CardType.ACTION,
        cost={ResourceType.TEKLO_ENERGY: 1},
        abilities=["choose_two", "equip_evo", "nanite_counter", "cost_reduction", "graveyard_recursion"],
        theme="Nano",
        rarity="common",
        keywords=["nano", "instant"]
    )
    
    cards["Teklo Reconstitution Cycle"] = Card(
        name="Teklo Reconstitution Cycle",
        card_type=CardType.ACTION,
        cost={ResourceType.TEKLO_ENERGY: 1},
        pitch_value=2,
        defense_value=2,
        abilities=["choose_two", "equip_evo", "scrap", "repair_equipment", "instant_item"],
        theme="Nano",
        rarity="rare",
        keywords=["nano", "construct", "instant"]
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
    
    cards["Singularity Protocol: Nano Genesis"] = Card(
        name="Singularity Protocol: Nano Genesis",
        card_type=CardType.ACTION,
        cost={ResourceType.TEKLO_ENERGY: 2},
        abilities=["transform_hero", "nanite_ascendant"],
        theme="Nano",
        rarity="legendary",
        keywords=["modular_ascension", "construct"],
        pitch_value=0
    )
    
    # Base Equipment (for transformation targets)
    cards["Base Chest"] = Card(
        name="Base Chest",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 1},
        equipment_slot=EquipmentSlot.CHEST,
        defense_value=1,
        theme="Base",
        rarity="common"
    )
    
    cards["Base Head"] = Card(
        name="Base Head",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 1},
        equipment_slot=EquipmentSlot.HEAD,
        defense_value=1,
        theme="Base",
        rarity="common"
    )
    
    cards["Base Arms"] = Card(
        name="Base Arms",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 1},
        equipment_slot=EquipmentSlot.ARMS,
        defense_value=1,
        theme="Base",
        rarity="common"
    )
    
    cards["Base Legs"] = Card(
        name="Base Legs",
        card_type=CardType.EQUIPMENT,
        cost={ResourceType.TEKLO_ENERGY: 1},
        equipment_slot=EquipmentSlot.LEGS,
        defense_value=1,
        theme="Base",
        rarity="common"
    )
    
    cards["Teklo Leveler"] = Card(
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
    
    return cards


def create_deck_preset(preset_name: str, card_db: dict) -> list:
    """Create predefined deck configurations"""
    
    presets = {
        "nano_focused": [
            # Base equipment for transformations
            "Base Chest", "Base Head", "Base Arms", "Base Legs", "Teklo Leveler",
            
            # Nano core engine
            "Evo - Nanite Core Reactor", "Evo - NeuroWeave Visor", 
            "Evo - Phage Arms", "Evo - Swarm-Forged Tower",
            
            # Nano items and support
            "Item - Nanite Forge", "Item - Cloakfield Generator", "Item - Teklo Fabricator",
            "Self-Assembly Protocol", "Teklo Reconstitution Cycle",
            
            # Transformation cards
            "Nanite Devastator", "Singularity Protocol: Nano Genesis",
            
            # Additional copies for consistency
            "Self-Assembly Protocol", "Item - Nanite Forge",
            "Evo - NeuroWeave Visor", "Evo - Phage Arms"
        ],
        
        "ai_focused": [
            # Base equipment
            "Base Chest", "Base Head", "Base Arms", "Base Legs", "Teklo Leveler",
            
            # AI items
            "AI - Overclock Core", "AI - Predator Logic", 
            "AI - Singularity Cannon", "AI - Nemesis Driver",
            
            # Mixed equipment for versatility
            "Evo - NeuroWeave Visor", "Evo - Phage Arms",
            
            # Additional copies
            "AI - Overclock Core", "AI - Overclock Core", "AI - Nemesis Driver",
            "Self-Assembly Protocol", "Teklo Reconstitution Cycle"
        ],
        
        "quantum_focused": [
            # Base equipment
            "Base Chest", "Base Head", "Base Arms", "Base Legs", "Teklo Leveler",
            
            # Quantum evos
            "Evo - Quantum Processor", "Evo - Quantum Controller",
            "Evo - Quantum Nexus", "Evo - Quantum Tower",
            
            # Support cards
            "Self-Assembly Protocol", "Teklo Genesis Matrix",
            
            # Mixed synergies
            "AI - Overclock Core", "Item - Nanite Forge"
        ],
        
        "balanced_mix": [
            # Base equipment
            "Base Chest", "Base Head", "Base Arms", "Base Legs", "Teklo Leveler",
            
            # Mix of themes
            "Evo - Nanite Core Reactor", "Evo - NeuroWeave Visor",
            "AI - Overclock Core", "AI - Predator Logic",
            "Evo - Quantum Nexus",
            
            # Support and versatility
            "Item - Nanite Forge", "Self-Assembly Protocol", "Teklo Reconstitution Cycle",
            
            # Duplicates for consistency
            "Self-Assembly Protocol", "AI - Overclock Core", "Item - Nanite Forge"
        ]
    }
    
    if preset_name not in presets:
        raise ValueError(f"Unknown preset: {preset_name}")
    
    deck = []
    for card_name in presets[preset_name]:
        if card_name in card_db:
            deck.append(card_db[card_name])
        else:
            print(f"Warning: Card '{card_name}' not found in database")
    
    return deck


def create_opponent_deck(card_db: dict) -> list:
    """Create a simple opponent deck for testing"""
    # Generic aggro deck with basic cards
    opponent_cards = [
        "Base Chest", "Base Head", "Base Arms", "Base Legs", "Teklo Leveler"
    ] * 2  # Duplicate for multiple copies
    
    deck = []
    for card_name in opponent_cards:
        if card_name in card_db:
            deck.append(card_db[card_name])
    
    # Add some filler cards
    for i in range(10):
        deck.append(Card(
            name=f"Generic Attack {i}",
            card_type=CardType.ACTION,
            cost={ResourceType.ACTION_POINT: 1},
            attack_value=3,
            pitch_value=1
        ))
    
    return deck


# Balance scoring data for ML training
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
