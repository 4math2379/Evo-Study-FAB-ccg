"""Predict a deck's win rate with the v2 model, and optionally check it by simulation.

Run notebooks/v2 01 to 03 first: they create models/v2/model.joblib.

    python examples/predict_deck.py examples/decks/nano_evo.txt
    python examples/predict_deck.py examples/decks/ai_overclock.txt --simulate 200
"""

from __future__ import annotations

import argparse
import json

import joblib
import pandas as pd

from decklist import ROOT, load_all_cards, read_deck

import teklo  # noqa: E402  (decklist puts the repo root on sys.path)

MODELS = ROOT / "models" / "v2"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("deck", help="deck list file (see examples/decks)")
    parser.add_argument("--simulate", type=int, default=0, metavar="N",
                        help="also play N games against the reference opponent to check the prediction")
    args = parser.parse_args()

    if not (MODELS / "model.joblib").exists():
        raise SystemExit("No model yet: run notebooks/v2/01_simulate, 02_dataset and 03_train_evaluate first.")
    model = joblib.load(MODELS / "model.joblib")
    features = json.loads((MODELS / "model_info.json").read_text())["features"]

    cards = load_all_cards()
    deck = read_deck(args.deck, cards)
    x = pd.DataFrame([teklo.deck_features(deck)])[features]
    predicted = float(model.predict(x)[0])

    print(f"Deck: {args.deck} ({len(deck)} cards, {sum(c.custom for c in deck)} fan-made)")
    print(f"Predicted win rate against the reference opponent: {predicted:.0%}")
    shown = ["n_attack", "n_item", "n_evo", "avg_attack_power", "avg_defense", "n_ongoing", "n_dead"]
    print("Key features: " + ", ".join(f"{k}={x.iloc[0][k]:g}" for k in shown))

    if args.simulate:
        opponent = teklo.reference_opponent(teklo.generic_pool(cards))
        result = teklo.evaluate_deck(deck, opponent, n_games=args.simulate, seed=1)
        print(f"Simulated over {args.simulate} games: {result['win_rate']:.0%} "
              f"(difference {result['win_rate'] - predicted:+.0%})")


if __name__ == "__main__":
    main()
