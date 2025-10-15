"""
Teklovossen Game Simulation Engine
Core framework for simulating Flesh and Blood gameplay with Teklovossen cards[Dunno if its work lol]
"""

import random
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid


class CardType(Enum):
    EQUIPMENT = "equipment"
    ITEM = "item"
    ACTION = "action"
    ATTACK = "attack"
    REACTION = "reaction"


class EquipmentSlot(Enum):
    HEAD = "head"
    CHEST = "chest"
    ARMS = "arms"
    LEGS = "legs"
    WEAPON = "weapon"


class ResourceType(Enum):
    TEKLO_ENERGY = "teklo_energy"
    NANITE_COUNTER = "nanite_counter"
    QUANTUM_CHARGE = "quantum_charge"
    ACTION_POINT = "action_point"


@dataclass
class Card:
    """Represents a single card with all its properties"""
    name: str
    card_type: CardType
    cost: Dict[ResourceType, int] = field(default_factory=dict)
    pitch_value: int = 0
    attack_value: int = 0
    defense_value: int = 0
    life_value: int = 0
    equipment_slot: Optional[EquipmentSlot] = None
    keywords: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)
    theme: str = ""  # AI, Nano, Quantum, Biomancy
    rarity: str = "common"  # common, rare, legendary
    is_evo: bool = False
    base_card: Optional[str] = None  # For Evo transformations
    
    def __post_init__(self):
        self.id = str(uuid.uuid4())
    
    def can_activate(self, resources: Dict[ResourceType, int]) -> bool:
        """Check if player has enough resources to activate this card"""
        for resource_type, required in self.cost.items():
            if resources.get(resource_type, 0) < required:
                return False
        return True
    
    def is_battleworn(self) -> bool:
        """Check if card has battleworn property"""
        return "battleworn" in self.keywords


@dataclass
class Player:
    """Represents a player's game state"""
    name: str
    life: int = 20
    resources: Dict[ResourceType, int] = field(default_factory=lambda: {
        ResourceType.TEKLO_ENERGY: 0,
        ResourceType.NANITE_COUNTER: 0,
        ResourceType.QUANTUM_CHARGE: 0,
        ResourceType.ACTION_POINT: 1
    })
    
    # Game zones
    hand: List[Card] = field(default_factory=list)
    deck: List[Card] = field(default_factory=list)
    graveyard: List[Card] = field(default_factory=list)
    banished: List[Card] = field(default_factory=list)
    
    # Equipment zones
    equipment: Dict[EquipmentSlot, Optional[Card]] = field(default_factory=lambda: {
        EquipmentSlot.HEAD: None,
        EquipmentSlot.CHEST: None,
        EquipmentSlot.ARMS: None,
        EquipmentSlot.LEGS: None,
        EquipmentSlot.WEAPON: None
    })
    
    # Items and arsenals
    items: List[Card] = field(default_factory=list)
    arsenal: List[Card] = field(default_factory=list)
    
    # Counters and tokens
    counters: Dict[str, int] = field(default_factory=dict)
    
    def draw_cards(self, count: int = 1) -> List[Card]:
        """Draw cards from deck to hand"""
        drawn = []
        for _ in range(min(count, len(self.deck))):
            if self.deck:
                card = self.deck.pop(0)
                self.hand.append(card)
                drawn.append(card)
        return drawn
    
    def gain_resource(self, resource_type: ResourceType, amount: int = 1):
        """Gain specified resource"""
        self.resources[resource_type] = self.resources.get(resource_type, 0) + amount
    
    def spend_resource(self, resource_type: ResourceType, amount: int = 1) -> bool:
        """Spend specified resource if available"""
        if self.resources.get(resource_type, 0) >= amount:
            self.resources[resource_type] -= amount
            return True
        return False
    
    def can_equip(self, card: Card) -> bool:
        """Check if card can be equipped"""
        if not card.equipment_slot:
            return False
        
        # Check if slot is empty or card is Evo transformation
        slot = card.equipment_slot
        current_equipment = self.equipment[slot]
        
        if current_equipment is None:
            return True
        
        # Allow Evo transformation if this is an Evo of the current equipment
        if card.is_evo and current_equipment.name == card.base_card:
            return True
            
        return False
    
    def equip_card(self, card: Card) -> bool:
        """Equip a card if possible"""
        if not self.can_equip(card):
            return False
        
        slot = card.equipment_slot
        old_card = self.equipment[slot]
        
        # If this is an Evo transformation, send base to graveyard
        if card.is_evo and old_card:
            self.graveyard.append(old_card)
        
        self.equipment[slot] = card
        if card in self.hand:
            self.hand.remove(card)
        return True
    
    def get_equipped_evos(self) -> List[Card]:
        """Get all equipped Evo cards"""
        evos = []
        for equipment in self.equipment.values():
            if equipment and equipment.is_evo:
                evos.append(equipment)
        return evos
    
    def count_theme_items(self, theme: str) -> int:
        """Count items of a specific theme"""
        return sum(1 for item in self.items if item.theme.lower() == theme.lower())


