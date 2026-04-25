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
    attrs = ["name", "size", "rotate"]

    def render(self, name, size="24", rotate="0", **_):
        return f'<span class="nz-icon nz-icon-{name}" style="--icon-size:{size or "24"}px;rotate:{rotate}deg"></span>'

class Separator:
    tag = "nz-sep"
    attrs = ["name", "c0", "c1", "href"]

    def render(self, name, c0, c1, href="", **_):
        inner = f'<nz-icon rotate="90" name="direction"/>{name}'
        style = f'display:flex;gap:10px;align-items:center;justify-content:center;height:34px;background-color:{c0};color:{c1}'
        if href:
            return f'<a href="{href}" style="text-decoration:none"><div style="{style}">{inner}</div></a>'
        return f'<div style="{style}">{inner}</div>'

class NavButton:
    tag = "nav-button"
    attrs = ["href", "c0", "c1", "id"]

    def render(self, href, inner, c0, c1, id=None, **_):
        id_attr = f' id="{id}"' if id else ""
        return f'<a style="text-decoration: none;" href="{href}"><button style="--c1: {c1}; --c0: {c0};"{id_attr}>{inner}</button></a>'

SECTION_COLORS = {
    "doromiert": ("var(--b0)",  "var(--b1)", None),
    "jab":       ("var(--n1)",  "var(--n0)", None),
    "lib":       ("var(--z1)",  "var(--z0)", "library"),
    "blog":      ("var(--po1)", "var(--j0)", "announcement"),
    "devices":   ("var(--x0)",  "var(--z0)", "cpu"),
    "music":     ("var(--r1)",  "var(--r0)", "music"),
    "contact":   ("var(--pu1)", "var(--r0)", "chat"),
}

class NzSection:
    tag = "nz-section"
    attrs = ["id", "name", "nosep"]

    def render(self, id, name="", nosep="", inner="", **_):
        c0, c1, icon = SECTION_COLORS.get(id, ("var(--x0)", "var(--w)", None))
        sep_c0, sep_c1 = {
            "jab":     ("var(--n1)", "var(--n0)"),
            "lib":     ("var(--z1)", "var(--z0)"),
            "blog":    ("var(--po1)", "var(--j0)"),
            "devices": ("var(--x0)", "var(--z0)"),
            "music":   ("var(--r1)", "var(--r0)"),
            "contact": ("var(--pu1)", "var(--r0)"),
        }.get(id, (c0, c1))

        sep = "" if nosep else f'<nz-sep name="{name}" href="#{id}" c0="{sep_c0}" c1="{sep_c1}"></nz-sep>'
        extra = ' style="min-height:calc(100vh - 80px)!important"' if id == "contact" else ""

        header = ""
        if icon:
            header = f'<nz-icon name="{icon}" size="64"></nz-icon><b style="font-size:20px">{name}</b>'
        elif id == "jab":
            header = f'<img src="doromiert-bold.svg" alt="Logo" /><b style="font-size:20px">{name}</b>'

        return f'{sep}<section class="nz-section" id="{id}" style="--c0:{c0};--c1:{c1}"{extra}>{header}{inner}</section>'

# Add new element classes above, then register them here
ELEMENTS = [NzIcon, NavButton, Separator, NzSection]

# =============================================================================
# COMPILER
# =============================================================================

def compile_elements(html):
    for _ in range(10):  # max depth, prevents infinite loops
        prev = html
        for cls in ELEMENTS:
            el = cls()

            def replacer(m, el=el):
                raw = m.group(0)
                kwargs = {
                    a: ((re.search(rf'{a}="([^"]*)"', raw) or [None, ""])[1])
                    for a in el.attrs
                }
                inner = re.search(rf'<{el.tag}[^>]*>(.*?)</{el.tag}>', raw, re.DOTALL)
                kwargs["inner"] = inner.group(1).strip() if inner else ""
                return el.render(**kwargs)

            html = re.sub(
                rf'<{el.tag}[^>]*>.*?</{el.tag}>|<{el.tag}[^>]*/?>',
                replacer,
                html, flags=re.DOTALL
            )
        if html == prev:
            break  # nothing left to expand
    return html

# =============================================================================
# ICON SPRITE CSS
# =============================================================================

def generate_icon_css():
    icons = (ROOT / "icons.txt").read_text().strip().split("\n")
    total = len(icons)

    css = (
        f".nz-icon{{display:inline-block;width:var(--icon-size,24px);height:var(--icon-size,24px);"
        f"background-color:currentColor;"
        f"--icon-count:{total};--icon-index:0;"
        f"mask-image:url('icons.svg');"
        f"mask-size:calc(var(--icon-count)*var(--icon-size,24px)) var(--icon-size,24px);"
        f"mask-position:calc(var(--icon-index)*var(--icon-size,24px)*-1) 0;"
        f"-webkit-mask-image:url('icons.svg');"
        f"-webkit-mask-size:calc(var(--icon-count)*var(--icon-size,24px)) var(--icon-size,24px);"
        f"-webkit-mask-position:calc(var(--icon-index)*var(--icon-size,24px)*-1) 0}}"
    )
    for i, name in enumerate(icons):
        css += f".nz-icon-{name}{{--icon-index:{i}}}"

    return css

# =============================================================================
# INLINE SVGS
# =============================================================================

def inline_svgs(html):
    def replacer(m):
        src = m.group(1)
        style = m.group(2)
        path = ROOT / src
        if not path.exists():
            return m.group(0)
        svg = path.read_text()
        if style:
            svg = re.sub(r'<svg', f'<svg style="{style}"', svg, count=1)
        return svg
    return re.sub(r'<img\s+src="([^"]+\.svg)"[^>]*style="([^"]*)"[^>]*/>', replacer, html)

# =============================================================================
# BUILD
# =============================================================================

def build():
    html = (ROOT / "index.html").read_text()

    html = inline_svgs(html)       # inline SVGs first, before element compilation
    html = compile_elements(html)  # so inner content is already resolved
    html = html.replace("</style>", generate_icon_css() + "\n    </style>", 1)

    DIST.mkdir(exist_ok=True)
    out = DIST / "index.html"
    out.write_text(html)           # write once, after all transforms

    for asset in ["icons.svg", "doromiert-znak", "doromiert-bold.svg"]:
        src = ROOT / asset
        if not src.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, DIST / asset, dirs_exist_ok=True)
        else:
            shutil.copy(src, DIST / asset)

    with open(out, "rb") as f_in, gzip.open(str(out) + ".gz", "wb", compresslevel=9) as f_out:
        f_out.write(f_in.read())

    raw = out.stat().st_size
    gz = Path(str(out) + ".gz").stat().st_size
    print(f"built  {raw:,}b raw  |  {gz:,}b gzip")

build()
