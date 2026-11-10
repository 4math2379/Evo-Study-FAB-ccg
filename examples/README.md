# 🧪 Examples

Small scripts that use the [`teklo`](../teklo) package directly. Run them from the repository root, inside the virtual environment.

| Script | What it does | Needs |
|---|---|---|
| [`predict_deck.py`](predict_deck.py) | predicts a deck's win rate against the reference opponent, and with `--simulate N` checks it by playing N games | the model from notebooks 01 to 03 |
| [`play_one_game.py`](play_one_game.py) | plays one game against the reference opponent and prints it turn by turn | nothing |
| [`decklist.py`](decklist.py) | reads deck list files; used by the two scripts above | |

```bash
python examples/predict_deck.py examples/decks/nano_evo.txt --simulate 200
python examples/play_one_game.py examples/decks/ai_overclock.txt --seed 7
```

```text
Deck: examples/decks/nano_evo.txt (30 cards, 15 fan-made)
Predicted win rate against the reference opponent: 81%
Key features: n_attack=12, n_item=2, n_evo=9, avg_attack_power=6, avg_defense=2.16667, n_ongoing=0, n_dead=6
Simulated over 200 games: 93% (difference +12%)
```

Both example decks are stronger than most of the random decks the model learned from, and the model under-predicts them by about 10 points. That is a typical limit: a model is least reliable at the edges of its training data.

## Deck lists

One card per line, `<copies> <card id>`, with `#` for comments. Card ids are `Name (pitch)`; the full list is in `data/v2/cards.csv` after notebook 01. A misspelled id gets a "did you mean" suggestion.

```text
# Nano Evo
2 Evo - Phage Arms (1)
3 Gas Up (3)
3 Payload (1)
```

| Deck | Idea |
|---|---|
| [`decks/nano_evo.txt`](decks/nano_evo.txt) | upgrade every equipment slot with the fan-made Nano Evos, then hit hard |
| [`decks/ai_overclock.txt`](decks/ai_overclock.txt) | AI items power up every attack; cheap Go again actions chain into big hits |

Decks of 30 cards match what the model was trained on.
