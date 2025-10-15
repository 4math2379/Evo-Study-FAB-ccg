"""
Teklovossen Game Simulation Module
Core simulation engine and card database for Flesh and Blood gameplay analysis
"""

from .game_engine import (
    GameEngine,
    GameState,
    Player,
    Card,
    CardType,
    EquipmentSlot,
    ResourceType
)

from .card_database import (
    create_card_database,
    create_deck_preset,
    create_opponent_deck,
    CARD_BALANCE_SCORES
)

__version__ = "1.0.0"
__author__ = "Teklovossen Card Balance Team"

__all__ = [
    # Game Engine
    'GameEngine',
    'GameState', 
    'Player',
    'Card',
    'CardType',
    'EquipmentSlot',
    'ResourceType',
    
    # Card Database
    'create_card_database',
    'create_deck_preset',
    'create_opponent_deck',
    'CARD_BALANCE_SCORES'
]
