# 🧮 Features

[`teklo/features.py`](../teklo/features.py) turns a deck list into the model's inputs. **Every feature is known before a game is played**: it only looks at the cards in the deck.

## Reference

| Feature | Meaning |
|---|---|
| `n_attack`, `n_action`, `n_instant`, `n_item`, `n_evo` | how many cards of each kind |
| `n_red`, `n_yellow`, `n_blue` | cards that pitch for 1, 2 and 3 resources |
| `avg_cost` | average cost over the deck |
| `avg_attack_power` | average power of the attack cards |
| `avg_defense` | average defense over the deck |
| `n_big_attack` | attacks with 6 or more power |
| `n_go_again` | cards with Go again |
| `n_boost` | cards with Boost |
| `n_generic` | Generic cards: they never trigger Boost |
| `n_dead` | non-attack cards the simulator gets nothing from: no parsed effect, no Go again, or an Evo that adds no defense |
| `n_ongoing` | items and Evos with at least one effect |
| `ongoing_power_bonus`, `ongoing_draw`, `ongoing_energy`, `ongoing_damage`, `ongoing_life` | what items and Evos give **every turn**, summed over the deck |
| `once_power_bonus`, `once_draw`, `once_energy`, `once_damage`, `once_life` | what the other cards give **once**, summed over the deck |
| `n_custom` | fan-made cards |
| `n_AI`, `n_Nano`, `n_Quantum`, `n_Bio` | fan-made cards per tech path |

A missing count is a real 0. In v1, missing counts were filled with the column average, so a Nano deck was told it had 3 AI cards.

`ongoing_energy` and `once_energy` are always 0 for now: no card text matches the parser's energy patterns. They stay in the list so a better parser (notebook 04) can fill them without changing the model's inputs.

## Why effects are split by timing

The first feature set added each effect up over the whole deck. It scored a cross-validated R² of **0.37**. In this game an item that gives +1 power pays off every turn, while an action that gives +1 power pays off once. Splitting each total by timing, and counting the cards that do nothing (`n_dead`), raised the score to **0.66** with the same data and the same model. Notebook 02 shows the comparison.

## The leakage rule

Ask of every column: **would I have this value before the games are played?**

v1's model used `avg_turns`, `avg_final_life` and `consistency_score`, which are measured from the games. A model fed outcome columns looks excellent and is useless: notebook 02 shows our own outcome columns (`avg_turns`, `avg_life_diff`) push the score from 0.66 to a fake **0.97**. They stay in the dataset for analysis, but [`features.json`](data-format.md) lists only the allowed inputs.

## Using the features

```python
import pandas as pd
import teklo

row = teklo.deck_features(deck)              # dict, keys in teklo.FEATURES order
x = pd.DataFrame([row])[teklo.FEATURES]      # one row, named columns
```
