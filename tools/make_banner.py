"""Generate the animated profile banner SVG (text converted to paths)."""

import base64
import io
import re
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageFilter

HERE = Path(__file__).parent
AVATAR = HERE / "assets/avatar-black.png"
FONT_BOLD = HERE / "fonts/JetBrainsMono-Bold.ttf"
FONT_REGULAR = HERE / "fonts/JetBrainsMono-Regular.ttf"

WIDTH, HEIGHT = 1200, 360
BG = "#AA601F"
WHITE = "#FFFFFF"
CREAM = "#F6E7D4"
ACCENT = "#F2B544"
MUTED = "#D9BFA0"
TERM_BAR = "#5C300F"
INK = "#1A0E06"
# The sleeve ends of the round profile picture look cut off in a rectangle: crop above them.
AVATAR_CROP = 920
AVATAR_WIDTH = HEIGHT * 1000 / AVATAR_CROP


def text_path(font: TTFont, text: str, x: float, y: float, size: float) -> tuple[str, float]:
    """Return an SVG path for `text` with its baseline at (x, y), and the end x."""
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    pen = SVGPathPen(glyph_set)
    cursor = x
    for char in text:
        name = cmap[ord(char)]
        glyph = glyph_set[name]
        glyph.draw(TransformPen(pen, (scale, 0, 0, -scale, cursor, y)))
        cursor += glyph.width * scale
    commands = re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group()):.1f}", pen.getCommands())
    return commands, cursor


def png_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode()


def eyelid_base64(x: int, row: int, width: int, height: int) -> str:
    """Average the skin rows below the eye and stretch them upward into a closed lid."""
    with Image.open(AVATAR) as avatar:
        skin = avatar.convert("RGB").crop((x, row, x + width, row + 12))
    line = skin.resize((width, 1), Image.Resampling.BOX).filter(ImageFilter.GaussianBlur(3))
    return png_base64(line.resize((width, height), Image.Resampling.NEAREST))


def avatar_base64(size: int) -> str:
    with Image.open(AVATAR) as avatar:
        return png_base64(avatar.convert("RGB").resize((size, size), Image.Resampling.LANCZOS))


STYLE = """
.cursor { animation: blink 1.1s steps(1) infinite; }
@keyframes blink { 50% { opacity: 0; } }
.breathe { transform-box: view-box; transform-origin: 500px 920px;
  animation: breathe 4.6s ease-in-out infinite; }
@keyframes breathe { 50% { transform: scale(1.006, 1.014); } }
.head { transform-box: view-box; transform-origin: 515px 612px;
  animation: tilt 11s ease-in-out infinite; }
@keyframes tilt {
  0%, 18% { transform: rotate(0deg); }
  30%, 48% { transform: rotate(-1.6deg); }
  62%, 80% { transform: rotate(1deg); }
  92%, 100% { transform: rotate(0deg); } }
.lids { opacity: 0; animation: lids 5.3s linear infinite; }
@keyframes lids { 0%, 93% { opacity: 0; } 93.5%, 96% { opacity: 1; } 96.5%, 100% { opacity: 0; } }
"""


def build() -> str:
    bold = TTFont(FONT_BOLD)
    regular = TTFont(FONT_REGULAR)
    text_x = 440
    name_d, name_end = text_path(bold, "lystriq", text_x, 128, 80)
    phrase = ["i build clean tools,", "games and apps that work", "and that people use."]
    lines = [text_path(regular, line, text_x, 188 + i * 34, 25)[0] for i, line in enumerate(phrase)]
    tags, _ = text_path(regular, "19 · paris · station f · 42", text_x, 314, 20)
    image = avatar_base64(720)
    left_lid = eyelid_base64(405, 506, 76, 69)
    right_lid = eyelid_base64(591, 506, 50, 68)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-label="lystriq: i build clean tools, games and apps that work and that people use.">
<style>{STYLE}</style>
<defs>
  <clipPath id="head-clip"><path d="M0 0 H1000 V540 L680 540 L660 560 L630 580 L600 600 L560 612 L530 617 L500 615 L470 607 L430 590 L400 572 L0 572 Z"/></clipPath>
  <clipPath id="body-clip"><path d="M1000 1000 H0 V568 L400 568 L430 586 L470 603 L500 611 L530 613 L560 608 L600 596 L630 576 L660 556 L680 536 L1000 536 Z"/></clipPath>
  <image id="art" width="1000" height="1000" href="data:image/png;base64,{image}"/>
</defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>
<svg x="20" y="0" width="{AVATAR_WIDTH:.1f}" height="{HEIGHT}" viewBox="0 0 1000 {AVATAR_CROP}" overflow="hidden">
  <g class="breathe">
    <use href="#art" clip-path="url(#body-clip)"/>
    <g class="head">
      <use href="#art" clip-path="url(#head-clip)"/>
      <g class="lids">
        <image x="405" y="438" width="76" height="69" href="data:image/png;base64,{left_lid}"/>
        <image x="591" y="439" width="50" height="68" href="data:image/png;base64,{right_lid}"/>
      </g>
    </g>
  </g>
</svg>
<path d="{name_d}" fill="{WHITE}"/>
<rect class="cursor" x="{name_end + 10:.1f}" y="70" width="24" height="64" fill="{ACCENT}"/>
{"".join(f'<path d="{d}" fill="{CREAM}"/>' for d in lines)}
<path d="{tags}" fill="{ACCENT}"/>
</svg>
"""


if __name__ == "__main__":
    Path(sys.argv[1]).write_text(build())
