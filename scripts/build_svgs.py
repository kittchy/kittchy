"""プロフィール README 用の SVG を生成するスクリプト。

kittchy-blog のデザインシステム（old wood / grayish white / turquoise、Archivo）に合わせて、
ヘッダー・Skills・Career の SVG をライト用とダーク用の2枚ずつ assets/ に書き出す。

使い方:
    python scripts/build_svgs.py <Archivo の woff2 が入ったディレクトリ>

woff2 は npm の @fontsource/archivo に入っている archivo-latin-{400,600,700}-normal.woff2 を使う。
"""

import base64
import sys
from html import escape
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

THEMES = {
    "light": {
        "panel": "#F0EFF0",
        "card": "#FFFFFF",
        "border": "#E3E2E1",
        "text": "#2F2F28",
        "secondary": "#5E5E54",
        "muted": "#6E6E64",
        "rule": "#D6D6CE",
        "accent": "#31A2AC",
    },
    "dark": {
        "panel": "#1A1A16",
        "card": "#22221D",
        "border": "#34342D",
        "text": "#F0EFF0",
        "secondary": "#C7C6C1",
        "muted": "#9C9B93",
        "rule": "#4A4A41",
        "accent": "#4FC3CD",
    },
}

INTRO = [
    "Hi, I'm Takahiro Kinouchi (@kittchy). I work as an AI/ML engineer.",
    (
        "At university I researched speech recognition. Since then I've built "
        "natural language processing, image processing, recommendation, and image search systems."
    ),
    "I play the drums, and I like walking around cities I don't know.",
]

SKILLS = [
    ("LANGUAGES", ["Python", "Rust", "C#", "TypeScript", "C", "Java", "Ruby"]),
    (
        "FRAMEWORKS",
        [
            "PyTorch",
            "ONNX",
            "OpenVINO",
            "LiteRT (TFLite)",
            "FastAPI",
            "gRPC",
            "Ruby on Rails",
        ],
    ),
    (
        "INFRA & TOOLS",
        ["AWS", "GCP", "Terraform", "Kubernetes", "Docker", "Helm", "ArgoCD"],
    ),
]

CAREER = [
    ("2026 —", "Knowledge Work", "AI Engineer", True),
    (
        "2024 — 2026",
        "MIXI",
        "ML Engineer · person albums, recommendation, image search",
        False,
    ),
    (
        "2022 — 2025",
        "Poetics",
        "ML Engineer (side job) · speech recognition, VAD",
        False,
    ),
    (
        "2022 — 2024",
        "Toyohashi University of Technology",
        "M.Eng. · domain adaptation of speech recognition",
        False,
    ),
]

CERTS = [
    "Certified Kubernetes Application Developer (CKAD)",
    "AWS Certified Machine Learning Engineer – Associate",
]


class Font:
    """woff2 から文字幅を測り、SVG に埋め込む @font-face を作る。"""

    def __init__(self, path: Path, weight: int):
        self.weight = weight
        self.data = path.read_bytes()
        font = TTFont(path)
        self.upm = font["head"].unitsPerEm
        self.cmap = font.getBestCmap()
        self.hmtx = font["hmtx"]

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        units = 0
        for ch in text:
            glyph = self.cmap.get(ord(ch), ".notdef")
            units += self.hmtx[glyph][0]
        return units / self.upm * size + tracking * size * len(text)

    def face(self) -> str:
        b64 = base64.b64encode(self.data).decode()
        return (
            f"@font-face{{font-family:'Archivo';font-weight:{self.weight};"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
        )


def wrap(font: Font, text: str, size: float, max_width: float) -> list[str]:
    lines, cur = [], ""
    for word in text.split(" "):
        trial = f"{cur} {word}".strip()
        if cur and font.width(trial, size) > max_width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def svg(width: int, height: int, fonts: list[Font], body: str, t: dict) -> str:
    style = "".join(f.face() for f in fonts)
    style += "text{font-family:'Archivo','Helvetica Neue',Arial,sans-serif;}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f"<style>{style}</style>"
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="18" '
        f'fill="{t["panel"]}" stroke="{t["border"]}"/>'
        f"{body}</svg>"
    )


def text(x, y, s, size, weight, fill, tracking=0.0, anchor="start") -> str:
    ls = f' letter-spacing="{tracking * size:.2f}"' if tracking else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}"{ls} text-anchor="{anchor}">{escape(s)}</text>'
    )


