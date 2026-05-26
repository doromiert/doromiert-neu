#!/usr/bin/env python3
import sys
import re, gzip, shutil, io
import markdown as mdlib
from pathlib import Path
import subprocess
import backcompat

# --- OG image deps (optional, skip gracefully if missing) ---
try:
    from PIL import Image, ImageDraw, ImageFont
    import cairosvg as _cairosvg

    _OG_ENABLED = True
except ImportError:
    _OG_ENABLED = False

CSS_VARS = {
    "--b1": "#5a1e17",
    "--b0": "#c96959",
    "--po0": "#e58b3c",
    "--po1": "#7c3a0b",
    "--j0": "#ffd165",
    "--j1": "#a87600",
    "--z0": "#76e256",
    "--z1": "#2e7700",
    "--n0": "#59a7c9",
    "--n1": "#004a69",
    "--r0": "#d47be6",
    "--r1": "#7a1b8d",
    "--pu0": "#7159c9",
    "--pu1": "#150055",
    "--x1": "#5d5d5d",
    "--x0": "#1a1a1a",
    "--w": "#ffffff",
}

BASE_URL = "https://doromiert.neg-zero.com"

PROJ = Path(__file__).parent.parent
DATA = PROJ / "data"
MAIN = PROJ / "src" / "main"
BIZ = PROJ / "src" / "business"
DIST = PROJ / "dist"


def optimize_fonts():
    font_dir = DATA / "fonts"
    font_dir.mkdir(exist_ok=True)

    fonts = [("fonts/std.ttf", "std.woff2"), ("fonts/mono.ttf", "mono.woff2")]

    for src_path, dest_name in fonts:
        src = DATA / src_path
        dest = font_dir / dest_name
        if src.exists() and not dest.exists():
            print(f"Optimizing {dest_name}...")
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "fontTools.subset",
                    str(src),
                    "--unicodes=U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD",
                    "--flavor=woff2",
                    f"--output-file={dest}",
                ]
            )


# =============================================================================
# CUSTOM ELEMENTS
# =============================================================================


class NzIcon:
    tag = "nz-icon"
    attrs = ["name", "size", "rotate"]

    def render(self, name, size="24", rotate="0", **_):
        return f'<span class="nz-icon nz-icon-{name}" style="--icon-size:{size or "24"}px{f";rotate:{rotate}deg" if rotate and rotate != "0" else ""}"></span>'


class BCard:
    tag = "nz-bcard"
    attrs = ["name", "icon"]

    def render(self, name, icon, inner="", **_):
        return f'<div class="nz-bcard"><div class="nz-bcard-header"><nz-icon name="{icon}" size="24" rotate="0"></nz-icon><span>{name}</span></div><div class="nz-bcard-content">{inner}</div></div>'


class Separator:
    tag = "nz-sep"
    attrs = ["name", "c0", "c1", "href"]

    def render(self, name, c0, c1, href="", **_):
        inner = f'<nz-icon rotate="90" name="direction"/>{name}'
        style = f"display:flex;gap:10px;align-items:center;justify-content:center;height:34px;background-color:{c0};color:{c1}"
        if href:
            return f'<a href="{href}" style="text-decoration:none"><div style="{style}">{inner}</div></a>'
        return f'<div style="{style}">{inner}</div>'


class NavButton:
    tag = "nav-button"
    attrs = ["href", "c0", "c1", "id", "style", "aria-label"]

    def render(self, href, inner, c0, c1, id=None, style=None, **kwargs):
        id_attr = f' id="{id}"' if id else ""
        aria = (
            f' aria-label="{kwargs["aria-label"]}"' if kwargs.get("aria-label") else ""
        )
        return f'<a class="navbutton" style="--c1:{c1};--c0:{c0};{style}" {id_attr}{aria} href="{href}">{inner}</a>'


SECTION_COLORS = {
    "doromiert": ("var(--b0)", "var(--b1)", None),
    "jab": ("var(--n1)", "var(--n0)", None),
    "lib": ("var(--z1)", "var(--z0)", "library"),
    "blog": ("var(--po1)", "var(--j0)", "announcement"),
    "devices": ("var(--x0)", "var(--z0)", "cpu"),
    "music": ("var(--r1)", "var(--r0)", "music"),
    "contact": ("var(--pu1)", "var(--r0)", "chat"),
    "b-hero": ("var(--n1)", "var(--j0)", None),
    "b-werk": ("var(--po0)", "var(--po1)", "zap"),
    "b-lib": ("var(--x0)", "var(--w)", "library"),
}


