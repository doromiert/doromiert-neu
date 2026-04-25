#!/usr/bin/env python3
import re
import gzip
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"

icons = (ROOT / "icons.txt").read_text().strip().split("\n")
total = len(icons)
sprite_width = total * 24

# --- generate icon CSS ---
css = (
    f".nz-icon{{display:inline-block;width:24px;height:24px;"
    f"background-color:currentColor;"
    f"mask-image:url('icons.svg');mask-size:{sprite_width}px 24px;"
    f"-webkit-mask-image:url('icons.svg');-webkit-mask-size:{sprite_width}px 24px}}"
)
for i, name in enumerate(icons):
    offset = i * 24
    css += f".nz-icon-{name}{{mask-position:-{offset}px 0;-webkit-mask-position:-{offset}px 0}}"

# --- process HTML ---
html = (ROOT / "index.html").read_text()

# replace <nz-icon name="X">...</nz-icon> and <nz-icon name="X"/>
html = re.sub(
    r'<nz-icon name="([^"]+)"[^>]*>.*?</nz-icon>',
    lambda m: f'<span class="nz-icon nz-icon-{m.group(1)}"></span>',
    html, flags=re.DOTALL
)
html = re.sub(
    r'<nz-icon name="([^"]+)"[^>]*/?>',
    lambda m: f'<span class="nz-icon nz-icon-{m.group(1)}"></span>',
    html
)

# inject icon CSS right before </style>
html = html.replace("</style>", css + "\n    </style>", 1)

# --- write dist ---
DIST.mkdir(exist_ok=True)
out = DIST / "index.html"
out.write_text(html)

# copy static assets
for asset in ["icons.svg", "doromiert.svg"]:
    src = ROOT / asset
    if src.exists():
        shutil.copy(src, DIST / asset)

# gzip for size reference
with open(out, "rb") as f_in, gzip.open(str(out) + ".gz", "wb", compresslevel=9) as f_out:
    f_out.write(f_in.read())

raw = out.stat().st_size
gz = (Path(str(out) + ".gz")).stat().st_size
print(f"built  {raw:,}b raw  |  {gz:,}b gzip  ({total} icons)")
