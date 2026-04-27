#!/usr/bin/env python3
import sys
import re, gzip, shutil
import markdown as mdlib
from pathlib import Path
import subprocess

PROJ = Path(__file__).parent.parent
DATA = PROJ / "data"
MAIN = PROJ / "src" / "main"
BIZ  = PROJ / "src" / "business"
DIST = PROJ / "dist"

def optimize_fonts():
    font_dir = DATA / "fonts"
    font_dir.mkdir(exist_ok=True)

    fonts = [
        ("fonts/std.ttf", "std.woff2"),
        ("fonts/mono.ttf", "mono.woff2")
    ]

    for src_path, dest_name in fonts:
        src = DATA / src_path
        dest = font_dir / dest_name
        if src.exists() and not dest.exists():
            print(f"Optimizing {dest_name}...")
            subprocess.run([
                sys.executable, "-m", "fontTools.subset", str(src),
                "--unicodes=U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD",
                "--flavor=woff2",
                f"--output-file={dest}"
            ])

# =============================================================================
# CUSTOM ELEMENTS
# =============================================================================

class NzIcon:
    tag = "nz-icon"
    attrs = ["name", "size", "rotate"]
    def render(self, name, size="24", rotate="0", **_):
        return f'<span class="nz-icon nz-icon-{name}" style="--icon-size:{size or "24"}px;rotate:{rotate}deg"></span>'

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
        style = f'display:flex;gap:10px;align-items:center;justify-content:center;height:34px;background-color:{c0};color:{c1}'
        if href:
            return f'<a href="{href}" style="text-decoration:none"><div style="{style}">{inner}</div></a>'
        return f'<div style="{style}">{inner}</div>'

class NavButton:
    tag = "nav-button"
    attrs = ["href", "c0", "c1", "id", "style"]
    def render(self, href, inner, c0, c1, id=None, style=None, **_):
        id_attr = f' id="{id}"' if id else ""
        return f'<a style="text-decoration: none;" href="{href}"><button style="--c1: {c1}; --c0: {c0}; {style}"{id_attr}>{inner}</button></a>'

