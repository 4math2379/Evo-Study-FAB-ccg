"""Read a deck list file: one card per line, "<copies> <card id>", "#" starts a comment.

    # Nano Evo
    2 Evo - Phage Arms (1)
    3 Zipper Hit (3)

Card ids are "Name (pitch)", as listed in data/v2/cards.csv (or `teklo.cards_frame`).
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import teklo  # noqa: E402

CARD_CSV = ROOT / "notebooks" / "card.csv"
CUSTOM_CSV = ROOT / "custom_cards.csv"


def load_all_cards() -> list[teklo.Card]:
    return teklo.load_cards(CARD_CSV, CUSTOM_CSV)


def read_deck(path: str | Path, cards: list[teklo.Card]) -> list[teklo.Card]:
    by_id = {c.id: c for c in cards}
    counts: dict[str, int] = {}
    for n, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        copies, _, card_id = line.partition(" ")
        if not copies.isdigit() or not card_id.strip():
            raise SystemExit(f"{path}:{n}: expected '<copies> <card id>', got: {raw!r}")
        card_id = card_id.strip()
        if card_id not in by_id:
            hint = difflib.get_close_matches(card_id, by_id, n=3)
            raise SystemExit(f"{path}:{n}: unknown card {card_id!r}" + (f". Did you mean: {', '.join(hint)}?" if hint else ""))
        counts[card_id] = counts.get(card_id, 0) + int(copies)
    deck = teklo.deck_from_counts(counts, by_id)
    if len(deck) != 30:
        print(f"note: {path} has {len(deck)} cards; the model was trained on 30-card decks", file=sys.stderr)
    return deck