class NzSection:
    tag = "nz-section"
    attrs = ["id", "name", "nosep"]

    def render(self, id, name="", nosep="", inner="", **_):
        c0, c1, icon = SECTION_COLORS.get(id, ("var(--x0)", "var(--w)", None))
        sep_c0, sep_c1 = {
            "jab": ("var(--n1)", "var(--n0)"),
            "lib": ("var(--z1)", "var(--z0)"),
            "blog": ("var(--po1)", "var(--j0)"),
            "devices": ("var(--x0)", "var(--z0)"),
            "music": ("var(--r1)", "var(--r0)"),
            "contact": ("var(--pu1)", "var(--r0)"),
        }.get(id, (c0, c1))
        sep = (
            ""
            if nosep
            else f'<nz-sep name="{name}" href="#{id}" c0="{sep_c0}" c1="{sep_c1}"></nz-sep>'
        )
        extra = (
            ' style="min-height:calc(100vh - 80px)!important"'
            if id == "contact"
            else ""
        )
        header = ""
        if icon:
            header = f'<nz-icon name="{icon}" size="64"></nz-icon><b style="font-size:20px">{name}</b>'
        elif id == "jab":
            header = f'<img id="jab-doromiert" src="doromiert-bold.svg" alt="Logo" /><b style="font-size:20px;">{name}</b>'
        elif id == "b-hero":
            header = f'<div class="doromiert-znak"><img src="doromiert-znak/dor.svg" /><img src="doromiert-znak/omi.svg" /><img src="doromiert-znak/ert.svg" /></div><b style="font-size:20px;">{name}</b>'
        return f'{sep}<section class="nz-section" id="{id}" style="--c0:{c0};--c1:{c1}"{extra}>{header}{inner}</section>'


ELEMENTS = [NzIcon, NavButton, Separator, NzSection, BCard]

# =============================================================================
# COMPILER
# =============================================================================


def md_render(body):
    """Convert markdown → (html, toc_tokens).
    Uses the 'toc' extension so headings get proper id= attributes
    and we get a structured tree to build the minimap from."""
    md = mdlib.Markdown(extensions=["toc", "tables"])
    html = md.convert(body)
    return html, getattr(md, "toc_tokens", [])


def build_minimap_html(toc_tokens, depth=0):
    """Convert md.toc_tokens into nested <details>/<summary> HTML.
    depth=0 → h1 (mm-level-1, no indent)
    depth=1 → h2 (mm-level-2, 12px indent)
    depth=2 → h3 (mm-level-3, 24px indent)"""
    if not toc_tokens:
        return ""
    cls = f"mm-level-{depth + 1}"
    items = []
    for tok in toc_tokens:
        slug = tok["id"]
        name = tok["name"]
        children = tok.get("children", [])
        link = f'<a href="#{slug}">{name}</a>'
        if children:
            inner = build_minimap_html(children, depth + 1)
            items.append(
                f'<details open class="{cls}"><summary>{link}<nz-icon name="direction" rotate="90" size="16"></nz-icon></summary>{inner}</details>'
            )
        else:
            items.append(f'<div class="mm-leaf {cls}">{link}</div>')
    return "".join(items)


def generate_rss(base_url="https://doromiert.neg-zero.com"):
    from email.utils import formatdate
    import time

    src = PROJ / "data" / "blog"
    if not src.exists():
        return

    posts = [
        (f.stem, *parse_frontmatter(f.read_text()))
        for f in sorted(src.glob("*.md"), reverse=True)
    ]
    if not posts:
        return

    def post_to_item(slug, meta, body):
        title = meta.get("title", meta.get("date", slug))
        date = meta.get("date", slug)
        url = f"{base_url}/blog/{slug}.html"
        desc = mdlib.markdown(body)
        # try to parse YYYY-MM-DD into an RFC 2822 date
        try:
            t = time.strptime(date, "%Y-%m-%d")
            pub_date = formatdate(time.mktime(t))
        except ValueError:
            pub_date = formatdate()
        return (
            f"    <item>\n"
            f"      <title>{title}</title>\n"
            f"      <link>{url}</link>\n"
            f'      <guid isPermaLink="true">{url}</guid>\n'
            f"      <pubDate>{pub_date}</pubDate>\n"
            f"      <description><![CDATA[{desc}]]></description>\n"
            f"    </item>"
        )

    items = "\n".join(post_to_item(*p) for p in posts)
    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>doromiert</title>\n"
        f"    <link>{base_url}</link>\n"
        f"    <description>posts by doromiert</description>\n"
        f"    <language>en</language>\n"
        f'    <atom:link href="{base_url}/feed.xml" rel="self" type="application/rss+xml"/>\n'
        f"{items}\n"
        "  </channel>\n"
        "</rss>"
    )
    (DIST / "feed.xml").write_text(rss)
    print(f"feed.xml written ({len(posts)} posts)")


def compile_elements(html):
    for _ in range(10):
        prev = html
        for cls in ELEMENTS:
            el = cls()

            def replacer(m, el=el):
                raw = m.group(0)
                kwargs = {
                    a: ((re.search(rf'{a}="([^"]*)"', raw) or [None, ""])[1])
                    for a in el.attrs
                }
                inner = re.search(
                    rf"<{el.tag}[^>]*>(.*?)</{el.tag}\s*>", raw, re.DOTALL
                )
                kwargs["inner"] = inner.group(1).strip() if inner else ""
                return el.render(**kwargs)

            html = re.sub(
                rf"<{el.tag}[^>]*>.*?</{el.tag}\s*>|<{el.tag}[^>]*/>",
                replacer,
                html,
                flags=re.DOTALL,
            )
        if html == prev:
            break
    return html


