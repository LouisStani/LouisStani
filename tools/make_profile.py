"""Generate the profile README images: banner and projects, then trophies.

Style: every part is a sticker drawn like the avatar (thick ink outline, cream
fill, hard shadow); trophies are ink-drawn cups standing on a shelf. Parts are separated by a
hand-drawn wave and a tilted label.
"""

import json
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fontTools.ttLib import TTFont

from make_banner import ACCENT, BG, FONT_BOLD, FONT_REGULAR, INK, MUTED, TERM_BAR, build, text_path

WIDTH = 1200
PAPER = "#F6E7D4"
PAPER_TEXT = "#3A2412"
PAPER_MUTED = "#8A5A30"
STROKE = 5
SHADOW = 10
MARGIN = 48
PROJECT_HEIGHT = 214
SHELF_TOP = 250
# Transparent band above the trophy panel: GitHub stacks the two images with a
# few pixels between them anyway, so the gap is made wide enough to look meant.
PANEL_GAP = 18
PLANK = 24
STATS = Path(__file__).parent / "stats.json"
# Cup colour, letter colour and size for each rank: gold, silver, bronze, not earned yet.
GOLD = (ACCENT, INK, 1.0)
SILVER = (PAPER, INK, 0.9)
BRONZE = (PAPER_MUTED, PAPER, 0.82)
RANK_LOOK = {"SECRET": GOLD, "SSS": GOLD, "SS": GOLD, "S": GOLD, "AAA": SILVER, "AA": SILVER, "A": SILVER,
             "B": BRONZE, "C": BRONZE, "?": BRONZE}
LETTER_SIZE = {1: 48, 2: 38, 3: 30}

PROJECTS = [
    {
        "name": "kindric",
        "repo": "kindric",
        "logo": Path(__file__).parent / "assets/kindric.svg",
        "lines": [
            "several claude code sessions, across several accounts, side by side.",
            "split panes, tabs, and sessions that talk to each other.",
        ],
        "footer": "rust · linux, macos, windows · gpl-3.0 · built with claude code",
    },
]


class Fonts:
    def __init__(self) -> None:
        self.bold = TTFont(FONT_BOLD)
        self.regular = TTFont(FONT_REGULAR)


def text(font: TTFont, value: str, x: float, y: float, size: float, fill: str) -> str:
    return f'<path d="{text_path(font, value, x, y, size)[0]}" fill="{fill}"/>'


def separator(fonts: Fonts, label: str, y: float) -> str:
    """Hand-drawn wave across the page with a tilted label on it."""
    waves = (WIDTH - 2 * MARGIN) // 50
    wave = f"M{MARGIN} {y} " + " ".join(f"q 25 {-14 if i % 2 else 14} 50 0" for i in range(waves))
    width = len(label) * 32 * 0.6 + 52
    x = MARGIN + 60
    return (f'<path d="{wave}" fill="none" stroke="{INK}" stroke-width="{STROKE}" stroke-linecap="round"/>'
            f'<g transform="rotate(-4 {x + width / 2} {y})">'
            f'<rect x="{x}" y="{y - 31}" width="{width:.1f}" height="62" rx="10" fill="{ACCENT}" stroke="{INK}" stroke-width="{STROKE}"/>'
            f'{text(fonts.bold, label, x + 26, y + 11, 32, INK)}</g>')


def state_pill(fonts: Fonts, state: str, right: float, baseline: float) -> str:
    width = len(state) * 22 * 0.6 + 36
    x = right - width
    if state == "live" or state.startswith("v"):
        return (f'<rect x="{x:.1f}" y="{baseline - 28}" width="{width:.1f}" height="38" rx="19" fill="{ACCENT}" stroke="{INK}" stroke-width="3"/>'
                + text(fonts.regular, state, x + 18, baseline, 22, INK))
    return (f'<rect x="{x:.1f}" y="{baseline - 28}" width="{width:.1f}" height="38" rx="19" fill="none" stroke="{PAPER_MUTED}" stroke-width="2.5"/>'
            + text(fonts.regular, state, x + 18, baseline, 22, PAPER_MUTED))


def centered(font: TTFont, value: str, cx: float, y: float, size: float, fill: str) -> str:
    width = text_path(font, value, 0, 0, size)[1]
    return text(font, value, cx - width / 2, y, size, fill)