SECTION_COLORS = {
    "doromiert": ("var(--b0)",  "var(--b1)", None),
    "jab":       ("var(--n1)",  "var(--n0)", None),
    "lib":       ("var(--z1)",  "var(--z0)", "library"),
    "blog":      ("var(--po1)", "var(--j0)", "announcement"),
    "devices":   ("var(--x0)",  "var(--z0)", "cpu"),
    "music":     ("var(--r1)",  "var(--r0)", "music"),
    "contact":   ("var(--pu1)", "var(--r0)", "chat"),
    "b-hero":    ("var(--n1)",  "var(--j0)", None),
    "b-werk":    ("var(--po0)",  "var(--po1)", "zap"),
    "b-lib":     ("var(--x0)",  "var(--w)", "library"),
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
            header = f'<img id="jab-doromiert" src="doromiert-bold.svg" alt="Logo" /><b style="font-size:20px;">{name}</b>'
        elif id == "b-hero":
            header = f'<div class="doromiert-znak"><img src="doromiert-znak/dor.svg" /><img src="doromiert-znak/omi.svg" /><img src="doromiert-znak/ert.svg" /></div><b style="font-size:20px;">{name}</b>'
        return f'{sep}<section class="nz-section" id="{id}" style="--c0:{c0};--c1:{c1}"{extra}>{header}{inner}</section>'

ELEMENTS = [NzIcon, NavButton, Separator, NzSection, BCard]

# =============================================================================
# COMPILER
# =============================================================================

def compile_elements(html):
    for _ in range(10):
        prev = html
        for cls in ELEMENTS:
            el = cls()
            def replacer(m, el=el):
                raw = m.group(0)
                kwargs = {a: ((re.search(rf'{a}="([^"]*)"', raw) or [None, ""])[1]) for a in el.attrs}
                inner = re.search(rf'<{el.tag}[^>]*>(.*?)</{el.tag}\s*>', raw, re.DOTALL)
                kwargs["inner"] = inner.group(1).strip() if inner else ""
                return el.render(**kwargs)
            html = re.sub(
                rf'<{el.tag}[^>]*>.*?</{el.tag}\s*>|<{el.tag}[^>]*/>',
                replacer, html, flags=re.DOTALL
            )
        if html == prev:
            break
    return html

def generate_icon_css(icon_path="/icons.svg"):
    icons_file = DATA / "icons.txt"
    if not icons_file.exists(): return ""
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

def inline_svgs(html):
    def read_svg(src):
        path = DATA / src.lstrip("/")
        if not path.exists(): return None
        svg = path.read_text()
        return re.sub(r'<\?xml[^?]*\?>', '', svg).strip()

    def img_replacer(m):
        raw = m.group(0)
        src_m = re.search(r'src="([^"]+\.svg)"', raw)
        if not src_m: return raw
        svg = read_svg(src_m.group(1))
        if svg is None: return raw
        style_m = re.search(r'style="([^"]*)"', raw)
        if style_m and style_m.group(1):
            svg = re.sub(r'<svg', f'<svg style="{style_m.group(1)}"', svg, count=1)
        alt_m = re.search(r'alt="([^"]*)"', raw)
        if alt_m and alt_m.group(1):
            svg = re.sub(r'<svg', f'<svg aria-label="{alt_m.group(1)}" role="img"', svg, count=1)
        return svg

    html = re.sub(r'<img\b[^>]*src="[^"]+\.svg"[^>]*/>', img_replacer, html)

    def favicon_replacer(m):
        raw = m.group(0)
        href_m = re.search(r'href="([^"]+\.svg)"', raw)
        if not href_m: return raw
        path = DATA / href_m.group(1).lstrip("/")
        if not path.exists(): return raw
        import base64
        b64 = base64.b64encode(path.read_bytes()).decode()
        return re.sub(r'href="[^"]+"', f'href="data:image/svg+xml;base64,{b64}"', raw)

    html = re.sub(r'<link\b[^>]*rel="icon"[^>]*href="[^"]+\.svg"[^>]*/>', favicon_replacer, html)
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
    "lib":     ("var(--z1)",  "var(--z0)"),
    "blog":    ("var(--po1)", "var(--j0)"),
    "devices": ("var(--x0)",  "var(--z0)"),
    "music":   ("var(--r1)",  "var(--r0)"),
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

def lnk_btn(label_html, href, c0, c1):
    """Button that's disabled (no href) or wrapped in <a>."""
    b = f'<button style="--c0:{c0};--c1:{c1}; width: 100%">{label_html}</button>'
    if href:
        return f'<a href="{href}" style="text-decoration:none">{b}</a>'
    return f'<button style="--c0:{c0};--c1:{c1};opacity:.3" disabled>{label_html}</button>'

def article_page(title, body_html, section_id):
    c0, c1 = CONTENT_C[section_id]
    back_btn = f'<button style="--c0:{c0};--c1:{c1}"><nz-icon name="direction" rotate="180"></nz-icon></button>'
    return (
        f'<!doctype html><html lang="en"><head>'
        f'<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>'
        f'<title>{title} — doromiert</title>'
        f'<link rel="icon" type="image/svg+xml" href="/doromiert.svg"/>'
        f'<style>{(PROJ / "src" / "base.css").read_text()}</style>'
        f'<style>:root{{--c0:{c0};--c1:{c1}}}'
        f'body{{margin:0;padding:0;background:var(--c0);color:var(--c1);'
        f'min-height:100vh;display:flex;flex-direction:column;align-items:center}}'
        f'</style>'
        f'</head><body>'
        f'<a class="page-back" href="/">{back_btn}</a>'
        f'{body_html}'
        f'</body></html>'
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
        title    = meta.get("title", f.stem)
        subtitle = meta.get("subtitle", "")
        icon     = meta.get("icon", "docs")
        tags     = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
        ext_url  = meta.get("url", "")
        href     = ext_url or f"/lib/{f.stem}.html"
        tag_html = "".join(f'<span class="tag">{t}</span>' for t in tags)
        cards.append(
            f'<a class="card" href="{href}">'
            f'<nz-icon name="{icon}" size="32"></nz-icon>'
            f'<b>{title}</b>'
            f'{"<div class=tags>" + tag_html + "</div>" if tag_html else ""}'
            f'</a>'
        )
        if not ext_url:
            art_tags = "".join(f'<span class="art-tag">{t}</span>' for t in tags)
            body_html = (
                f'<div class="art-header">'
                f'<nz-icon name="{icon}" size="64"></nz-icon>'
                f'<b style="font-size:24px">{title}</b>'
                f'{"<span class=art-subtitle>" + subtitle + "</span>" if subtitle else ""}'
                f'{"<div class=art-tags>" + art_tags + "</div>" if art_tags else ""}'
                f'</div>'
                f'<article>{mdlib.markdown(body)}</article>'
            )
            (out / f"{f.stem}.html").write_text(compile_page(article_page(title, body_html, "lib")))
    return f'<div class="card-grid">{"".join(cards)}</div>'

# --- blog ---

def build_blog():
    src = PROJ / "data" / "blog"
    if not src.exists():
        return ""
    c0, c1 = CONTENT_C["blog"]
    out = DIST / "blog"
    out.mkdir(parents=True, exist_ok=True)
    posts = [(f.stem, *parse_frontmatter(f.read_text())) for f in sorted(src.glob("*.md"), reverse=True)]
    if not posts:
        return ""
    total = len(posts)

    # Individual post pages
    for i, (slug, meta, body) in enumerate(posts):
        date     = meta.get("date", slug)
        prev_url = f"/blog/{posts[i + 1][0]}.html" if i + 1 < total else ""
        next_url = f"/blog/{posts[i - 1][0]}.html" if i > 0 else ""
        body_html = (
            f'<div class="art-header"><b style="font-size:18px">{date} ({i + 1}/{total})</b></div>'
            f'<article>{mdlib.markdown(body)}</article>'
            f'<div class="post-nav">'
            f'{lnk_btn("<nz-icon name=\"direction\" rotate=\"180\"></nz-icon>", prev_url, c0, c1)}'
            f'{lnk_btn("<nz-icon name=\"calendar\"></nz-icon><span>Browse by date</span>", "/blog/", c0, c1)}'
            f'{lnk_btn("<nz-icon name=\"direction\"></nz-icon>", next_url, c0, c1)}'
            f'</div>'
        )
        (out / f"{slug}.html").write_text(compile_page(article_page(date, body_html, "blog")))

    # Date index page /blog/index.html
    date_btns = "".join(
        lnk_btn(meta.get("date", slug), f"/blog/{slug}.html", c0, c1)
        for slug, meta, _ in posts
    )
    index_body = (
        f'<div class="art-header">'
        f'<nz-icon name="calendar" size="64"></nz-icon>'
        f'<b style="font-size:20px">All posts</b>'
        f'</div>'
        f'<div class="card-grid" style="max-width:600px">{date_btns}</div>'
        f'<style>body{{padding: 0px 20px}}</style>'
    )

    (out / "index.html").write_text(compile_page(article_page("Blog", index_body, "blog")))

    # Inline snippet for index.html — latest post only
    slug, meta, body = posts[0]
    date = meta.get("date", slug)
    prev_url = f"/blog/{posts[1][0]}.html" if total > 1 else ""
    return (
        f'<b style="font-size:18px">{date} (1/{total})</b>'
        f'<div class="blog-body">{mdlib.markdown(body)}</div>'
        f'<div class="post-nav">'
        f'{lnk_btn("<nz-icon name=\"direction\" rotate=\"180\"></nz-icon>", prev_url, c0, c1)}'
        f'{lnk_btn("<nz-icon name=\"calendar\"></nz-icon><span>Browse by date</span>", "/blog/", c0, c1)}'
        f'</div>'
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
            title    = meta.get("title", slug)
            icon     = meta.get("icon", "docs")
            tags     = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
            art_tags = "".join(f'<span class="art-tag">{t}</span>' for t in tags)
            body_html = (
                f'<div class="art-header">'
                f'<nz-icon name="{icon}" size="64"></nz-icon>'
                f'<b style="font-size:24px">{title}</b>'
                f'{"<div class=art-tags>" + art_tags + "</div>" if art_tags else ""}'
                f'</div>'
                f'<article>{mdlib.markdown(body)}</article>'
            )
            (out / f"{slug}.html").write_text(compile_page(article_page(title, body_html, section_id)))

    # "Now listening to" widget for music
    now_html = ""
    if section_id == "music":
        nf = src / "_now.txt"
        if nf.exists():
            lines = nf.read_text().strip().splitlines()
            song   = lines[0] if lines else ""
            artist = lines[1] if len(lines) > 1 else ""
            now_html = (
                f'<div class="now-playing">'
                f'<div class="np-label"><nz-icon name="headphones"></nz-icon>Now listening to</div>'
                f'<span class="np-song" style="margin-left: 4px;">{song}</span>'
                f'<span style="margin-left: 4px;">{artist}</span>'
                f'</div>'
            )

    # Category groups
    groups = "".join(
        f'<div class="cat-group">'
        f'<div class="cat-header">{cat}</div>'
        f'<div class="cat-rows">'
        + "".join(
            f'<a class="cat-item" href="/{section_id}/{slug}.html">'
            f'<nz-icon name="{meta.get("icon", "docs")}"></nz-icon>'
            f'<span>{meta.get("title", slug)}</span>'
            f'<nz-icon name="direction"></nz-icon>'
            f'</a>'
            for slug, meta, _ in items
        )
        + f'</div></div>'
        for cat, items in cats.items()
    )
    return now_html + f'<div class="cat-list">{groups}</div>'


def inject_section(html, section_id, content):
    """Inject content into empty <nz-section id="X" ...></nz-section>."""
    def rep(m):
        if f'id="{section_id}"' in m.group(0):
            return m.group(0).replace("></nz-section>", f">{content}</nz-section>", 1)
        return m.group(0)
    return re.sub(r'<nz-section[^>]*></nz-section>', rep, html)

def build():
    optimize_fonts()
    DIST.mkdir(exist_ok=True); BIZ.mkdir(parents=True, exist_ok=True)
    (DIST / "CNAME").write_text("doromiert.neg-zero.com")
    base_css = (PROJ / "src" / "base.css").read_text() if (PROJ / "src" / "base.css").exists() else ""
    l, b, d, m = build_lib(), build_blog(), build_category("devices"), build_category("music")

    def compile_standard_page(raw, vt_name):
        html = re.sub(r'<link[^>]*href="[^"]*base\.css"[^>]*>', f'<style>{base_css}</style>', raw)
        html = inject_section(inject_section(inject_section(inject_section(html, "lib", l), "blog", b), "devices", d), "music", m)
        html = compile_elements(html)
        html = inline_svgs(html)
        html = html.replace("</style>", generate_icon_css() + "</style>", 1)
        # inject the transition name into the body
        html = re.sub(r'<body([^>]*)>', rf'<body\1 style="view-transition-name: {vt_name}">', html)
        return html

    if (MAIN / "index.html").exists():
        (DIST / "index.html").write_text(compile_standard_page((MAIN / "index.html").read_text(), "page-main"))

    for f in BIZ.rglob("*"):
        if f.is_file():
            out = DIST / "business" / f.relative_to(BIZ)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(compile_standard_page(f.read_text(), "page-biz")) if f.suffix == ".html" else shutil.copy(f, out)

    for asset in ["icons.svg", "doromiert-znak", "doromiert-bold.svg", "doromiert.svg", "fonts"]:
        src = DATA / asset
        if src.exists(): shutil.copytree(src, DIST / asset, dirs_exist_ok=True) if src.is_dir() else shutil.copy(src, DIST / asset)

    for f in DIST.rglob("*.html"):
        with open(f, "rb") as fi, gzip.open(str(f) + ".gz", "wb", compresslevel=9) as fo: fo.write(fi.read())
    print("build complete.")

if __name__ == "__main__": build()
