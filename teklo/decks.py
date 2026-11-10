"""Random deck generation, so the model sees many different decks instead of 9 presets."""

from __future__ import annotations

from collections import Counter

import numpy as np

from .cards import KINDS, Card

DECK_SIZE = 30
MAX_COPIES = 3

# Dirichlet weights: on average decks are mostly attacks, but some lean on items or Evos.
KIND_ALPHA = {"attack": 4.0, "action": 1.2, "instant": 0.5, "item": 1.2, "evo": 1.0}


def random_deck(pool: list[Card], rng: np.random.Generator, size: int = DECK_SIZE) -> list[Card]:
    """Build a random but deck-like list: 10 to 15 different cards, 1 to 3 copies each.

    Each deck also draws its own preferences: how much it leans on each card kind, on the
    fan-made cards and on Generic cards. That spread is what lets a model learn later.
    """
    by_kind = {k: [c for c in pool if c.kind == k] for k in KINDS}
    kinds = [k for k in KINDS if by_kind[k]]
    kind_weights = rng.dirichlet([KIND_ALPHA[k] for k in kinds])
    custom_pref = rng.uniform(0.2, 6.0)  # > 1 means this deck favours fan-made cards
    generic_pref = rng.uniform(0.05, 1.0)

    def card_weight(c: Card) -> float:
        if c.custom:
            return custom_pref
        if c.theme == "Generic":
            return generic_pref
        return 1.0

    n_distinct = int(rng.integers(10, 16))
    chosen: list[Card] = []
    while len(chosen) < n_distinct:
        kind = kinds[rng.choice(len(kinds), p=kind_weights)]
        candidates = [c for c in by_kind[kind] if c not in chosen]
        if not candidates:
            continue
        w = np.array([card_weight(c) for c in candidates])
        chosen.append(candidates[rng.choice(len(candidates), p=w / w.sum())])

    copies = Counter({c.id: 1 for c in chosen})
    while sum(copies.values()) < size:
        c = chosen[rng.integers(len(chosen))]
        if copies[c.id] < MAX_COPIES:
            copies[c.id] += 1
    by_id = {c.id: c for c in chosen}
    return [by_id[cid] for cid, n in copies.items() for _ in range(n)]


def reference_opponent(generic_cards: list[Card], seed: int = 2025) -> list[Card]:
    """A fixed Generic deck every Teklovossen deck is measured against.

    It favours efficient attacks (power at least cost + 3) and mixes in some non-attacks.
    """
    rng = np.random.default_rng(seed)
    attacks = [c for c in generic_cards if c.kind == "attack" and c.power >= c.cost + 3]
    others = [c for c in generic_cards if c.kind in ("action", "instant") and c.effects.magnitude() > 0]
    picks = list(rng.choice(len(attacks), size=8, replace=False))
    deck = [attacks[i] for i in picks for _ in range(3)]
    picks = list(rng.choice(len(others), size=3, replace=False))
    deck += [others[i] for i in picks for _ in range(2)]
    return deck[:DECK_SIZE]


def deck_counts(deck: list[Card]) -> Counter:
    return Counter(c.id for c in deck)


def deck_from_counts(counts: dict[str, int], cards_by_id: dict[str, Card]) -> list[Card]:
    return [cards_by_id[cid] for cid, n in counts.items() for _ in range(int(n))]