def sticker(y: float, height: float, body: str) -> str:
    """Cream sticker with an ink outline and a hard shadow."""
    x, width = MARGIN, WIDTH - 2 * MARGIN - SHADOW
    return (f'<rect x="{x + SHADOW}" y="{y + SHADOW}" width="{width}" height="{height}" rx="22" fill="{INK}"/>'
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="22" fill="{PAPER}" stroke="{INK}" stroke-width="{STROKE}"/>'
            f'<g transform="translate({x} {y})">{body}</g>')


def cup(fill: str, shadow: bool) -> str:
    """Trophy cup whose foot rests on y = 0; `shadow` draws its flat silhouette, without handles."""
    stroke = "none" if shadow else INK
    parts = [
        f'<path d="M-56 -140 H56 V-112 Q56 -56 0 -44 Q-56 -56 -56 -112 Z" fill="{fill}" stroke="{stroke}" stroke-width="{STROKE}" stroke-linejoin="round"/>',
        f'<rect x="-62" y="-152" width="124" height="16" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="{STROKE}"/>',
        f'<path d="M-9 -46 H9 L13 -18 H-13 Z" fill="{fill}" stroke="{stroke}" stroke-width="{STROKE}" stroke-linejoin="round"/>',
        f'<rect x="-40" y="-20" width="80" height="20" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="{STROKE}"/>',
    ]
    if not shadow:
        parts.insert(0, f'<path d="M-54 -126 C-98 -126 -98 -72 -40 -66 M54 -126 C98 -126 98 -72 40 -66" fill="none" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>')
        parts.insert(2, '<path d="M-38 -126 Q-41 -88 -22 -64" fill="none" stroke="#FFFFFF" stroke-opacity="0.55" stroke-width="7" stroke-linecap="round"/>')
    return "".join(parts)


def sparkle(x: float, y: float, size: float) -> str:
    k = size * 0.22
    d = (f"M{x} {y - size} Q{x + k} {y - k} {x + size} {y} Q{x + k} {y + k} {x} {y + size} "
         f"Q{x - k} {y + k} {x - size} {y} Q{x - k} {y - k} {x} {y - size} Z")
    return f'<path d="{d}" fill="{ACCENT}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'


def plaque(fonts: Fonts, name: str) -> str:
    """Dark name plate under a cup, sized to its text, bottom on y = 0."""
    width = text_path(fonts.bold, name, 0, 0, 17)[1] + 30
    return (f'<rect x="{-width / 2 + 6}" y="-32" width="{width}" height="38" rx="7" fill="{INK}"/>'
            f'<rect x="{-width / 2}" y="-38" width="{width}" height="38" rx="7" fill="{INK}" stroke="{TERM_BAR}" stroke-width="2"/>'
            + centered(fonts.bold, name, 0, -13, 17, PAPER))


def trophy(fonts: Fonts, rank: str, name: str, cx: float, shelf: float) -> str:
    fill, letter, scale = RANK_LOOK[rank]
    shine = sparkle(-96, -166, 18) + sparkle(88, -190, 13) + sparkle(104, -116, 10) if RANK_LOOK[rank] == GOLD else ""
    return (f'<g transform="translate({cx} {shelf})">{plaque(fonts, name)}'
            f'<g transform="translate(0 -38) scale({scale})">'
            f'<g transform="translate(7 7)">{cup(INK, True)}</g>{cup(fill, False)}{shine}'
            + centered(fonts.bold, rank, 0, -76, LETTER_SIZE.get(len(rank), 26), letter)
            + '</g></g>')


def trophies(fonts: Fonts, y: float, earned: list[dict]) -> str:
    """Trophy shelf: cups on a dark plank, each title written under its cup."""
    step = (WIDTH - 2 * MARGIN) / len(earned)
    shelf = y + SHELF_TOP
    left, right = MARGIN, WIDTH - MARGIN - SHADOW
    plank = (f'<rect x="{left + SHADOW}" y="{shelf + SHADOW}" width="{right - left}" height="{PLANK}" rx="6" fill="{INK}"/>'
             f'<rect x="{left}" y="{shelf}" width="{right - left}" height="{PLANK}" rx="6" fill="{TERM_BAR}" stroke="{INK}" stroke-width="{STROKE}"/>')
    cups = "".join(trophy(fonts, t["rank"], t["name"], MARGIN + step * (i + 0.5), shelf) for i, t in enumerate(earned))
    titles = "".join(centered(fonts.regular, t["title"], MARGIN + step * (i + 0.5), shelf + PLANK + 42, 18, MUTED)
                     for i, t in enumerate(earned))
    return plank + cups + titles