def generate_icon_css(icon_path="/icons.svg"):
    icons_file = DATA / "icons.txt"
    if not icons_file.exists():
        return ""
    icons = icons_file.read_text().strip().split("\n")
    total = len(icons)
    css = (
        f".nz-icon{{display:inline-block;width:var(--icon-size,24px);height:var(--icon-size,24px);"
        f"background-color:currentColor;--icon-count:{total};--icon-index:0;"
        f"mask-image:url('{icon_path}');"
        f"mask-size:calc(var(--icon-count)*var(--icon-size,24px)) var(--icon-size,24px);"
        f"mask-position:calc(var(--icon-index)*var(--icon-size,24px)*-1) 0;"
        f"-webkit-mask-image:url('{icon_path}');"
        f"-webkit-mask-size:calc(var(--icon-count)*var(--icon-size,24px)) var(--icon-size,24px);"
        f"-webkit-mask-position:calc(var(--icon-index)*var(--icon-size,24px)*-1) 0}}"
    )
    for i, name in enumerate(icons):
        css += f".nz-icon-{name}{{--icon-index:{i}}}"
    return css


def resolve_var(var):
    """Resolve a CSS var() to a hex color."""
    return CSS_VARS.get(
        var.strip().replace("var(", "").replace(")", "").strip(), "#ffffff"
    )


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def auto_description(body, max_len=160):
    """Extract first meaningful paragraph from markdown body and strip markup."""
    for line in body.splitlines():
        line = line.strip()
        if (
            not line
            or line.startswith("#")
            or line.startswith("!")
            or line.startswith("-")
        ):
            continue
        clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)  # links
        clean = re.sub(r"[*_`#]", "", clean).strip()
        if clean:
            return clean[:max_len] + ("…" if len(clean) > max_len else "")
    return ""


