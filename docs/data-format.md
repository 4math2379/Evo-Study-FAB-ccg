# 🗃️ Data and model files

Notebooks 01 to 03 write these files. Both folders are gitignored: run the notebooks in order to rebuild them (about two minutes in total).

## `data/v2/` (notebooks 01 and 02)

| File | Written by | One row per | Columns |
|---|---|---|---|
| `cards.csv` | 01 | usable card | `id`, `name`, `kind`, `cost`, `pitch`, `power`, `defense`, `slot`, `theme`, `custom`, `keywords`, `text`, and the parsed effects `fx_go_again`, `fx_boost`, `fx_power_bonus`, `fx_draw`, `fx_energy`, `fx_damage`, `fx_life` |
| `opponent.csv` | 01 | card in the reference opponent | `card_id`, `copies` |
| `deck_cards.csv` | 01 | card in a deck | `deck_id`, `card_id`, `copies` |
| `results.csv` | 01 | deck | `deck_id`, `games`, `wins`, `draws`, `win_rate`, `avg_turns`, `avg_life_diff` |
| `teklo_decks.csv` | 02 | deck | `deck_id`, every [feature](features.md), `win_rate`, `games`, `wins`, `draws`, `avg_turns`, `avg_life_diff`, `split` (`train` or `test`) |
| `features.json` | 02 | | the ordered list of columns a model may use |

- `win_rate` = (wins + 0.5 × draws) / games, against the reference opponent, 50 games per deck.
- `avg_turns` and `avg_life_diff` are measured from the games. They are **not** model inputs (see [the leakage rule](features.md#the-leakage-rule)).
- Card ids are `Name (pitch)`, for example `Zipper Hit (3)`, because most cards exist in red, yellow and blue.
- The test split (154 of 800 decks) is frozen in notebook 02 and only used once, at the end of notebook 03.

## `models/v2/` (notebook 03)

| File | Content |
|---|---|
| `model.joblib` | the trained scikit-learn model (gradient boosting) |
| `model_info.json` | model name, target, ordered `features`, metrics, data sizes, scikit-learn version |

Current metrics:

| Metric | Value |
|---|---|
| Cross-validated R² (train, 5 folds) | 0.67 ± 0.02 |
| Test R² (154 unseen decks) | 0.69 |
| Test MAE | 0.15 (15 win-rate points) |
| Best R² possible with 50 games per deck | 0.98 |

## Loading the model

```python
import json
import joblib
import pandas as pd
import teklo

model = joblib.load("models/v2/model.joblib")
features = json.loads(open("models/v2/model_info.json").read())["features"]

x = pd.DataFrame([teklo.deck_features(deck)])[features]   # named columns, in order
print(model.predict(x)[0])                                 # predicted win rate, 0 to 1
```

Pass a table with named columns, not a bare list of numbers. v1's model card showed a list of 19 numbers while the model expected 17, which is why its Quick Start crashed.
