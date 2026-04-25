#!/usr/bin/env python3
import re
import gzip
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"

# =============================================================================
# CUSTOM ELEMENTS
# =============================================================================
# To add a new custom element:
#   1. Create a class with a `tag` (kebab-case), `attrs` list, and `render` method
#   2. `render` receives each attr as a keyword argument (empty string if omitted)
#   3. Add the class to the ELEMENTS list at the bottom of this section
#
# Example usage in index.html:
#   <nz-icon name="home"></nz-icon>   or self-closing: <nz-icon name="home"/>
# =============================================================================

class NzIcon:
    tag = "nz-icon"
    attrs = ["name", "size"]

    def render(self, name, size="24", **_):
        return f'<span class="nz-icon nz-icon-{name}" style="--icon-size:{size or "24"}px"></span>'


class NavButton:
    tag = "nav-button"
    attrs = ["href", "c0", "c1"]

    def render(self, href, inner, c0, c1, **_):
        return f'<a style="text-decoration: none;" href="{href}"><button style="--c1: {c1}; --c0: {c0};">{inner}</button></a>'

# Add new element classes above, then register them here
ELEMENTS = [NzIcon, NavButton]

# =============================================================================
# COMPILER
# =============================================================================

def compile_elements(html):
    for cls in ELEMENTS:
        el = cls()

        def replacer(m, el=el):
            raw = m.group(0)
            kwargs = {
                a: ((re.search(rf'{a}="([^"]*)"', raw) or [None, ""])[1])
                for a in el.attrs
            }
            # extract inner content if the element has a closing tag
            inner = re.search(rf'<{el.tag}[^>]*>(.*?)</{el.tag}>', raw, re.DOTALL)
            kwargs["inner"] = inner.group(1).strip() if inner else ""
            return el.render(**kwargs)

        html = re.sub(
            rf'<{el.tag}[^>]*>.*?</{el.tag}>|<{el.tag}[^>]*/?>',
            replacer,
            html, flags=re.DOTALL
        )
    return html

# =============================================================================
# ICON SPRITE CSS
# =============================================================================

def generate_icon_css():
    icons = (ROOT / "icons.txt").read_text().strip().split("\n")
    total = len(icons)
    sprite_width = total * 24

    css = (
        f".nz-icon{{display:inline-block;width:var(--icon-size,24px);height:var(--icon-size,24px);"
        f"background-color:currentColor;"
        f"mask-image:url('icons.svg');mask-size:{sprite_width}px 24px;"
        f"-webkit-mask-image:url('icons.svg');-webkit-mask-size:{sprite_width}px 24px}}"
    )
    for i, name in enumerate(icons):
        offset = i * 24
        css += f".nz-icon-{name}{{mask-position:-{offset}px 0;-webkit-mask-position:-{offset}px 0}}"

    return css

# =============================================================================
# BUILD
# =============================================================================

def build():
    html = (ROOT / "index.html").read_text()

    html = compile_elements(html)
    html = html.replace("</style>", generate_icon_css() + "\n    </style>", 1)

    DIST.mkdir(exist_ok=True)
    out = DIST / "index.html"
    out.write_text(html)

    for asset in ["icons.svg", "doromiert.svg"]:
        src = ROOT / asset
        if src.exists():
            shutil.copy(src, DIST / asset)

    with open(out, "rb") as f_in, gzip.open(str(out) + ".gz", "wb", compresslevel=9) as f_out:
        f_out.write(f_in.read())

    raw = out.stat().st_size
    gz = Path(str(out) + ".gz").stat().st_size
    print(f"built  {raw:,}b raw  |  {gz:,}b gzip")

build()