@dataclass
class GameState:
    """Represents the complete game state"""
    players: List[Player]
    current_player_index: int = 0
    turn_number: int = 1
    phase: str = "start"  # start, main, combat, end
    
    # Combat state
    attacking_card: Optional[Card] = None
    defending_player: Optional[Player] = None
    combat_chain: List[Card] = field(default_factory=list)
    
    # Game log for analysis
    game_log: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]
    
    @property
    def opponent(self) -> Player:
        return self.players[1 - self.current_player_index]
    
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log game events for analysis"""
        event = {
            'turn': self.turn_number,
            'phase': self.phase,
            'player': self.current_player.name,
            'event_type': event_type,
            'timestamp': len(self.game_log),
            'data': data
        }
        self.game_log.append(event)
    
    def start_turn(self):
        """Start a new turn"""
        player = self.current_player
        
        # Draw cards (Arsenal phase)
        cards_to_draw = 1  # Base draw
        drawn = player.draw_cards(cards_to_draw)
        
        # Gain action point
        player.gain_resource(ResourceType.ACTION_POINT, 1)
        
        # Generate Teklo Energy (hero ability simulation)
        teklo_generation = self._calculate_teklo_generation(player)
        player.gain_resource(ResourceType.TEKLO_ENERGY, teklo_generation)
        
        self.log_event('turn_start', {
            'cards_drawn': len(drawn),
            'teklo_energy_gained': teklo_generation,
            'resources': dict(player.resources)
        })
        
        self.phase = "main"
    
    def _calculate_teklo_generation(self, player: Player) -> int:
        """Calculate Teklo Energy generation based on equipped items"""
        base_generation = 1
        bonus = 0
        
        # Check for energy-generating equipment
        for equipment in player.equipment.values():
            if equipment and "teklo_energy_generation" in equipment.keywords:
                bonus += 1
        
        return base_generation + bonus
    
    def end_turn(self):
        """End current turn and switch to next player"""
        player = self.current_player
        
        # Reset action points
        player.resources[ResourceType.ACTION_POINT] = 0
        
        # Apply end-of-turn effects
        self._apply_end_turn_effects(player)
        
        self.log_event('turn_end', {
            'resources_remaining': dict(player.resources)
        })
        
        # Switch to next player
        self.current_player_index = 1 - self.current_player_index
        if self.current_player_index == 0:
            self.turn_number += 1
        
        self.phase = "start"
    
    def _apply_end_turn_effects(self, player: Player):
        """Apply end-of-turn effects like Nanite counter decay"""
        # Quantum charges decay (example mechanic)
        if ResourceType.QUANTUM_CHARGE in player.resources:
            decay_amount = player.resources[ResourceType.QUANTUM_CHARGE] // 2
            player.resources[ResourceType.QUANTUM_CHARGE] -= decay_amount
            if decay_amount > 0:
                self.log_event('resource_decay', {
                    'resource': 'quantum_charge',
                    'amount': decay_amount
                })


class GameEngine:
    """Main game engine for running simulations"""
    
    def __init__(self):
        self.game_state: Optional[GameState] = None
    
    def initialize_game(self, player1_deck: List[Card], player2_deck: List[Card]) -> GameState:
        """Initialize a new game with given decks"""
        player1 = Player(name="Teklovossen", deck=player1_deck.copy())
        player2 = Player(name="Opponent", deck=player2_deck.copy())
        
        # Shuffle decks
        random.shuffle(player1.deck)
        random.shuffle(player2.deck)
        
        # Draw starting hands
        player1.draw_cards(5)
        player2.draw_cards(5)
        
        self.game_state = GameState(players=[player1, player2])
        return self.game_state
    
    def simulate_turn(self) -> Dict[str, Any]:
        """Simulate a single turn with AI decision making"""
        if not self.game_state:
            raise ValueError("Game not initialized")
        
        self.game_state.start_turn()
        
        # Simulate player decisions
        turn_data = self._simulate_player_actions()
        
        self.game_state.end_turn()
        
        return turn_data
    
    def _simulate_player_actions(self) -> Dict[str, Any]:
        """Simulate intelligent player actions during their turn"""
        player = self.game_state.current_player
        actions_taken = []
        
        # Priority system for actions
        while player.resources[ResourceType.ACTION_POINT] > 0:
            action = self._choose_best_action(player)
            if action:
                result = self._execute_action(action)
                actions_taken.append(result)
            else:
                break  # No more viable actions
        
        return {
            'actions': actions_taken,
            'resources_used': self._calculate_resources_used(player),
            'cards_played': len([a for a in actions_taken if a['type'] in ['equip', 'activate']])
        }
    
    def _choose_best_action(self, player: Player) -> Optional[Dict[str, Any]]:
        """Choose the best available action using heuristics"""
        possible_actions = []
        
        # Equipment actions
        for card in player.hand:
            if card.card_type == CardType.EQUIPMENT and player.can_equip(card):
                if card.can_activate(player.resources):
                    priority = self._calculate_equipment_priority(card, player)
                    possible_actions.append({
                        'type': 'equip',
                        'card': card,
                        'priority': priority
                    })
        
        # Item activation actions
        for item in player.items:
            if item.can_activate(player.resources):
                priority = self._calculate_item_priority(item, player)
                possible_actions.append({
                    'type': 'activate_item',
                    'card': item,
                    'priority': priority
                })
        
        # Attack actions
        weapon = player.equipment[EquipmentSlot.WEAPON]
        if weapon and weapon.can_activate(player.resources):
            priority = self._calculate_attack_priority(weapon, player)
            possible_actions.append({
                'type': 'attack',
                'card': weapon,
                'priority': priority
            })
        
        # Choose highest priority action
        if possible_actions:
            return max(possible_actions, key=lambda x: x['priority'])
        
        return None
    
    def _calculate_equipment_priority(self, card: Card, player: Player) -> float:
        """Calculate priority for equipping a card"""
        base_priority = 5.0
        
        # Evo transformations get high priority
        if card.is_evo:
            base_priority += 3.0
        
        # Cards that generate resources get priority
        if "teklo_energy_generation" in card.keywords:
            base_priority += 2.0
        
        # Theme synergy bonus
        theme_items = player.count_theme_items(card.theme)
        base_priority += theme_items * 0.5
        
        return base_priority
    
    def _calculate_item_priority(self, card: Card, player: Player) -> float:
        """Calculate priority for activating an item"""
        base_priority = 3.0
        
        # Resource generation items get priority when resources are low
        total_resources = sum(player.resources.values())
        if total_resources < 5:
            base_priority += 2.0
        
        # Combat items get priority during combat
        if "combat" in card.abilities:
            base_priority += 1.5
        
        return base_priority
    
    def _calculate_attack_priority(self, card: Card, player: Player) -> float:
        """Calculate priority for attacking"""
        base_priority = 4.0
        
        # Higher attack value = higher priority
        base_priority += card.attack_value * 0.3
        
        # Priority increases if opponent is low on life
        opponent_life_ratio = self.game_state.opponent.life / 20.0
        if opponent_life_ratio < 0.5:
            base_priority += 3.0
        
        return base_priority
    
    def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a chosen action and return results"""
        player = self.game_state.current_player
        action_type = action['type']
        card = action['card']
        
        result = {
            'type': action_type,
            'card_name': card.name,
            'success': False,
            'effects': []
        }
        
        if action_type == 'equip':
            if player.equip_card(card):
                # Pay costs
                for resource, amount in card.cost.items():
                    player.spend_resource(resource, amount)
                
                player.spend_resource(ResourceType.ACTION_POINT, 1)
                result['success'] = True
                result['effects'].append(f"Equipped {card.name}")
                
                self.game_state.log_event('equip', {
                    'card': card.name,
                    'slot': card.equipment_slot.value if card.equipment_slot else None
                })
        
        elif action_type == 'activate_item':
            # Pay costs
            for resource, amount in card.cost.items():
                player.spend_resource(resource, amount)
            
            # Apply item effects (simplified)
            self._apply_item_effects(card, player, result)
            result['success'] = True
            
            self.game_state.log_event('activate_item', {
                'card': card.name,
                'theme': card.theme
            })
        
        elif action_type == 'attack':
            damage_dealt = self._resolve_attack(card, player)
            result['success'] = True
            result['effects'].append(f"Dealt {damage_dealt} damage")
            
            self.game_state.log_event('attack', {
                'card': card.name,
                'damage': damage_dealt
            })
        
        return result
    
    def _apply_item_effects(self, card: Card, player: Player, result: Dict[str, Any]):
        """Apply effects of activated items"""
        # Simplified effect system - can be expanded
        if "draw_card" in card.abilities:
            drawn = player.draw_cards(1)
            result['effects'].append(f"Drew {len(drawn)} card(s)")
        
        if "gain_teklo_energy" in card.abilities:
            player.gain_resource(ResourceType.TEKLO_ENERGY, 1)
            result['effects'].append("Gained 1 Teklo Energy")
        
        if "gain_nanite_counter" in card.abilities:
            player.gain_resource(ResourceType.NANITE_COUNTER, 1)
            result['effects'].append("Gained 1 Nanite Counter")
    
    def _resolve_attack(self, weapon: Card, attacker: Player) -> int:
        """Resolve an attack and return damage dealt"""
        base_damage = weapon.attack_value
        
        # Pay attack costs
        for resource, amount in weapon.cost.items():
            attacker.spend_resource(resource, amount)
        
        attacker.spend_resource(ResourceType.ACTION_POINT, 1)
        
        # Apply damage to opponent
        damage_dealt = min(base_damage, self.game_state.opponent.life)
        self.game_state.opponent.life -= damage_dealt
        
        return damage_dealt
    
    def _calculate_resources_used(self, player: Player) -> Dict[str, int]:
        """Calculate resources used during the turn"""
        # This would track resource changes - simplified for now
        return {
            'teklo_energy': 0,  # Would track actual usage
            'nanite_counters': 0,
            'action_points': 0
        }
    
    def is_game_over(self) -> bool:
        """Check if game is over"""
        return any(player.life <= 0 for player in self.game_state.players)
    
    def get_winner(self) -> Optional[Player]:
        """Get the winning player"""
        for player in self.game_state.players:
            if player.life > 0 and any(p.life <= 0 for p in self.game_state.players if p != player):
                return player
        return None
