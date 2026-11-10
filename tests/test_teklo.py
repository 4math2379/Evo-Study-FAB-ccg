"""Checks that the v2 simulator behaves like a game: run with `python -m pytest tests`."""

from pathlib import Path

import numpy as np
import pytest

import teklo
from teklo.cards import Card, Effects, parse_effects
from teklo.engine import play_game

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def cards():
    return teklo.load_cards(ROOT / "notebooks" / "card.csv", ROOT / "custom_cards.csv")


@pytest.fixture(scope="module")
def opponent(cards):
    return teklo.reference_opponent(teklo.generic_pool(cards))


def test_parser_reads_common_patterns():
    fx = parse_effects("The next attack action card you play this turn gains +2{p}. Draw a card.",
                       ("Go again",), "action")
    assert fx == Effects(go_again=True, power_bonus=2, draw=1)
    # an attack's own +N{p} is conditional, so it is not counted
    assert parse_effects("If you've boosted, this gets +3{p}.", ("Boost",), "attack").power_bonus == 0


def test_cards_load_and_keep_custom_ones(cards):
    assert len(cards) > 500
    assert sum(c.custom for c in cards) >= 30
    assert {c.kind for c in cards} == set(teklo.cards.KINDS)


def test_same_seed_same_game(opponent):
    first = play_game(opponent, opponent, seed=7)
    second = play_game(opponent, opponent, seed=7)
    assert first == second


def test_mirror_match_is_fair(opponent):
    result = teklo.evaluate_deck(opponent, opponent, n_games=400, seed=3)
    assert 0.42 < result["win_rate"] < 0.58


def test_pure_blue_deck_without_attacks_loses(opponent):
    filler = Card(id="Filler (3)", name="Filler", kind="action", cost=0, pitch=3, power=0, defense=2,
                  slot=None, theme="Generic", custom=False)
    result = teklo.evaluate_deck([filler] * 30, opponent, n_games=100, seed=1)
    assert result["win_rate"] < 0.2


def test_features_are_complete_and_pre_game(cards):
    deck = teklo.random_deck(teklo.teklo_pool(cards), np.random.default_rng(0))
    assert len(deck) == 30
    feats = teklo.deck_features(deck)
    assert list(feats) == teklo.FEATURES
    assert feats["n_red"] + feats["n_yellow"] + feats["n_blue"] <= 30
