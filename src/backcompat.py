import re
import sys
from pathlib import Path


def extract_root_vars(css_text: str) -> dict:
    """
    grabs all the variables from :root so we can violently inject them
    everywhere else as static values.
    """
    vars_dict = {}
    root_match = re.search(r":root\s*\{([^}]+)\}", css_text)
    if root_match:
        for line in root_match.group(1).splitlines():
            if ":" in line and "--" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    vars_dict[parts[0].strip()] = parts[1].strip().rstrip(";")
    return vars_dict


def inject_viewport_fallbacks(css_text: str) -> str:
    """
    automatically duplicates lines with modern viewport units (lvh, svh, dvh)
    and replaces them with standard 'vh' for backwards compatibility.
    """
    out_lines = []
    for line in css_text.splitlines():
        if re.search(r"\b\d+(lvh|svh|dvh)\b", line):
            fallback_line = re.sub(r"(\b\d+)(lvh|svh|dvh)\b", r"\g<1>vh", line)
            out_lines.append(fallback_line)
        out_lines.append(line)
    return "\n".join(out_lines)


def inject_variable_fallbacks(text_content: str, global_vars: dict) -> str:
    """
    violently replaces every instance of var(--x) with its static hex value.
    no fallbacks. no mercy. the wii u demands a blood sacrifice.
    """
    # sort by length so --c10 is replaced before --c1, preventing partial match bugs
    sorted_vars = sorted(global_vars.keys(), key=len, reverse=True)

    for v_name in sorted_vars:
        text_content = text_content.replace(f"var({v_name})", global_vars[v_name])

    return text_content


def process_css_text(raw_css: str, global_vars: dict) -> str:
    """
    the core unroller pipeline for any chunk of css.
    """
    try:
        import sass
    except ImportError:
        print(
            "yo, you need libsass to unroll modern css properly. run: pip install libsass"
        )
        sys.exit(1)

    # yank view-transitions temporarily so libsass doesn't panic
    view_transitions = ""
    vt_match = re.search(r"@view-transition\s*\{[^}]+\}", raw_css)
    if vt_match:
        view_transitions = vt_match.group(0)
        raw_css = raw_css.replace(view_transitions, "")

    try:
        flat_css = sass.compile(string=raw_css, output_style="expanded")
    except sass.CompileError as e:
        print(f"css compile error: {e}")
        flat_css = raw_css  # fallback to raw on failure

    flat_css = inject_viewport_fallbacks(flat_css)
    flat_css = inject_variable_fallbacks(flat_css, global_vars)

    if view_transitions:
        flat_css += f"\n\n/* preserved bleeding-edge rules */\n{view_transitions}\n"

    return flat_css


def compile_compatible_css(src_path: Path, dest_path: Path, global_vars: dict):
    print(f"flattening css file: {src_path.name}...")
    raw_css = src_path.read_text(encoding="utf-8")
    final_css = process_css_text(raw_css, global_vars)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(final_css, encoding="utf-8")


def compile_html_file(src_path: Path, dest_path: Path, global_vars: dict):
    print(f"flattening html file: {src_path.name}...")
    html_text = src_path.read_text(encoding="utf-8")

    # 1. unroll nested css inside <style> tags
    def style_replacer(match):
        start_tag = match.group(1)
        raw_css = match.group(2)
        end_tag = match.group(3)
        flat_css = process_css_text(raw_css, global_vars)
        return f"{start_tag}\n{flat_css}\n{end_tag}"

    html_text = re.sub(
        r"(<style[^>]*>)(.*?)(</style>)",
        style_replacer,
        html_text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # 2. brutally replace all remaining variables globally across the whole html file
    # this catches inline styles, custom component attributes, and anything else the regex missed
    html_text = inject_variable_fallbacks(html_text, global_vars)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(html_text, encoding="utf-8")


# --- EXECUTION HOOK ---
if __name__ == "__main__":
    PROJ = Path(__file__).parent.parent
    SRC = PROJ / "src"
    DIST = PROJ / "dist"

    base_css_src = SRC / "base.css"
    base_css_dest = DIST / "base.css"

    global_vars = {}

    # parse base.css first to extract the global dictionary
    if base_css_src.exists():
        global_vars = extract_root_vars(base_css_src.read_text(encoding="utf-8"))
        compile_compatible_css(base_css_src, base_css_dest, global_vars)
    else:
        print(f"couldn't find {base_css_src}, proceeding without global vars.")

    # rip through all html files and unroll their styles
    for html_src in SRC.rglob("*.html"):
        html_dest = DIST / html_src.relative_to(SRC)
        compile_html_file(html_src, html_dest, global_vars)

    print("\n✅ everything compiled, unrolled, and violently wii-u-proofed.")
