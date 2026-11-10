"""Play one game between a deck list and the reference opponent, and print it turn by turn.

Needs no model: only the card CSVs.

    python examples/play_one_game.py examples/decks/nano_evo.txt
    python examples/play_one_game.py examples/decks/ai_overclock.txt --seed 7 --second
"""

from __future__ import annotations

import argparse

from decklist import load_all_cards, read_deck

import teklo  # noqa: E402  (decklist puts the repo root on sys.path)
from teklo.engine import play_game  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("deck", help="deck list file (see examples/decks)")
    parser.add_argument("--seed", type=int, default=42, help="shuffle seed (default 42)")
    parser.add_argument("--second", action="store_true", help="let the opponent go first")
    args = parser.parse_args()

    cards = load_all_cards()
    deck = read_deck(args.deck, cards)
    opponent = teklo.reference_opponent(teklo.generic_pool(cards))

    log: list[str] = []
    result = play_game(deck, opponent, seed=args.seed, a_first=not args.second, log=log)
    print("A = your deck, B = the reference opponent\n")
    print("\n".join(log))
    verdict = {"A": "your deck wins", "B": "the opponent wins", "draw": "draw"}[result.winner]
    print(f"\nResult: {verdict} after {result.turns} turns (life {result.life_a} to {result.life_b}).")


if __name__ == "__main__":
    main()
