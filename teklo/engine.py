"""A small Flesh and Blood-style duel, built to generate training data.

This is not a rules engine. It keeps the parts of the game that make deck building matter
and drops the rest, so that every rule fits on one screen:

* Each hero starts with 20 life, a weapon (3 power, costs 1 to attack, once per turn)
  and four base equipment pieces (1 defense each).
* Each turn you have one action point. You pay costs by pitching cards from hand
  (red = 1, yellow = 2, blue = 3 resources) or by spending stored Teklo Energy.
* Cards with Go again, items, Evo equipment and instants give the action point back.
* Boost (Mechanologist): when you attack with a Boost card you banish the top card of your
  deck; if it is not a Generic card, the attack gains Go again.
* Items and Evo equipment stay in play and repeat their effects at the start of each turn.
  Evo equipment replaces the base piece in its slot (better defense).
* The defender blocks with equipment first (each block wears it down by 1; Blade Break
  pieces are destroyed) and then with up to two cards from hand.
* At the end of your turn you draw back up to 4 cards.
* The game ends when a hero reaches 0 life. After 40 turns the hero with more life wins.

Both players use the same simple decision rules (see ``_choose_play`` and ``_defend``).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .cards import SLOTS, Card, Effects

HERO_LIFE = 20
INTELLECT = 4
WEAPON_POWER = 3
WEAPON_COST = 1
BASE_EQUIPMENT_DEFENSE = 1
ENERGY_CAP = 5
MAX_TURNS = 40
MAX_HAND_BLOCKS = 2


@dataclass
class Gear:
    defense: int
    blade_break: bool = False
    effects: Effects = Effects()
    name: str = "base"


class Player:
    def __init__(self, name: str, deck: list[Card], rng: random.Random):
        self.name = name
        self.deck = list(deck)
        rng.shuffle(self.deck)
        self.hand: list[Card] = []
        self.life = HERO_LIFE
        self.gear = {slot: Gear(BASE_EQUIPMENT_DEFENSE) for slot in SLOTS}
        self.weapon_power = WEAPON_POWER
        self.items: list[Card] = []
        self.energy = 0
        self.damage_dealt = 0
        self.cards_played = 0
        self.draw(INTELLECT)

    def draw(self, n: int) -> None:
        for _ in range(n):
            if not self.deck:
                return
            self.hand.append(self.deck.pop(0))

    def refill(self) -> None:
        self.draw(max(0, INTELLECT - len(self.hand)))

    def ongoing_effects(self) -> list[Effects]:
        return [c.effects for c in self.items] + [g.effects for g in self.gear.values()]

    def pitch_total(self, skip: int | None = None) -> int:
        return sum(c.pitch for i, c in enumerate(self.hand) if i != skip)

    def pay(self, cost: int, floating: int, reserve: Card | None = None) -> int:
        """Pay a cost: floating resources, then Teklo Energy, then pitch (blue cards first).

        ``reserve`` is a card in hand that must not be pitched, because the player plans to
        play it next. Returns the resources still floating afterwards. The caller checks
        affordability.
        """
        if floating >= cost:
            return floating - cost
        cost -= floating
        used = min(self.energy, cost)
        self.energy -= used
        cost -= used
        floating = 0
        # keep one copy of the reserved card (the attack planned next) out of the pitch
        keep = next((j for j, c in enumerate(self.hand) if c is reserve), None)
        while cost > 0:
            # pitch the card with the most resources; among equals, the weakest attacker
            options = [j for j in range(len(self.hand)) if j != keep] or list(range(len(self.hand)))
            i = max(options, key=lambda j: (self.hand[j].pitch, -self.hand[j].power))
            if keep is not None and i < keep:
                keep -= 1
            card = self.hand.pop(i)
            self.deck.append(card)  # pitched cards go to the bottom of the deck
            floating += card.pitch
            if floating >= cost:
                return floating - cost
            cost -= floating
            floating = 0
        return floating


@dataclass
class GameResult:
    winner: str  # "A", "B" or "draw"
    turns: int
    life_a: int
    life_b: int
    a_first: bool


class Duel:
    def __init__(self, deck_a: list[Card], deck_b: list[Card], seed: int, a_first: bool = True,
                 log: list[str] | None = None):
        self.rng = random.Random(seed)
        self.a = Player("A", deck_a, self.rng)
        self.b = Player("B", deck_b, self.rng)
        self.a_first = a_first
        self.log = log

    def _say(self, msg: str) -> None:
        if self.log is not None:
            self.log.append(msg)

    # -- the whole game ------------------------------------------------------

    def play(self) -> GameResult:
        order = (self.a, self.b) if self.a_first else (self.b, self.a)
        turn = 0
        for turn in range(1, MAX_TURNS + 1):
            me, foe = order[(turn - 1) % 2], order[turn % 2]
            self._say(f"--- turn {turn}: {me.name} (life {me.life}) vs {foe.name} (life {foe.life})")
            self._take_turn(me, foe)
            if foe.life <= 0 or me.life <= 0:
                break
        if self.a.life <= 0 < self.b.life:
            winner = "B"
        elif self.b.life <= 0 < self.a.life:
            winner = "A"
        elif self.a.life != self.b.life:
            winner = "A" if self.a.life > self.b.life else "B"
        else:
            winner = "draw"
        self._say(f"=== winner: {winner} after {turn} turns (A {self.a.life}, B {self.b.life})")
        return GameResult(winner, turn, self.a.life, self.b.life, self.a_first)

    # -- one turn ------------------------------------------------------------

    def _take_turn(self, me: Player, foe: Player) -> None:
        bonus = 0
        for fx in me.ongoing_effects():
            bonus += fx.power_bonus
            me.energy = min(ENERGY_CAP, me.energy + fx.energy)
            me.draw(fx.draw)
            foe.life -= fx.damage
            me.life += fx.life
        floating = 0
        action_points = 1
        weapon_ready = True

        while action_points > 0 and foe.life > 0:
            play, reserve = self._choose_play(me, floating, bonus, weapon_ready)
            if play is None:
                break
            action_points -= 1
            if play == "weapon":
                floating = me.pay(WEAPON_COST, floating)
                weapon_ready = False
                self._say(f"{me.name} attacks with the weapon")
                self._attack(me, foe, me.weapon_power + bonus)
                bonus = 0
                continue

            card = me.hand.pop(play)
            floating = me.pay(card.cost, floating, reserve)
            me.cards_played += 1
            go_again = card.effects.go_again or card.kind in ("item", "evo", "instant")
            fx = card.effects

            if card.kind == "item":
                me.items.append(card)
                self._say(f"{me.name} plays item {card.id}")
            elif card.kind == "evo":
                self._equip(me, card)
            elif card.kind in ("action", "instant"):
                bonus += fx.power_bonus
                self._apply_once(me, foe, fx)
                self._say(f"{me.name} plays {card.id} (bonus now +{bonus})")
            else:  # attack
                if fx.boost and len(me.deck) > 5:
                    top = me.deck.pop(0)  # banished
                    if top.theme != "Generic":
                        go_again = True
                    self._say(f"{me.name} boosts, banishing {top.id}")
                self._say(f"{me.name} attacks with {card.id}")
                if self._attack(me, foe, card.power + bonus):
                    self._apply_once(me, foe, fx)
                bonus = 0
            if go_again:
                action_points += 1

        me.refill()

    @staticmethod
    def _apply_once(me: Player, foe: Player, fx: Effects) -> None:
        me.energy = min(ENERGY_CAP, me.energy + fx.energy)
        me.draw(fx.draw)
        foe.life -= fx.damage
        me.life += fx.life

    def _equip(self, me: Player, card: Card) -> None:
        if card.slot == "weapon":
            me.weapon_power = max(me.weapon_power, card.power)
        else:
            me.gear[card.slot] = Gear(card.defense, "Blade Break" in card.keywords, card.effects, card.id)
        self._say(f"{me.name} equips Evo {card.id}")

    # -- decisions -----------------------------------------------------------

    @staticmethod
    def _value(me: Player, card: Card, bonus: int) -> float:
        """How much a simulated player wants to play a card right now."""
        fx = card.effects
        if card.kind == "attack":
            return card.power + bonus + (1.5 if fx.go_again or fx.boost else 0) - 0.3 * card.cost
        if card.kind in ("action", "instant"):
            return 1 + fx.power_bonus + 1.5 * fx.draw + fx.energy + fx.damage + 0.5 * fx.life
        if card.kind == "item":
            return 1.5 + 2 * fx.magnitude()
        # evo
        if card.slot == "weapon":
            return 1 + 2 * (card.power - me.weapon_power)
        upgrade = card.defense - me.gear[card.slot].defense
        return 1 + upgrade + 2 * fx.magnitude()

    def _choose_play(self, me: Player, floating: int, bonus: int, weapon_ready: bool):
        """Pick what to play: (hand index or "weapon" or None, card to keep out of the pitch).

        Rule of thumb: play cards that keep the turn going (Go again, items, Evos, instants)
        first, as long as the best attack is still affordable afterwards; then make the best
        attack. Attacks with Go again count both ways: they keep the turn going, and they can
        be the final attack.
        """
        budget = floating + me.energy
        keep_going, finishers = [], []
        for i, card in enumerate(me.hand):
            if card.cost > budget + me.pitch_total(skip=i):
                continue
            value = self._value(me, card, bonus)
            if value <= 0:
                continue
            go = card.effects.go_again or card.kind in ("item", "evo", "instant")
            if go:
                keep_going.append((value, i))
            if not go or card.kind == "attack":
                finishers.append((value, i))
        if weapon_ready and WEAPON_COST <= budget + me.pitch_total():
            finishers.append((me.weapon_power + bonus - 0.5 * WEAPON_COST, "weapon"))

        best_finisher = max(finishers, key=lambda t: t[0]) if finishers else None
        for value, i in sorted(keep_going, key=lambda t: t[0], reverse=True):
            if value < 1:
                break
            if best_finisher is None:
                return i, None
            fin = best_finisher[1]
            if fin == i:  # this card is the best attack itself
                return i, None
            # still able to pay for the best finisher after playing this card?
            fin_cost = WEAPON_COST if fin == "weapon" else me.hand[fin].cost
            card = me.hand[i]
            left = budget + me.pitch_total(skip=i) - card.cost
            if fin != "weapon":
                left -= me.hand[fin].pitch
            if left >= fin_cost:
                return i, (None if fin == "weapon" else me.hand[fin])
        if best_finisher and best_finisher[0] >= 2:
            return best_finisher[1], None
        return None, None

    def _attack(self, me: Player, foe: Player, power: int) -> bool:
        blocked = self._defend(foe, power)
        damage = max(0, power - blocked)
        foe.life -= damage
        me.damage_dealt += damage
        self._say(f"  {power} power, {blocked} blocked, {damage} damage -> {foe.name} at {foe.life}")
        return damage > 0

    @staticmethod
    def _defend(foe: Player, power: int) -> int:
        """Block with equipment first, then with up to two cards from hand."""
        blocked = 0
        for gear in sorted(foe.gear.values(), key=lambda g: g.defense, reverse=True):
            left = power - blocked
            if left < 2 and left < foe.life:
                break
            if gear.defense <= 0:
                break
            blocked += gear.defense
            if gear.blade_break:  # destroyed: no defense and no more effects
                gear.defense = 0
                gear.effects = Effects()
            else:
                gear.defense -= 1
        hand_blocks = 0
        while foe.hand and hand_blocks < MAX_HAND_BLOCKS:
            left = power - blocked
            lethal = left >= foe.life
            if left < 3 and not lethal:
                break
            j = max(range(len(foe.hand)), key=lambda k: foe.hand[k].defense)
            if foe.hand[j].defense < (1 if lethal else 2):
                break
            blocked += foe.hand.pop(j).defense
            hand_blocks += 1
        return blocked


def play_game(deck_a: list[Card], deck_b: list[Card], seed: int, a_first: bool = True,
              log: list[str] | None = None) -> GameResult:
    return Duel(deck_a, deck_b, seed, a_first, log).play()


def evaluate_deck(deck: list[Card], opponent: list[Card], n_games: int, seed: int) -> dict:
    """Play ``n_games`` against the opponent, alternating who goes first."""
    wins = draws = turns = life_diff = 0
    for g in range(n_games):
        r = play_game(deck, opponent, seed=seed * 100_003 + g, a_first=(g % 2 == 0))
        wins += r.winner == "A"
        draws += r.winner == "draw"
        turns += r.turns
        life_diff += max(r.life_a, 0) - max(r.life_b, 0)
    return {
        "games": n_games,
        "wins": wins,
        "draws": draws,
        "win_rate": (wins + 0.5 * draws) / n_games,
        "avg_turns": turns / n_games,
        "avg_life_diff": life_diff / n_games,
    }