def generate_og_image(title, section_id, icon_name, description, tags, slug, out_dir):
    """Generate a 1200x630 OG preview image. Returns relative URL or empty string."""
    if not _OG_ENABLED:
        return ""

    W, H = 1200, 630
    c0_var, c1_var = CONTENT_C[section_id]
    c0 = resolve_var(c0_var)
    c1 = resolve_var(c1_var)
    c0_rgb = hex_to_rgb(c0)
    c1_rgb = hex_to_rgb(c1)

    img = Image.new("RGB", (W, H), c0_rgb)
    draw = ImageDraw.Draw(img)

    # top accent stripe
    # stripe = tuple(max(0, v - 25) for v in c0_rgb)
    # draw.rectangle([(0, 0), (W, 8)], fill=stripe)

    font_std = str(DATA / "fonts/std.ttf")
    font_mono = str(DATA / "fonts/mono.ttf")

    # doromiert logo — top left, override CSS media query with direct fill
    try:
        dor_svg = (DATA / "doromiert.svg").read_text()
        # nuke the <style> block entirely and set fill directly on the path
        dor_svg = re.sub(r"<style>.*?</style>", "", dor_svg, flags=re.DOTALL)
        dor_svg = re.sub(
            r'id="doromiert-logo-svg"', f'id="doromiert-logo-svg" fill="{c1}"', dor_svg
        )
        dor_png = _cairosvg.svg2png(bytestring=dor_svg.encode(), output_height=36)
        dor_img = Image.open(io.BytesIO(dor_png)).convert("RGBA")
        img.paste(dor_img, (40, 36), dor_img)
    except Exception:
        pass

    # section icon — centered
    try:
        icons = (DATA / "icons.txt").read_text().strip().split("\n")
        _icon = icon_name if icon_name in icons else "docs"
        idx = icons.index(_icon)
        svg_src = (DATA / "icons.svg").read_text()
        patched = re.sub(r'viewBox="[^"]*"', f'viewBox="{idx * 24} 0 24 24"', svg_src)
        patched = re.sub(r'<svg([^>]*?)width="[^"]*"', r'<svg\1width="96"', patched)
        patched = re.sub(r'<svg([^>]*?)height="[^"]*"', r'<svg\1height="96"', patched)
        patched = patched.replace('stroke="white"', f'stroke="{c1}"').replace(
            'fill="white"', f'fill="{c1}"'
        )
        icon_png = _cairosvg.svg2png(bytestring=patched.encode())
        icon_img = Image.open(io.BytesIO(icon_png)).convert("RGBA")
        img.paste(icon_img, ((W - 96) // 2, 168), icon_img)
    except Exception:
        pass

    # title
    try:
        font_title = ImageFont.truetype(font_std, 64)
    except Exception:
        font_title = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), title, font=font_title)
    draw.text(
        ((W - (bbox[2] - bbox[0])) // 2, 288), title, font=font_title, fill=c1_rgb
    )

    # description
    if description:
        try:
            font_desc = ImageFont.truetype(font_std, 24)
        except Exception:
            font_desc = ImageFont.load_default()
        words = description.split()
        lines, line = [], []
        for w in words:
            test = " ".join(line + [w])
            if draw.textbbox((0, 0), test, font=font_desc)[2] > 900 and line:
                lines.append(" ".join(line))
                line = [w]
            else:
                line.append(w)
        if line:
            lines.append(" ".join(line))
        y = 376
        for ln in lines[:2]:
            bx = draw.textbbox((0, 0), ln, font=font_desc)
            draw.text(((W - (bx[2] - bx[0])) // 2, y), ln, font=font_desc, fill=c1_rgb)
            y += 36

    # bottom-right URL
    # try:
    #     font_url = ImageFont.truetype(font_mono, 16)
    # except Exception:
    #     font_url = ImageFont.load_default()
    # url_text = "doromiert.neg-zero.com"
    # bx = draw.textbbox((0, 0), url_text, font=font_url)
    # faded_url = tuple(int(v * 0.4) for v in c1_rgb)
    # draw.text(
    #     (W - (bx[2] - bx[0]) - 40, H - 38), url_text, font=font_url, fill=faded_url
    # )

    dest = out_dir / "og" / section_id
    dest.mkdir(parents=True, exist_ok=True)
    out_path = dest / f"{slug}.png"
    img.save(out_path, optimize=True)
    return f"/og/{section_id}/{slug}.png"


def inline_svgs(html):
    def read_svg(src):
        path = DATA / src.lstrip("/")
        if not path.exists():
            return None
        svg = path.read_text()
        return re.sub(r"<\?xml[^?]*\?>", "", svg).strip()

    def img_replacer(m):
        raw = m.group(0)
        src_m = re.search(r'src="([^"]+\.svg)"', raw)
        if not src_m:
            return raw
        svg = read_svg(src_m.group(1))
        if svg is None:
            return raw
        style_m = re.search(r'style="([^"]*)"', raw)
        if style_m and style_m.group(1):
            svg = re.sub(r"<svg", f'<svg style="{style_m.group(1)}"', svg, count=1)
        alt_m = re.search(r'alt="([^"]*)"', raw)
        if alt_m and alt_m.group(1):
            svg = re.sub(
                r"<svg", f'<svg aria-label="{alt_m.group(1)}" role="img"', svg, count=1
            )
        return svg

    html = re.sub(r'<img\b[^>]*src="[^"]+\.svg"[^>]*/>', img_replacer, html)

    def favicon_replacer(m):
        raw = m.group(0)
        href_m = re.search(r'href="([^"]+\.svg)"', raw)
        if not href_m:
            return raw
        path = DATA / href_m.group(1).lstrip("/")
        if not path.exists():
            return raw
        import base64

        b64 = base64.b64encode(path.read_bytes()).decode()
        return re.sub(r'href="[^"]+"', f'href="data:image/svg+xml;base64,{b64}"', raw)

    html = re.sub(
        r'<link\b[^>]*rel="icon"[^>]*href="[^"]+\.svg"[^>]*/>', favicon_replacer, html
    )
    return html


# =============================================================================
# CONTENT SYSTEM
# =============================================================================
#
# Directory layout:
#   lib/slug.md        → card in #lib section + /lib/slug.html article page
#   blog/YYYY-MM-DD.md → latest post inline in #blog + /blog/slug.html + /blog/index.html
#   devices/slug.md    → categorized row in #devices + /devices/slug.html article page
#   music/slug.md      → categorized row in #music + /music/slug.html article page
#   music/_now.txt     → two lines: song title / artist  (optional, shown in #music)
#
# Frontmatter keys (all optional):
#   title, subtitle, icon, tags (comma-sep), category (devices/music), date (blog),
#   url (lib: external link overrides generated article page)
#
# =============================================================================

CONTENT_C = {
    "lib": ("var(--z1)", "var(--z0)"),
    "blog": ("var(--po1)", "var(--j0)"),
    "devices": ("var(--x0)", "var(--z0)"),
    "music": ("var(--r1)", "var(--r0)"),
}


def parse_frontmatter(text):
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta = {}
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            return meta, parts[2].strip()
    return {}, text


def lnk_btn(label_html, href, c0, c1, btnClass=""):
    if href:
        return f'<a href="{href}" class="navbutton {btnClass}" style="--c0:{c0};--c1:{c1};width:100%">{label_html}</a>'
    return f'<span class="navbutton {btnClass}" style="--c0:{c0};--c1:{c1};width:min-content;opacity:.3;cursor:not-allowed">{label_html}</span>'


def article_page(
    title,
    body_html,
    section_id,
    minimap_html="",
    description="",
    og_image_url="",
    canonical_url="",
):
    c0, c1 = CONTENT_C[section_id]
    minimap = (
        f'<nav class="article-minimap">{minimap_html}</nav>' if minimap_html else ""
    )
    og_image_abs = (
        f"{BASE_URL}{og_image_url}" if og_image_url else f"{BASE_URL}/images/og.png"
    )
    desc_tag = (
        f'<meta name="description" content="{description}"/>' if description else ""
    )
    og_tags = (
        f'<meta property="og:title" content="{title} — doromiert"/>'
        f'<meta property="og:type" content="article"/>'
        f'<meta property="og:image" content="{og_image_abs}"/>'
        + (
            f'<meta property="og:description" content="{description}"/>'
            if description
            else ""
        )
        + (
            f'<meta property="og:url" content="{canonical_url}"/>'
            if canonical_url
            else ""
        )
        + f'<meta name="twitter:card" content="summary_large_image"/>'
        + f'<meta name="twitter:image" content="{og_image_abs}"/>'
    )
    return (
        f'<!doctype html><html lang="en"><head>'
        f'<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>'
        f"<title>{title} — doromiert</title>"
        f'<link rel="icon" type="image/svg+xml" href="/doromiert.svg"/>'
        f"{desc_tag}{og_tags}"
        f"<style>{(PROJ / 'src' / 'base.css').read_text()}</style>"
        f"<style>:root{{--c0:{c0};--c1:{c1}}}"
        f"body{{margin:0;padding:0;background:var(--c0);color:var(--c1);"
        f"min-height:100vh;display:flex;flex-direction:column;align-items:center}}"
        f"</style>"
        f'</head><body style="gap: 20px;">'
        f"{minimap}"
        f'<nav-button id="page-back" href="/#{section_id}" c0="{c0}" c1="{c1}"><nz-icon name="direction" rotate="90"></nz-icon></nav-button>'
        f"{body_html}"
        f"</body></html>"
    )


def compile_page(html):
    """Run element compiler + inject icon CSS (absolute path for sub-pages)."""
    html = compile_elements(html)
    return html.replace("</style>", generate_icon_css("/icons.svg") + "</style>", 1)


# --- lib ---


def build_lib():
    src = PROJ / "data" / "lib"
    if not src.exists():
        return ""
    c0, c1 = CONTENT_C["lib"]
    out = DIST / "lib"
    out.mkdir(parents=True, exist_ok=True)
    cards = []
    for f in sorted(src.glob("*.md")):
        meta, body = parse_frontmatter(f.read_text())
        title = meta.get("title", f.stem)
        subtitle = meta.get("subtitle", "")
        icon = meta.get("icon", "docs")
        tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
        ext_url = meta.get("url", "")
        href = ext_url or f"/lib/{f.stem}.html"
        tag_html = "".join(f'<span class="tag">{t}</span>' for t in tags)
        cards.append(
            f'<a class="card" href="{href}">'
            f'<nz-icon name="{icon}" size="32"></nz-icon>'
            f"<b>{title}</b>"
            f"</a>"
        )
        if not ext_url:
            art_tags = "".join(f'<span class="art-tag">{t}</span>' for t in tags)

            md_html, toc_tokens = md_render(body)
            minimap_html = build_minimap_html(toc_tokens)
            body_html = (
                f'<div class="art-header">'
                f'<nz-icon name="{icon}" size="64"></nz-icon>'
                f'<b style="font-size:24px">{title}</b>'
                f"{'<span class=art-subtitle>' + subtitle + '</span>' if subtitle else ''}"
                f"{'<div class=art-tags>' + art_tags + '</div>' if art_tags else ''}"
                f"</div>"
                f"<article>{md_html}</article>"
            )
            desc = meta.get("description", "") or auto_description(body)
            og_url = generate_og_image(title, "lib", icon, desc, tags, f.stem, DIST)
            canonical = f"{BASE_URL}/lib/{f.stem}.html"
            (out / f"{f.stem}.html").write_text(
                compile_page(
                    article_page(
                        title, body_html, "lib", minimap_html, desc, og_url, canonical
                    )
                )
            )

    return f'<div class="card-grid">{"".join(cards)}</div>'


# --- blog ---


def build_blog():
    src = PROJ / "data" / "blog"
    if not src.exists():
        return ""
    c0, c1 = CONTENT_C["blog"]
    out = DIST / "blog"
    out.mkdir(parents=True, exist_ok=True)
    posts = [
        (f.stem, *parse_frontmatter(f.read_text()))
        for f in sorted(src.glob("*.md"), reverse=True)
    ]
    if not posts:
        return ""
    total = len(posts)

    # Individual post pages
    for i, (slug, meta, body) in enumerate(posts):
        date = meta.get("date", slug)
        prev_url = f"/blog/{posts[i + 1][0]}.html" if i + 1 < total else ""
        next_url = f"/blog/{posts[i - 1][0]}.html" if i > 0 else ""

        md_html, toc_tokens = md_render(body)
        minimap_html = build_minimap_html(toc_tokens)
        body_html = (
            f'<div class="art-header"><b style="font-size:18px">{date} ({i + 1}/{total})</b></div>'
            f"<article>{md_html}</article>"
            f'<div class="post-nav">'
            f"{lnk_btn('<nz-icon name="direction"rotate="180"></nz-icon>', next_url, c0, c1)}"
            f"{lnk_btn('<nz-icon name="calendar"></nz-icon><span>Browse by date</span>', '/blog/', c0, c1)}"
            f"{lnk_btn('<nz-icon name="direction" ></nz-icon>', prev_url, c0, c1)}"
            f"</div>"
            f"{lnk_btn('<nz-icon name="rss"></nz-icon><span >RSS feed</span>', '/feed.xml', 'var(--j0)', 'var(--x0)', 'rss-btn')}"
        )
        desc = meta.get("description", "") or auto_description(body)
        post_title = meta.get("title", date)
        og_url = generate_og_image(
            post_title, "blog", "announcement", desc, [], slug, DIST
        )
        canonical = f"{BASE_URL}/blog/{slug}.html"
        (out / f"{slug}.html").write_text(
            compile_page(
                article_page(
                    date, body_html, "blog", minimap_html, desc, og_url, canonical
                )
            )
        )

    # Date index page /blog/index.html
    date_btns = "".join(
        lnk_btn(meta.get("date", slug), f"/blog/{slug}.html", c0, c1)
        for slug, meta, _ in posts
    )
    index_body = (
        f'<div class="art-header">'
        f'<nz-icon name="calendar" size="64"></nz-icon>'
        f'<b style="font-size:20px">All posts</b>'
        f"</div>"
        f'<div class="card-grid" style="max-width:600px" id="blog-content">{date_btns}</div>'
        f"<style>body{{padding: 0px 20px}}</style>"
    )

    (out / "index.html").write_text(
        compile_page(article_page("Blog", index_body, "blog"))
    )

    # Inline snippet for index.html — latest post only
    slug, meta, body = posts[0]
    date = meta.get("date", slug)
    prev_url = f"/blog/{posts[1][0]}.html" if total > 1 else ""
    return (
        f'<b style="font-size:18px">{date} (1/{total})</b>'
        f'<div class="blog-body">{mdlib.markdown(body)}</div>'
        f'<div class="post-nav">'
        f"{lnk_btn('<nz-icon name="calendar"></nz-icon><span>Browse by date</span>', '/blog/', c0, c1)}"
        f"{lnk_btn('<nz-icon name="direction" ></nz-icon>', prev_url, c0, c1)}"
        f"</div>"
        f"{lnk_btn('<nz-icon name="rss"></nz-icon><span >RSS feed</span>', '/feed.xml', 'var(--j0)', 'var(--x0)', 'rss-btn')}"
    )


# --- devices / music (categorized) ---


def build_category(section_id):
    src = PROJ / "data" / section_id
    if not src.exists():
        return ""
    c0, c1 = CONTENT_C[section_id]
    out = DIST / section_id
    out.mkdir(parents=True, exist_ok=True)

    cats: dict = {}
    for f in sorted(src.glob("*.md")):
        if f.name.startswith("_"):
            continue
        meta, body = parse_frontmatter(f.read_text())
        cats.setdefault(meta.get("category", "Other"), []).append((f.stem, meta, body))

    # Article pages
    for items in cats.values():
        for slug, meta, body in items:
            title = meta.get("title", slug)
            icon = meta.get("icon", "docs")
            tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
            art_tags = "".join(f'<span class="art-tag">{t}</span>' for t in tags)

            md_html, toc_tokens = md_render(body)
            minimap_html = build_minimap_html(toc_tokens)
            body_html = (
                f'<div class="art-header">'
                f'<nz-icon name="{icon}" size="64"></nz-icon>'
                f'<b style="font-size:24px">{title}</b>'
                f"{'<div class=art-tags>' + art_tags + '</div>' if art_tags else ''}"
                f"</div>"
                f"<article>{md_html}</article>"
            )
            desc = meta.get("description", "") or auto_description(body)
            og_url = generate_og_image(title, section_id, icon, desc, tags, slug, DIST)
            canonical = f"{BASE_URL}/{section_id}/{slug}.html"
            (out / f"{slug}.html").write_text(
                compile_page(
                    article_page(
                        title,
                        body_html,
                        section_id,
                        minimap_html,
                        desc,
                        og_url,
                        canonical,
                    )
                )
            )

    # "Now listening to" widget for music
    now_html = ""
    if section_id == "music":
        nf = src / "_now.txt"
        if nf.exists():
            lines = nf.read_text().strip().splitlines()
            song = lines[0] if lines else ""
            artist = lines[1] if len(lines) > 1 else ""
            now_html = (
                f'<div class="now-playing">'
                f'<div class="np-label"><nz-icon name="headphones"></nz-icon>Now listening to</div>'
                f'<span class="np-song" style="margin-left: 4px;">{song}</span>'
                f'<span style="margin-left: 4px;">{artist}</span>'
                f"</div>"
            )

    # Category groups
    groups = "".join(
        f'<div class="cat-group">'
        f'<div class="cat-header">{cat}</div>'
        f'<div class="cat-rows">'
        + "".join(
            f'<a class="cat-item" href="/{section_id}/{slug}.html">'
            f'<nz-icon name="{meta.get("icon", "docs")}"></nz-icon>'
            f"<span>{meta.get('title', slug)}</span>"
            f'<nz-icon name="direction"></nz-icon>'
            f"</a>"
            for slug, meta, _ in items
        )
        + f"</div></div>"
        for cat, items in cats.items()
    )
    return now_html + f'<div class="cat-list">{groups}</div>'


def inject_section(html, section_id, content):
    """Inject content into empty <nz-section id="X" ...></nz-section>."""

    def rep(m):
        if f'id="{section_id}"' in m.group(0):
            return m.group(0).replace("></nz-section>", f">{content}</nz-section>", 1)
        return m.group(0)

    return re.sub(r"<nz-section[^>]*></nz-section>", rep, html)


def generate_sitemap(base_url="https://doromiert.neg-zero.com"):
    urls = []
    for f in sorted(DIST.rglob("*.html")):
        rel = f.relative_to(DIST).as_posix()
        # skip .gz artifacts if any sneak in, skip business pages if you want
        if rel.endswith(".gz"):
            continue
        path = "/" + rel
        urls.append(f"  <url><loc>{base_url}{path}</loc></url>")

    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>"
    )
    (DIST / "sitemap.xml").write_text(sitemap)

    # robots.txt pointing to it
    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n"
    )
    print(f"sitemap.xml written ({len(urls)} URLs)")


def generate_llms_txt(base_url="https://doromiert.neg-zero.com"):
    """Generate llms.txt and llms-full.txt for AI agent discovery."""

    # ---- collect data from all content sections ----
    def collect_section(section_id):
        src = PROJ / "data" / section_id
        if not src.exists():
            return []
        entries = []
        for f in sorted(src.glob("*.md")):
            if f.name.startswith("_"):
                continue
            meta, body = parse_frontmatter(f.read_text())
            entries.append((f.stem, meta, body))
        return entries

    blog_posts = []
    src_blog = PROJ / "data" / "blog"
    if src_blog.exists():
        for f in sorted(src_blog.glob("*.md"), reverse=True):
            meta, body = parse_frontmatter(f.read_text())
            blog_posts.append((f.stem, meta, body))

    lib_entries = collect_section("lib")
    dev_entries = collect_section("devices")
    music_entries = collect_section("music")

    # ---- build llms.txt (index / summary) ----
    lines = [
        "# doromiert",
        "",
        "> Personal site of doromiert — developer and designer.",
        '> Part of Negative Zero (–0), a tech collective with the mission "technology that takes you seriously".',
        "",
        f"Full site: {base_url}",
        f"RSS feed: {base_url}/feed.xml",
        "",
    ]

    if blog_posts:
        lines += ["## Blog", ""]
        for slug, meta, body in blog_posts:
            title = meta.get("title", slug)
            date = meta.get("date", slug)
            url = f"{base_url}/blog/{slug}.html"
            # first non-empty line of body as blurb, strip markdown
            blurb = next(
                (
                    re.sub(r"[#*`\[\]()]", "", l).strip()
                    for l in body.splitlines()
                    if l.strip()
                ),
                "",
            )[:120]
            entry = f"- [{title or date}]({url})"
            if blurb:
                entry += f": {blurb}"
            lines.append(entry)
        lines.append("")

    if lib_entries:
        lines += ["## Library / Projects", ""]
        for slug, meta, body in lib_entries:
            title = meta.get("title", slug)
            url = meta.get("url") or f"{base_url}/lib/{slug}.html"
            tags = meta.get("tags", "")
            blurb = next(
                (
                    re.sub(r"[#*`\[\]()]", "", l).strip()
                    for l in body.splitlines()
                    if l.strip()
                ),
                tags,
            )[:120]
            entry = f"- [{title}]({url})"
            if blurb:
                entry += f": {blurb}"
            lines.append(entry)
        lines.append("")

    if dev_entries:
        lines += ["## Devices", ""]
        for slug, meta, body in dev_entries:
            title = meta.get("title", slug)
            cat = meta.get("category", "")
            url = f"{base_url}/devices/{slug}.html"
            entry = f"- [{title}]({url})"
            if cat:
                entry += f" ({cat})"
            lines.append(entry)
        lines.append("")

    if music_entries:
        lines += ["## Music", ""]
        for slug, meta, body in music_entries:
            title = meta.get("title", slug)
            url = f"{base_url}/music/{slug}.html"
            lines.append(f"- [{title}]({url})")
        lines.append("")

    llms_txt = "\n".join(lines)
    (DIST / "llms.txt").write_text(llms_txt)
    print("llms.txt written")

    # ---- build llms-full.txt (everything inlined) ----
    full_lines = [llms_txt, "---", ""]

    def append_section_full(section_name, entries, url_prefix):
        if not entries:
            return
        full_lines.append(f"# {section_name}")
        full_lines.append("")
        for slug, meta, body in entries:
            title = meta.get("title", slug)
            url = f"{base_url}/{url_prefix}/{slug}.html"
            full_lines.append(f"## [{title}]({url})")
            if meta:
                for k, v in meta.items():
                    if k not in ("title",) and v:
                        full_lines.append(f"_{k}: {v}_")
            full_lines.append("")
            full_lines.append(body.strip())
            full_lines.append("")
            full_lines.append("---")
            full_lines.append("")

    if blog_posts:
        full_lines.append("# Blog Posts")
        full_lines.append("")
        for slug, meta, body in blog_posts:
            title = meta.get("title", meta.get("date", slug))
            url = f"{base_url}/blog/{slug}.html"
            full_lines.append(f"## [{title}]({url})")
            for k, v in meta.items():
                if k not in ("title",) and v:
                    full_lines.append(f"_{k}: {v}_")
            full_lines.append("")
            full_lines.append(body.strip())
            full_lines.append("")
            full_lines.append("---")
            full_lines.append("")

    append_section_full("Library / Projects", lib_entries, "lib")
    append_section_full("Devices", dev_entries, "devices")
    append_section_full("Music", music_entries, "music")

    llms_full_txt = "\n".join(full_lines)
    (DIST / "llms-full.txt").write_text(llms_full_txt)
    print(f"llms-full.txt written ({len(llms_full_txt)} chars)")


def build():
    optimize_fonts()
    DIST.mkdir(exist_ok=True)
    BIZ.mkdir(parents=True, exist_ok=True)
    (DIST / "CNAME").write_text("doromiert.neg-zero.com")

    base_css = (
        (PROJ / "src" / "base.css").read_text()
        if (PROJ / "src" / "base.css").exists()
        else ""
    )

    l, b, d, m = (
        build_lib(),
        build_blog(),
        build_category("devices"),
        build_category("music"),
    )

    def compile_standard_page(raw, vt_name):
        html = re.sub(
            r'<link[^>]*href="[^"]*base\.css"[^>]*>',
            f'<style>{base_css}</style>\n<meta name="robots" content="index, follow">\n<meta name="google-site-verification" content="-eYbb_jJi6sNoLs0tLS1QkbVupJZxszUWiAsZ_JZl44" />',
            raw,
        )
        html = inject_section(
            inject_section(
                inject_section(inject_section(html, "lib", l), "blog", b), "devices", d
            ),
            "music",
            m,
        )
        html = compile_elements(html)
        html = inline_svgs(html)
        html = html.replace("</style>", generate_icon_css() + "</style>", 1)
        # inject the transition name into the body
        html = re.sub(
            r"<body([^>]*)>", rf'<body\1 style="view-transition-name: {vt_name}">', html
        )
        return html

    if (MAIN / "index.html").exists():
        (DIST / "index.html").write_text(
            compile_standard_page((MAIN / "index.html").read_text(), "page-main")
        )

    for f in BIZ.rglob("*"):
        if f.is_file():
            out = DIST / "business" / f.relative_to(BIZ)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(
                compile_standard_page(f.read_text(), "page-biz")
            ) if f.suffix == ".html" else shutil.copy(f, out)

    for asset in [
        "images",
        "icons.svg",
        "doromiert-znak",
        "doromiert-bold.svg",
        "doromiert.svg",
        "fonts",
    ]:
        src = DATA / asset
        if src.exists():
            shutil.copytree(
                src, DIST / asset, dirs_exist_ok=True
            ) if src.is_dir() else shutil.copy(src, DIST / asset)

    # --- WII U BACKCOMPAT UNROLLER PASS (MUST RUN BEFORE GZIP) ---
    print("\nviolently flattening css and html for the wii u...")
    base_css_src = PROJ / "src" / "base.css"

    if base_css_src.exists():
        # 1. extract variables from original base.css source
        global_vars = backcompat.extract_root_vars(
            base_css_src.read_text(encoding="utf-8")
        )

        # 2. unnest & unroll standalone base.css in dist
        backcompat.compile_compatible_css(base_css_src, DIST / "base.css", global_vars)

        # 3. sweep all generated HTML in dist to unroll inlined blocks & inline styles
        for html_dist in DIST.rglob("*.html"):
            backcompat.compile_html_file(html_dist, html_dist, global_vars)

        print("✅ HTML and CSS fully unrolled & optimized.")
    else:
        print(f"⚠️ could not find base.css at {base_css_src}, skipping unroll pass.")

    # --- SITEMAP, RSS & LLMS.TXT ---
    generate_sitemap()
    generate_rss()
    generate_llms_txt()

    # --- FINAL GZIP COMPRESSION STEP ---
    print("compressing files...")
    for f in list(DIST.rglob("*.html")) + list(DIST.glob("sitemap.xml")):
        with (
            open(f, "rb") as fi,
            gzip.open(str(f) + ".gz", "wb", compresslevel=9) as fo,
        ):
            fo.write(fi.read())

    print("build complete.")


if __name__ == "__main__":
    build()