def logo(path: Path, x: float, y: float, size: float) -> str:
    """Embed a 512x512 SVG icon, outer <svg> tag replaced to place and size it."""
    inner = path.read_text().split(">", 1)[1].rsplit("</svg>", 1)[0]
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 512 512">{inner}</svg>'


def project_body(fonts: Fonts, project: dict) -> str:
    inner = WIDTH - 2 * MARGIN - SHADOW
    left = 196
    lines = "".join(text(fonts.regular, line, left, 114 + i * 32, 20, PAPER_TEXT) for i, line in enumerate(project["lines"]))
    return (logo(project["logo"], 36, 40, 134)
            + text(fonts.bold, project["name"], left, 72, 40, INK)
            + state_pill(fonts, project["state"], inner - 36, 66)
            + lines + text(fonts.regular, project["footer"], left, 182, 18, PAPER_MUTED))


def panel(parts: list[str], height: float, label: str, top_gap: float = 0) -> str:
    """Brown rounded panel with an ink frame; `top_gap` leaves a transparent band above it."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height + top_gap}" width="{WIDTH}" height="{height + top_gap}" role="img" aria-label="{escape(label)}">'
            f'<g transform="translate(0 {top_gap})">'
            f'<rect x="{STROKE / 2}" y="{STROKE / 2}" width="{WIDTH - STROKE}" height="{height - STROKE}" rx="28" fill="{BG}"/>'
            f'<clipPath id="page"><rect width="{WIDTH}" height="{height}" rx="28"/></clipPath>'
            f'<g clip-path="url(#page)">{"".join(parts)}</g>'
            f'<rect x="{STROKE / 2}" y="{STROKE / 2}" width="{WIDTH - STROKE}" height="{height - STROKE}" rx="28" fill="none" stroke="{INK}" stroke-width="{STROKE + 1}"/>'
            '</g></svg>\n')


def build_profile(stats: dict) -> str:
    """Top panel: banner and projects."""
    fonts = Fonts()
    projects = [{**p, "state": stats["releases"].get(p["repo"], "live")} for p in PROJECTS]
    banner = build().replace("<svg ", '<svg x="0" y="0" ', 1)
    # Straight ink rule under the banner: the avatar's cropped sleeves rest on it.
    parts = [banner, f'<line x1="0" y1="360" x2="{WIDTH}" y2="360" stroke="{INK}" stroke-width="{STROKE}"/>']
    y = 360 + 70
    parts.append(separator(fonts, "projects", y))
    y += 70
    for project in projects:
        parts.append(sticker(y, PROJECT_HEIGHT, project_body(fonts, project)))
        y += PROJECT_HEIGHT + 44
    label = ("lystriq: i build clean tools, games and apps that work and that people use. projects: "
             + " ".join(f"{p['name']} ({p['state']}): {' '.join(p['lines'])}" for p in projects))
    return panel(parts, y + 6, label)


def build_trophies(stats: dict) -> str:
    """Bottom panel: the trophy shelf, a separate image so it can link elsewhere."""
    fonts = Fonts()
    parts = [separator(fonts, "trophies", 70), trophies(fonts, 146, stats["trophies"])]
    label = "trophies: " + ", ".join(f"{t['name']} {t['rank']} ({t['title']})" for t in stats["trophies"]) + "."
    return panel(parts, 146 + SHELF_TOP + PLANK + 80, label, top_gap=PANEL_GAP)


def main() -> None:
    """Usage: make_profile.py <profile.svg> <trophies.svg> [stats.json]"""
    if len(sys.argv) < 3:
        raise SystemExit(main.__doc__)
    stats = json.loads((Path(sys.argv[3]) if len(sys.argv) > 3 else STATS).read_text())
    Path(sys.argv[1]).write_text(build_profile(stats))
    Path(sys.argv[2]).write_text(build_trophies(stats))


if __name__ == "__main__":
    main()
