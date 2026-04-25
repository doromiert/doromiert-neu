#!/usr/bin/env python3
import re, gzip, shutil
import markdown as mdlib
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"

# =============================================================================
# CUSTOM ELEMENTS
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

ELEMENTS = [NzIcon, NavButton, Separator, NzSection]

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
                inner = re.search(rf'<{el.tag}[^>]*>(.*?)</{el.tag}>', raw, re.DOTALL)
                kwargs["inner"] = inner.group(1).strip() if inner else ""
                return el.render(**kwargs)
            html = re.sub(rf'<{el.tag}[^>]*>.*?</{el.tag}>|<{el.tag}[^>]*/?>',
                          replacer, html, flags=re.DOTALL)
        if html == prev:
            break
    return html

# =============================================================================
# ICON SPRITE CSS
# =============================================================================

def generate_icon_css(icon_path="icons.svg"):
    icons = (ROOT / "icons.txt").read_text().strip().split("\n")
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

# =============================================================================
# INLINE SVGS
# =============================================================================

def inline_svgs(html):
    def replacer(m):
        src, style = m.group(1), m.group(2)
        path = ROOT / src
        if not path.exists():
            return m.group(0)
        svg = path.read_text()
        if style:
            svg = re.sub(r'<svg', f'<svg style="{style}"', svg, count=1)
        return svg
    return re.sub(r'<img\s+src="([^"]+\.svg)"[^>]*style="([^"]*)"[^>]*/>', replacer, html)

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

# Shared component CSS — injected into both index.html and article pages
COMPONENT_CSS = (
    ".card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:2px;width:100%;max-width:800px}"
    ".card{display:flex;flex-direction:column;align-items:center;gap:8px;padding:16px;"
    "background:color-mix(in srgb,var(--c1) 10%,transparent);color:var(--c1);"
    "text-decoration:none;outline:2px solid color-mix(in srgb,var(--c1) 25%,transparent);"
    "transition:all .15s;text-align:center}"
    ".card:hover{background:color-mix(in srgb,var(--c1) 20%,transparent);outline-width:5px}"
    ".card .tags{display:flex;flex-wrap:wrap;gap:4px;justify-content:center}"
    ".card .tag{font-size:11px;padding:1px 6px;background:color-mix(in srgb,var(--c1) 20%,transparent)}"
    ".cat-list{width:100%;max-width:700px;display:flex;flex-direction:column;gap:20px}"
    ".cat-group{display:flex;flex-direction:column;gap:6px}"
    ".cat-header{font-size:13px;opacity:.6;display:flex;align-items:center;gap:8px;padding:0 2px}"
    ".cat-header::after{content:'';flex:1;height:1px;background:currentColor;opacity:.3}"
    ".cat-rows{display:grid;grid-template-columns:1fr 1fr;gap:2px}"
    ".cat-item{display:flex;align-items:center;gap:8px;padding:10px 12px;"
    "background:color-mix(in srgb,var(--c1) 10%,transparent);color:var(--c1);"
    "text-decoration:none;transition:background .15s}"
    ".cat-item:hover{background:color-mix(in srgb,var(--c1) 20%,transparent)}"
    ".cat-item .nz-icon:last-child{margin-left:auto;opacity:.5}"
    ".now-playing{display:flex;flex-direction:column;align-items:center;gap:2px;padding:14px 24px;"
    "background:color-mix(in srgb,var(--c1) 15%,transparent);"
    "outline:1px solid color-mix(in srgb,var(--c1) 30%,transparent);max-width:300px}"
    ".np-label{font-size:12px;opacity:.7;display:flex;align-items:center;gap:6px}"
    ".np-song{font-weight:bold}"
    ".post-nav{display:flex;gap:10px;align-items:center;justify-content:center}"
    ".blog-body{max-width:500px;text-align:left}"
    ".art-header{display:flex;flex-direction:column;align-items:center;gap:8px;padding:60px 20px 20px}"
    ".art-subtitle{opacity:.7;font-size:14px}"
    ".art-tags{display:flex;flex-wrap:wrap;gap:4px;justify-content:center}"
    ".art-tag{font-size:12px;padding:2px 8px;background:color-mix(in srgb,var(--c1) 20%,transparent)}"
    ".page-back{position:fixed;top:20px;left:20px;z-index:10}"
    "article{max-width:600px;width:100%;padding:20px;padding-top:20px;box-sizing:border-box;text-align:left}"
    "article img{max-width:100%;display:block;margin:16px 0}"
    "article h1,article h2,article h3{margin-top:1.5em}"
)

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
    b = f'<button style="--c0:{c0};--c1:{c1}">{label_html}</button>'
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
        f'<link rel="stylesheet" href="/base.css"/>'
        f'<style>:root{{--c0:{c0};--c1:{c1}}}'
        f'body{{margin:0;padding:0;background:var(--c0);color:var(--c1);'
        f'min-height:100vh;display:flex;flex-direction:column;align-items:center}}'
        f'{COMPONENT_CSS}</style>'
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
    src = ROOT / "lib"
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
    src = ROOT / "blog"
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
    src = ROOT / section_id
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
                f'<span class="np-song">{song}</span>'
                f'<span>{artist}</span>'
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

# =============================================================================
# BUILD
# =============================================================================

def build():
    DIST.mkdir(exist_ok=True)

    html = (ROOT / "index.html").read_text()
    html = inline_svgs(html)

    # Inject content before compile_elements so nz-icon tags inside get compiled
    html = inject_section(html, "lib",     build_lib())
    html = inject_section(html, "blog",    build_blog())
    html = inject_section(html, "devices", build_category("devices"))
    html = inject_section(html, "music",   build_category("music"))

    html = compile_elements(html)
    html = html.replace("</style>", generate_icon_css() + COMPONENT_CSS + "\n    </style>", 1)

    out = DIST / "index.html"
    out.write_text(html)

    for asset in ["icons.svg", "doromiert-znak", "doromiert-bold.svg", "doromiert.svg", "base.css"]:
        src = ROOT / asset
        if not src.exists():
            continue
        if src.is_dir():
            shutil.copytree(src, DIST / asset, dirs_exist_ok=True)
        else:
            shutil.copy(src, DIST / asset)

    with open(out, "rb") as fi, gzip.open(str(out) + ".gz", "wb", compresslevel=9) as fo:
        fo.write(fi.read())

    raw = out.stat().st_size
    gz  = Path(str(out) + ".gz").stat().st_size
    print(f"built  {raw:,}b raw  |  {gz:,}b gzip")

build()
