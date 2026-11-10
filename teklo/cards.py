"""Turn the card CSVs into small, typed records the simulator can use.

Two sources are combined:

* ``notebooks/card.csv``: the official Flesh and Blood card database (tab-separated).
* ``custom_cards.csv``: the fan-made Teklovossen cards from this project.

Only cards a Teklovossen deck could play from hand are kept: attacks, non-attack actions,
instants, items and Evo equipment. Heroes, weapons, plain equipment, reactions, allies and
tokens are left out to keep the simulator small.

The rules text is read by a deliberately simple keyword parser (``parse_effects``). It only
understands a handful of patterns, which is the point: notebook 04 compares it with an LLM
that reads the same text.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

SLOTS = ("head", "chest", "arms", "legs")
CUSTOM_THEMES = ("AI", "Nano", "Quantum", "Bio")
KINDS = ("attack", "action", "instant", "item", "evo")

_NUMBER_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3}


@dataclass(frozen=True)
class Effects:
    """What a card does, reduced to a few numbers the simulator understands.

    For items and Evo equipment the effect repeats at the start of every turn.
    For actions and instants it happens once, when the card is played.
    For attacks, draw/energy/damage/life happen only if the attack hits.
    """

    go_again: bool = False
    boost: bool = False
    power_bonus: int = 0  # added to your next attack
    draw: int = 0  # cards drawn
    energy: int = 0  # resource points gained (Teklo Energy)
    damage: int = 0  # direct damage to the opponent
    life: int = 0  # life gained

    def magnitude(self) -> int:
        """Rough size of the effect, used by the simulated players to rank cards."""
        return self.power_bonus + self.draw + self.energy + self.damage + self.life


@dataclass(frozen=True)
class Card:
    id: str  # unique: "Name (pitch)", because most cards exist in red, yellow and blue
    name: str
    kind: str  # one of KINDS
    cost: int
    pitch: int
    power: int
    defense: int
    slot: str | None  # head, chest, arms, legs or weapon (Evo cards only)
    theme: str  # AI, Nano, Quantum, Bio, Mechanologist or Generic
    custom: bool  # True for the fan-made cards
    keywords: tuple[str, ...] = ()
    text: str = ""
    effects: Effects = field(default_factory=Effects)

    def to_row(self) -> dict:
        row = asdict(self)
        row.pop("effects")
        row["keywords"] = ", ".join(self.keywords)
        row.update({f"fx_{k}": v for k, v in asdict(self.effects).items()})
        return row


# ---------------------------------------------------------------------------
# Rules text -> Effects
# ---------------------------------------------------------------------------

def _first_int(pattern: str, text: str, cap: int) -> int:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return 0
    raw = m.group(1).lower()
    value = _NUMBER_WORDS.get(raw, int(raw) if raw.isdigit() else 0)
    return min(value, cap)


def parse_effects(text: str, keywords: tuple[str, ...], kind: str) -> Effects:
    """A small keyword parser for Flesh and Blood rules text.

    It recognises: Go again, Boost, "+N{p}" power bonuses, "draw a card", "gain N{r}",
    "deal N damage" and "gain N{h}". Anything else is ignored.
    """
    t = (text or "").replace("**", "")
    kw = {k.lower() for k in keywords}
    return Effects(
        go_again="go again" in kw,
        boost="boost" in kw,
        # An attack's own "+N{p}" is usually conditional, so only non-attacks grant a bonus.
        power_bonus=0 if kind == "attack" else _first_int(r"\+(\d+)\s*(?:\{p\}|attack|power)", t, 3),
        draw=_first_int(r"draw (a|an|one|two|three|\d+) cards?", t, 2),
        energy=_first_int(r"gain (\d+)\s*\{r\}", t, 2) or _first_int(r"gain (a|an|one|two|\d+) teklo energy", t, 2),
        damage=_first_int(r"deal (\d+) (?:arcane )?damage", t, 3),
        life=_first_int(r"gain (\d+)\s*\{h\}", t, 3),
    )


# ---------------------------------------------------------------------------
# CSV row -> Card
# ---------------------------------------------------------------------------

def _to_int(value, default: int = 0) -> int | None:
    if pd.isna(value):
        return default
    s = str(value).strip()
    if s.lstrip("-").isdigit():
        return int(s)
    try:
        return int(float(s))
    except ValueError:
        return None  # "X", "*", ... : not something the simulator can handle


def _kind_and_slot(types: set[str], keywords: tuple[str, ...]) -> tuple[str | None, str | None]:
    is_evo = "Evo" in types or "Evo" in keywords
    if is_evo and "Equipment" in types:
        slot = next((s for s in SLOTS if s.capitalize() in types), None)
        return ("evo", slot) if slot else (None, None)
    if is_evo and "Weapon" in types:
        return "evo", "weapon"
    if types & {"Hero", "Demi-Hero", "Weapon", "Equipment", "Token", "Ally", "Reaction"}:
        return None, None
    if any("Reaction" in t for t in types):
        return None, None
    if "Item" in types:
        return "item", None
    if "Attack" in types:
        return "attack", None
    if "Instant" in types:
        return "instant", None
    if "Action" in types:
        return "action", None
    return None, None


def _theme(types: set[str]) -> str:
    for theme in CUSTOM_THEMES:
        if theme in types:
            return theme
    if "Mechanologist" in types:
        return "Mechanologist"
    if "Generic" in types:
        return "Generic"
    return "Other"  # cards of other classes (Warrior, Wizard, ...): not used here


def card_from_row(row: dict, custom: bool) -> Card | None:
    """Convert one CSV row into a Card, or None if the simulator can't use it."""
    types = {t.strip() for t in str(row.get("Types", "")).split(",") if t.strip()}
    raw_kw = row.get("Card Keywords")
    keywords = tuple(k.strip() for k in str(raw_kw).split(",") if k.strip()) if pd.notna(raw_kw) else ()
    kind, slot = _kind_and_slot(types, keywords)
    if kind is None:
        return None
    cost = _to_int(row.get("Cost"))
    pitch = _to_int(row.get("Pitch"))
    power = _to_int(row.get("Power"))
    defense = _to_int(row.get("Defense"))
    if None in (cost, pitch, power, defense):
        return None
    name = str(row["Name"]).strip()
    text = str(row.get("Functional Text")) if pd.notna(row.get("Functional Text")) else ""
    return Card(
        id=f"{name} ({pitch})" if pitch else name,
        name=name,
        kind=kind,
        cost=cost,
        pitch=pitch,
        power=power,
        defense=defense,
        slot=slot,
        theme=_theme(types),
        custom=custom,
        keywords=keywords,
        text=text,
        effects=parse_effects(text, keywords, kind),
    )


def load_cards(fab_csv: str | Path, custom_csv: str | Path) -> list[Card]:
    """Load both CSVs and return every usable card once.

    Custom cards win over official ones with the same id.
    """
    cards: dict[str, Card] = {}
    for path, custom in ((fab_csv, False), (custom_csv, True)):
        df = pd.read_csv(path, sep="\t", encoding="utf-8")
        for row in df.to_dict("records"):
            card = card_from_row(row, custom)
            if card is None:
                continue
            if card.theme != "Other":
                cards[card.id] = card
    return list(cards.values())


def teklo_pool(cards: list[Card]) -> list[Card]:
    """Cards a Teklovossen deck may use: Mechanologist, fan-made and Generic cards."""
    return [c for c in cards if c.theme != "Generic" or c.kind != "evo"]


def generic_pool(cards: list[Card]) -> list[Card]:
    """Cards for the reference opponent: Generic cards only, no Evo equipment."""
    return [c for c in cards if c.theme == "Generic" and c.kind != "evo"]


def cards_frame(cards: list[Card]) -> pd.DataFrame:
    return pd.DataFrame([c.to_row() for c in cards])