def label(x, y, s, t, f600) -> str:
    """ブログのラベル（大文字・11px・字間 .14em）と、左のターコイズのドット。"""
    return f'<circle cx="{x + 3}" cy="{y - 4}" r="3" fill="{t["accent"]}"/>' + text(
        x + 14, y, s, 11, 600, t["muted"], tracking=0.14
    )


def header(t, f400, f600, f700) -> str:
    w, pad = 480, 32
    body = label(pad, pad + 14, "AI / ML ENGINEER  ·  TOKYO", t, f600)
    body += text(pad, pad + 64, "Takahiro Kinouchi", 38, 700, t["text"], tracking=-0.03)
    y = pad + 102
    for i, para in enumerate(INTRO):
        for line in wrap(f400, para, 14, w - pad * 2):
            body += text(pad, y, line, 14, 400, t["secondary"])
            y += 24
        if i < len(INTRO) - 1:
            y += 8
    return svg(w, int(y - 24 + pad + 4), [f400, f600, f700], body, t)


def skills(t, f400, f600) -> str:
    w, pad, col = 840, 32, 150
    body = label(pad, pad + 14, "SKILLS", t, f600)
    y = pad + 44
    for cat, items in SKILLS:
        x = pad + col
        body += text(pad, y + 19, cat, 11, 600, t["muted"], tracking=0.14)
        for item in items:
            pw = f400.width(item, 13) + 28
            if x + pw > w - pad:
                x = pad + col
                y += 40
            body += (
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{pw:.1f}" height="30" rx="15" '
                f'fill="{t["card"]}" stroke="{t["border"]}"/>'
            )
            body += text(
                x + pw / 2, y + 19.5, item, 13, 400, t["text"], anchor="middle"
            )
            x += pw + 8
        y += 46
    return svg(w, int(y - 16 + pad), [f400, f600], body, t)


def career(t, f400, f600) -> str:
    w, pad, col = 840, 32, 150
    body = label(pad, pad + 14, "CAREER", t, f600)
    y0 = pad + 50
    step = 54
    line_x = pad + col - 18
    body += (
        f'<line x1="{line_x}" y1="{y0 - 4}" x2="{line_x}" y2="{y0 + step * (len(CAREER) - 1) - 4}" '
        f'stroke="{t["rule"]}"/>'
    )
    for i, (period, org, role, current) in enumerate(CAREER):
        y = y0 + step * i
        body += text(pad, y, period, 11, 600, t["muted"], tracking=0.08)
        if current:
            body += f'<circle cx="{line_x}" cy="{y - 4}" r="5" fill="{t["accent"]}"/>'
        else:
            body += (
                f'<circle cx="{line_x}" cy="{y - 4}" r="4.5" fill="{t["panel"]}" '
                f'stroke="{t["muted"]}" stroke-width="1.5"/>'
            )
        body += text(pad + col, y, org, 15, 600, t["text"])
        body += text(pad + col, y + 20, role, 13, 400, t["secondary"])
    y = y0 + step * len(CAREER) + 6
    body += f'<line x1="{pad}" y1="{y - 22}" x2="{w - pad}" y2="{y - 22}" stroke="{t["rule"]}" stroke-dasharray="3 4"/>'
    body += label(pad, y + 4, "CERTIFICATION", t, f600)
    for j, cert in enumerate(CERTS):
        body += text(pad + col, y + 4 + j * 24, cert, 14, 400, t["text"])
    return svg(w, int(y + 4 + 24 * (len(CERTS) - 1) + pad), [f400, f600], body, t)


def main() -> None:
    font_dir = Path(sys.argv[1])
    f400 = Font(font_dir / "archivo-latin-400-normal.woff2", 400)
    f600 = Font(font_dir / "archivo-latin-600-normal.woff2", 600)
    f700 = Font(font_dir / "archivo-latin-700-normal.woff2", 700)
    OUT.mkdir(exist_ok=True)
    for name, t in THEMES.items():
        (OUT / f"header-{name}.svg").write_text(header(t, f400, f600, f700))
        (OUT / f"skills-{name}.svg").write_text(skills(t, f400, f600))
        (OUT / f"career-{name}.svg").write_text(career(t, f400, f600))


if __name__ == "__main__":
    main()
