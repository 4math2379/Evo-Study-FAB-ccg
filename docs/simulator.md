# ⚔️ Simulator

[`teklo/engine.py`](../teklo/engine.py) plays a small duel inspired by Flesh and Blood. It is **not a rules engine**: it keeps the parts of the game that make deck building matter and drops the rest, so the whole rule set fits on one screen and stays readable.

## Rules

| Rule | Value |
|---|---|
| Starting life | 20 for each hero |
| Weapon | 3 power, costs 1 resource to attack, once per turn |
| Equipment | head, chest, arms and legs, 1 defense each at the start |
| Hand size | draw up to 4 cards at the end of your own turn |
| Action points | 1 per turn |
| Resources | pitch a card from hand: red gives 1, yellow 2, blue 3. Pitched cards go to the bottom of the deck |
| Teklo Energy | stored resource from card effects, spent before pitching, capped at 5 |
| Go again | the card gives the action point back. Items, Evo equipment and instants always do |
| Boost (Mechanologist) | when attacking with a Boost card, banish the top card of the deck; if it is not a Generic card, the attack gains Go again |
| Items | stay in play and repeat their effect at the start of each of your turns |
| Evo equipment | replaces the piece in its slot (better defense) and repeats its effect every turn. An Evo weapon raises the weapon's power |
| Blocking | equipment first (each block wears a piece down by 1; Blade Break pieces are destroyed), then up to 2 cards from hand |
| End of game | a hero at 0 life loses. After 40 turns, more life wins; equal life is a draw |

Every deck is measured against one fixed **reference opponent**: a Generic deck of efficient attacks (power at least cost + 3) plus a few non-attack actions ([`teklo.reference_opponent`](../teklo/decks.py)). Games alternate who goes first, because going first is an advantage.

## How the simulated players decide

Both players use the same simple rules (`Duel._choose_play` and `Duel._defend`):

1. **Attack turn.** Cards that keep the turn going (Go again, items, Evos, instants) are played first, as long as the best remaining attack is still affordable afterwards. Then the best attack is made: attack cards are ranked by power, bonuses and cost, and the weapon is the fallback.
2. **Defense.** Block with equipment when 2 or more damage would get through, then with hand cards of defense 2 or more when 3 or more would get through, or with anything when the hit would be lethal.

These rules are deliberately naive. A stronger player AI would change which decks win, and the model would learn that instead.

## Sanity checks

Notebook 01 and [`tests/test_teklo.py`](../tests/test_teklo.py) check the simulator against answers known in advance:

| Check | Expected | Result |
|---|---|---|
| A deck against itself | about 50% | 53% over 1,000 games (within luck) |
| The player who goes first | an edge | 63% |
| 30 blue cards and no attacks | close to 0% | 0% |
| Same seed twice | the same game | identical |

## Known limits

- Rules text is read by a small keyword parser ([Cards](cards.md#the-rules-text-parser)). An effect the parser misses does not exist for the simulator.
- An item's effect repeats every turn even when the real card says "once" or "destroy this", so items are probably overrated.
- No reactions, arsenal, hero abilities, allies, tokens or card-specific triggers.
- Speed: about 0.7 ms per game, so 40,000 games take under a minute.

## Playing a game yourself

```bash
python examples/play_one_game.py examples/decks/nano_evo.txt
```

```python
from teklo.engine import play_game

log = []
result = play_game(my_deck, opponent, seed=42, log=log)
print("\n".join(log))
```
