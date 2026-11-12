"""Draw dream cards: a card frame in the style of the project's concept art, filled with AI art.

Themes listed in ``FRAMES`` use a painted frame: one of the ChatGPT concept cards in ``evos/``
with its own text, numbers and picture wiped out, saved in ``evos/frames/``. The other themes
use a frame drawn here in the same layout: cost in the top-left circle, name banner, pitch gem
top-right, a large art window, a rules box, power bottom-left and defense bottom-right.

All lettering is drawn here with Pillow. Image models garble text, so the model is only
asked for the illustration and the card text is always spelled correctly.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat

from .cards import Card

WIDTH, HEIGHT = 1024, 1536
ART_BOX = (68, 200, 956, 870)  # left, top, right, bottom
TEXT_BOX = (68, 890, 956, 1360)

CREAM = "#efe9dc"
INK = "#1d1b18"
MUTED = "#5b554c"

# Frame colour per theme (the Quantum blue matches the concept art).
THEME_COLORS = {
    "Quantum": "#4aa8e0",
    "AI": "#3cc3c8",
    "Nano": "#a7b4c2",
    "Bio": "#5fae5b",
    "Mechanologist": "#c98a3a",
    "Generic": "#9a9a9a",
}
# Flesh and Blood pitch colours: 1 red, 2 yellow, 3 blue.
PITCH_COLORS = {1: "#d0402f", 2: "#e7b52c", 3: "#2a78d6"}

# Painted frames. Each entry names the blank frame in evos/frames/ and where things sit on it,
# in pixels: (left, top, right, bottom) boxes and (x, y) circle centres.
#   art        box the picture is fitted to; a transparent frame shows it only through its window
#   gem        pitch gem (x, y, radius), recoloured to the card's pitch unless it already has it
#   gem_pitch  the pitch the gem's own colour stands for (None: always recolour)
#   cost_on_gem  the cost is written on the gem instead of in a circle
#   header     a ribbon for the theme name; otherwise the theme goes under the frame at label_y
# Themes without an entry use the frame drawn in render_card.
FRAME_DIR = Path(__file__).resolve().parent.parent / "evos" / "frames"
FRAMES = {
    "Quantum": {
        "file": "quantum.png",  # from "evos/Quantuum Evo/evo_study. 2025, 23_17_58.png"
        "art": (73, 186, 951, 905),
        "name": (185, 92, 825, 166),
        "text": (90, 930, 940, 1358),
        "type": (212, 1400, 828, 1452),
        "cost": (108, 128),
        "power": (100, 1420),
        "defense": (928, 1422),
        "gem": (906, 124, 50),
        "gem_pitch": 3,
        "label_y": 1484,
        "credit_y": 1520,
    },
    "Bio": {
        "file": "bio.png",  # from "evos/Biomancy evo/evo_study. 2025, 01_03_46.png"
        "art": (84, 179, 941, 937),
        "name": (200, 86, 820, 164),
        "text": (99, 955, 925, 1291),
        "type": (222, 1310, 808, 1369),
        "cost": (118, 126),
        "power": (110, 1345),
        "defense": (912, 1345),
        "gem": (905, 125, 46),
        "gem_pitch": None,
        "label_y": 1418,
        "credit_y": 1454,
    },
    "Nano": {
        "file": "nano.png",  # from "evos/Nano Evos/evo_study. 2025, 21_10_06.png"
        "art": (47, 169, 963, 961),
        "name": (175, 62, 845, 150),
        "text": (70, 981, 954, 1344),
        "type": (200, 1372, 840, 1432),
        "cost": (930, 99),
        "cost_on_gem": True,
        "power": (82, 1405),
        "defense": (940, 1410),
        "gem": (930, 99, 59),
        "gem_pitch": 1,
        "label_y": 1490,
        "credit_y": 1522,
    },
    "AI": {
        "file": "ai.png",  # from "evos/Ai-Evo/evo_study. 2025, 03_11_56.png"
        "art": (94, 254, 931, 870),
        "header": (250, 108, 760, 158),
        "name": (150, 172, 880, 240),
        "text": (100, 885, 923, 1296),
        "type": (232, 1316, 800, 1370),
        "cost": (888, 148),
        "cost_on_gem": True,
        "power": (118, 1345),
        "defense": (895, 1345),
        "gem": (888, 148, 60),
        "gem_pitch": None,
        "credit_y": 1428,
    },
}

# A visual style per theme, added to every art prompt so a set of cards looks consistent.
THEME_STYLE = {
    "Quantum": "deep blue nebula, glowing blue quantum crystals, probability arcs of light, textured energy",
    "AI": "cyan circuitry, holographic interfaces, neural light patterns",
    "Nano": "silver nanite swarms, fine metallic particles, clean workshop light",
    "Bio": "living bio-mechanical tissue, green bioluminescence, organic metal",
    "Mechanologist": "brass and steel machinery, sparks, forge light",
    "Generic": "dramatic fantasy lighting",
}

# ---------------------------------------------------------------------------
# Fonts: Palatino on Windows (closest to the concept art), DejaVu Serif everywhere else
# ---------------------------------------------------------------------------

_FONT_FILES = {
    "regular": ["pala.ttf", "Palatino.ttc", "DejaVuSerif.ttf"],
    "bold": ["palab.ttf", "Palatino.ttc", "DejaVuSerif-Bold.ttf"],
    "italic": ["palai.ttf", "Palatino.ttc", "DejaVuSerif-Italic.ttf"],
}


def _font_dirs() -> list[Path]:
    dirs = [Path("C:/Windows/Fonts"), Path("/System/Library/Fonts"), Path("/usr/share/fonts/truetype/dejavu")]
    try:
        import matplotlib

        dirs.append(Path(matplotlib.get_data_path()) / "fonts" / "ttf")
    except ImportError:
        pass
    return dirs


def font(style: str, size: int) -> ImageFont.FreeTypeFont:
    for name in _FONT_FILES[style]:
        for d in _font_dirs():
            if (d / name).exists():
                return ImageFont.truetype(str(d / name), size)
    return ImageFont.load_default(size)


# ---------------------------------------------------------------------------
# Card text
# ---------------------------------------------------------------------------

def type_line(card: Card, with_theme: bool = True) -> str:
    """The line under the art, e.g. 'Mechanologist Action — Attack — Quantum'."""
    if card.kind == "evo":
        line, theme = f"Mechanologist Equipment — {(card.slot or '').title()}", f"Evo {card.theme}"
    else:
        kind = {
            "attack": "Action — Attack",
            "action": "Action",
            "instant": "Instant",
            "item": "Action — Item",
        }[card.kind]
        line, theme = f"Mechanologist {kind}", card.theme
    return f"{line} — {theme}" if with_theme else line


def stats_line(card: Card) -> str:
    parts = [f"Pitch {card.pitch}", f"Cost {card.cost}"]
    if card.kind == "attack":
        parts.append(f"Power {card.power}")
    if card.defense:
        parts.append(f"Defense {card.defense}")
    return "   ".join(parts)


def pretty_text(text: str) -> str:
    """Turn the rules-text symbols the parser reads ({p}, {r}, {h}) into words for the card face."""
    return text.replace("{p}", " power").replace("{r}", " resource").replace("{h}", " life").replace("**", "")


def slug(card: Card) -> str:
    return re.sub(r"[^a-z0-9]+", "_", card.id.lower()).strip("_")


def _wrap(draw: ImageDraw.ImageDraw, text: str, fnt, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            trial = f"{line} {word}".strip()
            if draw.textlength(trial, font=fnt) <= width:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def _cover(img: Image.Image, size: tuple[int, int], zoom: float = 0.08) -> Image.Image:
    """Resize and centre-crop ``img`` so it fills ``size`` without stretching.

    ``zoom`` trims that share of each edge first: image models like to paint a fake artist
    signature in a corner, and the trim keeps it off the card.
    """
    dx, dy = round(img.width * zoom), round(img.height * zoom)
    img = img.crop((dx, dy, img.width - dx, img.height - dy))
    w, h = size
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def _placeholder_art(size: tuple[int, int], color: str) -> Image.Image:
    """A soft glow used before any art is generated, so the template can be previewed for free."""
    w, h = size
    img = Image.new("RGB", size, "#0d1626")
    glow = Image.new("RGB", size, color)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse((w * 0.2, h * 0.15, w * 0.8, h * 0.85), fill=170)
    img.paste(glow, mask=mask.filter(ImageFilter.GaussianBlur(90)))
    return img


def _circle(draw, center, radius, fill, ring, text=None, fnt=None, text_fill=INK):
    x, y = center
    draw.ellipse((x - radius - 8, y - radius - 8, x + radius + 8, y + radius + 8), fill=ring)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill, outline="#ffffff", width=3)
    if text is not None:
        draw.text((x, y + 2), str(text), font=fnt, fill=text_fill, anchor="mm")


def _tint_gem(img: Image.Image, gem: tuple[int, int, int], pitch: int, gem_pitch: int | None) -> None:
    """Recolour the frame's gem to the card's pitch colour, unless the gem already shows it."""
    if pitch == gem_pitch or pitch not in PITCH_COLORS:
        return
    x, y, r = gem
    crop = img.crop((x - r, y - r, x + r, y + r))
    gray = ImageOps.grayscale(crop)
    mask = Image.new("L", crop.size, 0)
    ImageDraw.Draw(mask).ellipse((2, 2, 2 * r - 2, 2 * r - 2), fill=255)
    # The gem's typical tone becomes the pitch colour, so dark and light gems both tint well.
    middle = min(max(int(ImageStat.Stat(gray, mask).median[0]), 20), 235)
    tinted = ImageOps.colorize(gray, black="#140404", white="#fff4dc", mid=PITCH_COLORS[pitch], midpoint=middle)
    img.paste(tinted, (x - r, y - r), mask.filter(ImageFilter.GaussianBlur(2)))


def _render_on_frame(card: Card, art: Image.Image | None, frame: dict, flavour: str,
                     credit: str) -> Image.Image:
    """Draw ``card`` on a painted frame from ``FRAMES``."""
    frame_img = Image.open(FRAME_DIR / frame["file"])
    img = frame_img.convert("RGB")
    _tint_gem(img, frame["gem"], card.pitch, frame["gem_pitch"])

    # Art window: the frame's transparent pixels, or the whole art box if the frame has none
    left, top, right, bottom = frame["art"]
    box_size = (right - left, bottom - top)
    color = THEME_COLORS.get(card.theme, THEME_COLORS["Generic"])
    art_img = _cover(art.convert("RGB"), box_size) if art is not None else _placeholder_art(box_size, color)
    window = ImageOps.invert(frame_img.getchannel("A")).crop(frame["art"]) if frame_img.mode == "RGBA" else None
    img.paste(art_img, (left, top), window)
    d = ImageDraw.Draw(img)

    # Name in the banner
    l, t, r, b = frame["name"]
    name_font = font("regular", 56)
    while d.textlength(card.name, font=name_font) > r - l - 20 and name_font.size > 28:
        name_font = font("regular", name_font.size - 2)
    d.text(((l + r) / 2, (t + b) / 2 + 2), card.name, font=name_font, fill=INK, anchor="mm")

    # Cost, power and defense in the circles
    stats = {"cost": card.cost, "power": card.power if card.kind == "attack" else None,
             "defense": card.defense or None}
    for key, value in stats.items():
        if value is None:
            continue
        x, y = frame[key]
        if key == "cost" and frame.get("cost_on_gem"):  # light figure with a dark edge on the gem
            d.text((x, y + 2), str(value), font=font("bold", 64), fill=CREAM, anchor="mm",
                   stroke_width=3, stroke_fill=INK)
        else:
            d.text((x, y + 2), str(value), font=font("regular", 68), fill=INK, anchor="mm")

    # Type line in the bottom banner
    l, t, r, b = frame["type"]
    kind_line = type_line(card, with_theme=False)
    type_font = font("regular", 30)
    while d.textlength(kind_line, font=type_font) > r - l - 20 and type_font.size > 18:
        type_font = font("regular", type_font.size - 2)
    d.text(((l + r) / 2, (t + b) / 2 + 1), kind_line, font=type_font, fill=INK, anchor="mm")

    # Keywords, rules text and flavour, shrunk until they fit the rules box
    l, t, r, b = frame["text"]
    width, size = r - l - 40, 36
    while True:
        rules_font, bold_font, flav_font = font("regular", size), font("bold", size), font("italic", size - 2)
        rules = _wrap(d, pretty_text(card.text), rules_font, width)
        flav = _wrap(d, flavour, flav_font, width) if flavour else []
        lines = len(rules) + len(flav) + (1 if card.keywords else 0)
        if t + 18 + lines * (size + 12) + (20 if flav else 0) <= b - 10 or size <= 22:
            break
        size -= 2
    y = t + 18
    if card.keywords:
        d.text((l + 20, y), ", ".join(card.keywords), font=bold_font, fill=INK)
        y += size + 12
    for line in rules:
        d.text((l + 20, y), line, font=rules_font, fill=INK)
        y += size + 12
    if flav:
        y += 20
        for line in flav:
            d.text(((l + r) / 2, y), line, font=flav_font, fill=MUTED, anchor="ma")
            y += size + 12

    # Theme in the header ribbon or under the frame, then the credit line
    theme = f"Evo {card.theme}" if card.kind == "evo" else card.theme
    if "header" in frame:
        l, t, r, b = frame["header"]
        d.text(((l + r) / 2, (t + b) / 2), theme.upper(), font=font("bold", 34), fill="#e6dcff", anchor="mm")
    else:
        d.text((WIDTH / 2, frame["label_y"]), theme, font=font("regular", 30), fill="#e8e8e8", anchor="mm")
    if credit:
        d.text((WIDTH / 2, frame["credit_y"]), credit, font=font("regular", 18), fill="#9a9a9a", anchor="mm")
    return img


def render_card(card: Card, art: Image.Image | None = None, flavour: str = "",
                credit: str = "") -> Image.Image:
    """Draw ``card`` as a 1024 x 1536 image. Without ``art`` a placeholder fills the art window.

    Themes in ``FRAMES`` get their painted frame; the others get the frame drawn below.
    """
    if card.theme in FRAMES:
        return _render_on_frame(card, art, FRAMES[card.theme], flavour, credit)
    color = THEME_COLORS.get(card.theme, THEME_COLORS["Generic"])
    img = Image.new("RGB", (WIDTH, HEIGHT), "#000000")
    d = ImageDraw.Draw(img)

    # Frame
    d.rounded_rectangle((28, 28, WIDTH - 28, HEIGHT - 60), radius=36, fill=color)
    d.rounded_rectangle((44, 44, WIDTH - 44, HEIGHT - 76), radius=28, outline="#ffffff", width=3)

    # Art window
    box_size = (ART_BOX[2] - ART_BOX[0], ART_BOX[3] - ART_BOX[1])
    art_img = _cover(art.convert("RGB"), box_size) if art is not None else _placeholder_art(box_size, color)
    img.paste(art_img, ART_BOX[:2])
    d.rectangle(ART_BOX, outline="#ffffff", width=4)

    # Name banner, cost circle and pitch gem
    d.rounded_rectangle((130, 66, WIDTH - 130, 176), radius=18, fill=CREAM, outline="#ffffff", width=3)
    name_font = font("regular", 58)
    while d.textlength(card.name, font=name_font) > WIDTH - 330 and name_font.size > 30:
        name_font = font("regular", name_font.size - 2)
    d.text((WIDTH / 2, 122), card.name, font=name_font, fill=INK, anchor="mm")
    _circle(d, (110, 121), 60, CREAM, color, card.cost, font("regular", 72))
    _circle(d, (WIDTH - 110, 121), 52, PITCH_COLORS.get(card.pitch, "#888888"), color)
    for i in range(card.pitch):  # one dot per pitch point, like a pitch strip
        x = WIDTH - 110 + (i - (card.pitch - 1) / 2) * 24
        d.ellipse((x - 7, 114, x + 7, 128), fill="#ffffff")

    # Rules box
    d.rounded_rectangle(TEXT_BOX, radius=14, fill=CREAM, outline="#ffffff", width=3)
    left, top, right, bottom = TEXT_BOX
    width = right - left - 64
    y = top + 30
    d.text((left + 32, y), type_line(card), font=font("bold", 30), fill=INK)
    y += 48
    d.text((left + 32, y), stats_line(card), font=font("regular", 28), fill=MUTED)
    y += 50
    if card.keywords:
        d.text((left + 32, y), ", ".join(card.keywords), font=font("bold", 32), fill=INK)
        y += 50
    # Shrink the rules text until it fits the box.
    size = 34
    while True:
        rules_font, flav_font = font("regular", size), font("italic", size - 2)
        rules = _wrap(d, pretty_text(card.text), rules_font, width)
        flav = _wrap(d, flavour, flav_font, width) if flavour else []
        needed = (len(rules) + len(flav)) * (size + 10) + (16 if flav else 0)
        if y + needed <= bottom - 24 or size <= 20:
            break
        size -= 2
    for line in rules:
        d.text((left + 32, y), line, font=rules_font, fill=INK)
        y += size + 10
    if flav:
        y += 16
        for line in flav:
            d.text((left + 32, y), line, font=flav_font, fill=MUTED)
            y += size + 10

    # Power and defense
    stat_font = font("regular", 64)
    if card.kind == "attack":
        _circle(d, (110, 1408), 54, CREAM, color, card.power, stat_font)
    if card.defense:
        _circle(d, (WIDTH - 110, 1408), 54, CREAM, color, card.defense, stat_font)
    d.text((WIDTH / 2, 1408), card.theme.upper(), font=font("bold", 30), fill="#ffffff", anchor="mm")

    # Credit line under the frame
    if credit:
        d.text((WIDTH / 2, HEIGHT - 30), credit, font=font("regular", 24), fill="#cfcfcf", anchor="mm")
    return img


# ---------------------------------------------------------------------------
# Art generation (Hugging Face Inference Providers)
# ---------------------------------------------------------------------------

def art_prompt(card: Card, idea: str) -> str:
    style = THEME_STYLE.get(card.theme, THEME_STYLE["Generic"])
    return (
        f"Fantasy trading card illustration, painterly digital art, dramatic lighting. {idea}. "
        f"Style: {style}. Landscape composition, subject centred. "
        "No text, no letters, no numbers, no card frame, no border."
    )


def generate_art(client, card: Card, idea: str, out_dir: Path, model: str, seed: int = 0,
                 overwrite: bool = False) -> Image.Image:
    """Ask ``model`` for the card's illustration, or reuse the saved one.

    The image and a JSON note (model, prompt, seed) are saved in ``out_dir``, so a card is only
    paid for once and the art can always be credited to the model that made it.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    art_path = out_dir / f"{slug(card)}_art.png"
    if art_path.exists() and not overwrite:
        return Image.open(art_path)
    prompt = art_prompt(card, idea)
    image = client.text_to_image(prompt, model=model, width=1024, height=768, seed=seed)
    image.save(art_path)
    note = {"card": card.id, "model": model, "seed": seed, "prompt": prompt}
    (out_dir / f"{slug(card)}_art.json").write_text(json.dumps(note, indent=2), encoding="utf-8")
    return image
