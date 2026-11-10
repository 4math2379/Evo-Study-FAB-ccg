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


def _card(name, kind="attack", cost=0, pitch=1, power=0, defense=0, slot=None, keywords=(), **fx):
    return Card(id=f"{name} ({pitch})", name=name, kind=kind, cost=cost, pitch=pitch, power=power,
                defense=defense, slot=slot, theme="Mechanologist", custom=False, keywords=keywords,
                effects=Effects(**fx))


def test_random_deck_respects_size_and_small_pools(cards):
    pool = teklo.teklo_pool(cards)
    rng = np.random.default_rng(1)
    for size in (5, 30, 60):
        assert len(teklo.random_deck(pool, rng, size=size)) == size
    small = pool[:4]
    assert len(teklo.random_deck(small, rng, size=12)) == 12
    with pytest.raises(ValueError):
        teklo.random_deck(small, rng, size=13)  # 4 cards x 3 copies can't make 13


def test_free_go_again_attack_beats_the_weapon():
    from teklo.engine import Duel
    duel = Duel([], [], seed=0)
    rabble = _card("Rabble", power=5, go_again=True)
    duel.a.hand = [rabble]
    play, _ = duel._choose_play(duel.a, floating=0, bonus=0, weapon_ready=True)
    assert play == 0


def test_planned_attack_is_not_pitched():
    from teklo.engine import Duel
    duel = Duel([], [], seed=0)
    item = _card("Overclock", kind="item", cost=1, power_bonus=2)
    attack = _card("Big hit", cost=0, pitch=3, power=6)
    filler = _card("Filler", pitch=1)
    duel.a.hand = [item, attack, filler]
    play, reserve = duel._choose_play(duel.a, floating=0, bonus=0, weapon_ready=False)
    assert play == 0 and reserve is attack
    duel.a.hand.pop(play)
    duel.a.pay(1, 0, reserve)
    assert attack in duel.a.hand and filler not in duel.a.hand


def test_blade_break_removes_the_effect():
    from teklo.engine import Duel, Gear
    duel = Duel([], [], seed=0)
    duel.a.hand = []
    duel.a.gear = {"head": Gear(2, blade_break=True, effects=Effects(draw=1))}
    Duel._defend(duel.a, power=5)
    assert duel.a.gear["head"].defense == 0
    assert duel.a.ongoing_effects() == [Effects()]


def test_features_are_complete_and_pre_game(cards):
    deck = teklo.random_deck(teklo.teklo_pool(cards), np.random.default_rng(0))
    assert len(deck) == 30
    feats = teklo.deck_features(deck)
    assert list(feats) == teklo.FEATURES
    assert feats["n_red"] + feats["n_yellow"] + feats["n_blue"] <= 30
