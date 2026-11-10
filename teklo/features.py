"""Deck -> feature vector.

Every feature here is known *before* a game is played: it only looks at the deck list.
That is the fix for v1, where features such as average game length or final life were
measured from the games themselves and leaked the answer into the inputs.

Effects are split by *when* they happen, because that is how the game uses them:
items and Evo equipment repeat their effect every turn, other cards use it once.
(Notebook 02 shows how much this split matters.)
"""

from __future__ import annotations

from .cards import CUSTOM_THEMES, KINDS, Card

EFFECTS = ("power_bonus", "draw", "energy", "damage", "life")
ONGOING_KINDS = ("item", "evo")

FEATURES = [
    # what the deck is made of
    *[f"n_{k}" for k in KINDS],
    # resources: red, yellow and blue cards pitch for 1, 2 and 3
    "n_red", "n_yellow", "n_blue",
    "avg_cost", "avg_attack_power", "avg_defense", "n_big_attack",
    # tempo and synergy
    "n_go_again", "n_boost", "n_generic",
    # cards that do nothing in this simulator
    "n_dead",
    # what the rules text adds (read by the parser in teklo.cards), split by timing
    "n_ongoing", *[f"ongoing_{e}" for e in EFFECTS],
    *[f"once_{e}" for e in EFFECTS],
    # fan-made content
    "n_custom", *[f"n_{t}" for t in CUSTOM_THEMES],
]


def is_dead(card: Card) -> bool:
    """A card the simulator can't get any value from, except as pitch or a block."""
    if card.kind == "attack" or card.effects.go_again or card.effects.magnitude() > 0:
        return False
    if card.kind == "evo":
        return card.slot != "weapon" and card.defense <= 1  # an Evo is only useful if it adds defense
    return True


def deck_features(deck: list[Card]) -> dict[str, float]:
    n = len(deck)
    attacks = [c for c in deck if c.kind == "attack"]
    ongoing = [c for c in deck if c.kind in ONGOING_KINDS]
    once = [c for c in deck if c.kind not in ONGOING_KINDS]
    f: dict[str, float] = {f"n_{k}": sum(c.kind == k for c in deck) for k in KINDS}
    f.update({
        "n_red": sum(c.pitch == 1 for c in deck),
        "n_yellow": sum(c.pitch == 2 for c in deck),
        "n_blue": sum(c.pitch == 3 for c in deck),
        "avg_cost": sum(c.cost for c in deck) / n,
        "avg_attack_power": sum(c.power for c in attacks) / len(attacks) if attacks else 0.0,
        "avg_defense": sum(c.defense for c in deck) / n,
        "n_big_attack": sum(c.power >= 6 for c in attacks),
        "n_go_again": sum(c.effects.go_again for c in deck),
        "n_boost": sum(c.effects.boost for c in deck),
        "n_generic": sum(c.theme == "Generic" for c in deck),
        "n_dead": sum(is_dead(c) for c in deck),
        "n_ongoing": sum(c.effects.magnitude() > 0 for c in ongoing),
        "n_custom": sum(c.custom for c in deck),
    })
    for e in EFFECTS:
        f[f"ongoing_{e}"] = sum(getattr(c.effects, e) for c in ongoing)
        f[f"once_{e}"] = sum(getattr(c.effects, e) for c in once)
    f.update({f"n_{t}": sum(c.theme == t for c in deck) for t in CUSTOM_THEMES})
    return {k: f[k] for k in FEATURES}
