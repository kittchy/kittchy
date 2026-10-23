"""プロフィール README 用の SVG を生成するスクリプト。

kittchy-blog のデザインシステム（old wood / grayish white / turquoise、Archivo）に合わせて、
ヘッダー・Skills・Career の SVG をライト用とダーク用の2枚ずつ、リンクボタンの SVG を1枚ずつ
assets/ に書き出す。
カードは横幅を狭め（ヘッダー 400px、Skills / Career 376px）、README では横に並べる。
画面が狭いと自然に縦に積まれるので、スマホでも縮小されずに読める。
文字はアウトライン（path）にして埋め込むので、表示側にフォントが無くても崩れない。
動きは SVG 内の CSS アニメーションで付け、prefers-reduced-motion では止める。

使い方:
    python scripts/build_svgs.py <Archivo の woff2 が入ったディレクトリ>

woff2 は npm の @fontsource/archivo に入っている archivo-latin-{400,600,700}-normal.woff2 を使う。
"""

import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
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

LINKS = ["Blog", "X", "LinkedIn", "Wantedly", "Instagram"]

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
    ("2024 — 2026", "MIXI", "ML Engineer", False),
    ("2022 — 2025", "Poetics", "ML Engineer (side job)", False),
    (
        "2022 — 2024",
        "Toyohashi Univ. of Technology",
        "M.Eng., speech recognition",
        False,
    ),
]

CERTS = [
    "CKAD",
    "AWS Certified ML Engineer – Associate",
]

# 共通の動き。読み込み時にふわっと出す・ドラムのように跳ねる・現在地のドットが脈打つ。
MOTION = (
    ".in{animation:in .7s cubic-bezier(.2,.7,.2,1) both}"
    "@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
    ".beat{transform-box:fill-box;transform-origin:50% 100%;animation:beat 1.2s ease-in-out infinite}"
    "@keyframes beat{0%,100%{transform:scaleY(.3)}25%{transform:scaleY(1)}50%{transform:scaleY(.55)}}"
    ".pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2.4s ease-out infinite}"
    "@keyframes pulse{0%{opacity:.6;transform:scale(1)}100%{opacity:0;transform:scale(2.6)}}"
    ".draw{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 1.4s ease-out .2s forwards}"
    "@keyframes draw{to{stroke-dashoffset:0}}"
    "@media (prefers-reduced-motion:reduce){.in,.beat,.pulse,.draw{animation:none}"
    ".draw{stroke-dashoffset:0}}"
)


class Font:
    """woff2 から文字幅を測り、文字列を SVG の path に変換する。"""

    def __init__(self, path: Path):
        font = TTFont(path)
        self.upm = font["head"].unitsPerEm
        self.cmap = font.getBestCmap()
        self.hmtx = font["hmtx"]
        self.glyphs = font.getGlyphSet()

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        units = 0
        for ch in text:
            glyph = self.cmap.get(ord(ch), ".notdef")
            units += self.hmtx[glyph][0]
        return units / self.upm * size + tracking * size * len(text)

    def path(self, text: str, x: float, y: float, size: float, tracking: float) -> str:
        """ベースライン (x, y) から文字列を描いた path の d 属性を返す。"""
        scale = size / self.upm
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
        for ch in text:
            glyph = self.cmap.get(ord(ch), ".notdef")
            self.glyphs[glyph].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
            x += self.hmtx[glyph][0] * scale + tracking * size
        return pen.getCommands()


FONTS: dict[int, Font] = {}


def wrap(text: str, size: float, max_width: float) -> list[str]:
    lines, cur = [], ""
    for word in text.split(" "):
        trial = f"{cur} {word}".strip()
        if cur and FONTS[400].width(trial, size) > max_width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def svg(width: int, height: int, body: str, t: dict | None) -> str:
    panel = ""
    if t:
        panel = (
            f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="18" '
            f'fill="{t["panel"]}" stroke="{t["border"]}"/>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}"><style>{MOTION}</style>{panel}{body}</svg>'
    )


def text(x, y, s, size, weight, fill, tracking=0.0, anchor="start") -> str:
    font = FONTS[weight]
    if anchor == "middle":
        x -= font.width(s, size, tracking) / 2
    return f'<path d="{font.path(s, x, y, size, tracking)}" fill="{fill}"/>'


def group(body: str, delay: float) -> str:
    """読み込み時に delay 秒遅れてふわっと出るまとまり。"""
    return f'<g class="in" style="animation-delay:{delay:.2f}s">{body}</g>'


def label(x, y, s, t) -> str:
    """ブログのラベル（大文字・字間 .14em）と、左のターコイズのドット。"""
    return f'<circle cx="{x + 4}" cy="{y - 5}" r="4" fill="{t["accent"]}"/>' + text(
        x + 18, y, s, 13, 600, t["muted"], tracking=0.14
    )


def beat_bars(x, y, t) -> str:
    """ドラムのリズムのように跳ねる5本のバー。y は下端。"""
    out = ""
    for i, delay in enumerate([0, 0.3, 0.15, 0.45, 0.6]):
        out += (
            f'<rect class="beat" style="animation-delay:-{delay}s" x="{x + i * 9}" '
            f'y="{y - 22}" width="5" height="22" rx="2.5" fill="{t["accent"]}"/>'
        )
    return out


def header(t) -> str:
    w, pad = 400, 32
    body = group(label(pad, pad + 16, "AI / ML ENGINEER · TOKYO", t), 0)
    body += beat_bars(w - pad - 41, pad + 18, t)
    name = text(pad, pad + 70, "Takahiro Kinouchi", 40, 700, t["text"], tracking=-0.03)
    body += group(name, 0.1)
    y = pad + 108
    for i, para in enumerate(INTRO):
        lines = ""
        for line in wrap(para, 16, w - pad * 2):
            lines += text(pad, y, line, 16, 400, t["secondary"])
            y += 27
        body += group(lines, 0.25 + i * 0.15)
        if i < len(INTRO) - 1:
            y += 9
    return svg(w, int(y - 27 + pad + 6), body, t)


def link_button(name: str) -> str:
    """ブログのプライマリボタン（ターコイズの面・白文字・ピル・右矢印）。両テーマ共通。

    Archivo の latin サブセットに → が無いので、矢印は線で描く。
    """
    size, h, arrow, gap = 16, 40, 12, 8
    tw = FONTS[600].width(name, size)
    w = int(tw + gap + arrow + 40)
    x = (w - tw - gap - arrow) / 2
    body = f'<rect width="{w}" height="{h}" rx="20" fill="#237C85"/>'
    body += text(x, 26, name, size, 600, "#FFFFFF")
    ax = x + tw + gap
    body += (
        f'<path d="M{ax:.1f} 20H{ax + arrow:.1f}M{ax + arrow - 4.5:.1f} 15.5L{ax + arrow:.1f} 20'
        f'L{ax + arrow - 4.5:.1f} 24.5" fill="none" stroke="#FFFFFF" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
    )
    return svg(w, h, group(body, 0.4), None)


def skills(t) -> str:
    w, pad = 376, 32
    body = group(label(pad, pad + 16, "SKILLS", t), 0)
    y = pad + 48
    n = 0
    for cat, items in SKILLS:
        body += group(text(pad, y, cat, 12, 600, t["muted"], tracking=0.14), 0.1)
        y += 14
        x = pad
        for item in items:
            pw = FONTS[400].width(item, 15) + 28
            if x + pw > w - pad:
                x = pad
                y += 42
            pill = (
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{pw:.1f}" height="34" rx="17" '
                f'fill="{t["card"]}" stroke="{t["border"]}"/>'
            )
            pill += text(
                x + pw / 2, y + 22.5, item, 15, 400, t["text"], anchor="middle"
            )
            body += group(pill, 0.15 + n * 0.04)
            n += 1
            x += pw + 7
        y += 34 + 30
    return svg(w, int(y - 30 + pad - 4), body, t)


def career(t) -> str:
    w, pad = 376, 32
    body = group(label(pad, pad + 16, "CAREER", t), 0)
    y0 = pad + 56
    step = 76
    line_x = pad + 6
    tx = pad + 28
    body += (
        f'<line class="draw" pathLength="1" x1="{line_x}" y1="{y0 + 14}" x2="{line_x}" '
        f'y2="{y0 + step * (len(CAREER) - 1) + 14}" stroke="{t["rule"]}" stroke-width="1.5"/>'
    )
    for i, (period, org, role, current) in enumerate(CAREER):
        y = y0 + step * i
        cy = y + 14
        item = text(tx, y, period, 12, 600, t["muted"], tracking=0.08)
        if current:
            body += f'<circle class="pulse" cx="{line_x}" cy="{cy}" r="6" fill="{t["accent"]}"/>'
            item += f'<circle cx="{line_x}" cy="{cy}" r="6" fill="{t["accent"]}"/>'
        else:
            item += (
                f'<circle cx="{line_x}" cy="{cy}" r="5" fill="{t["panel"]}" '
                f'stroke="{t["muted"]}" stroke-width="1.5"/>'
            )
        item += text(tx, y + 22, org, 17, 600, t["text"])
        item += text(tx, y + 43, role, 14, 400, t["secondary"])
        body += group(item, 0.2 + i * 0.15)
    y = y0 + step * len(CAREER) + 4
    certs = (
        f'<line x1="{pad}" y1="{y - 18}" x2="{w - pad}" y2="{y - 18}" '
        f'stroke="{t["rule"]}" stroke-dasharray="3 4"/>'
    )
    certs += label(pad, y + 14, "CERTIFICATIONS", t)
    for j, cert in enumerate(CERTS):
        certs += text(tx, y + 44 + j * 26, cert, 15, 400, t["text"])
    body += group(certs, 0.9)
    return svg(w, int(y + 44 + 26 * (len(CERTS) - 1) + pad - 4), body, t)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(
            "usage: python scripts/build_svgs.py <Archivo の woff2 が入ったディレクトリ>"
        )
    font_dir = Path(sys.argv[1])
    for weight in (400, 600, 700):
        FONTS[weight] = Font(font_dir / f"archivo-latin-{weight}-normal.woff2")
    OUT.mkdir(exist_ok=True)
    for name, t in THEMES.items():
        for part, build in (("header", header), ("skills", skills), ("career", career)):
            (OUT / f"{part}-{name}.svg").write_text(build(t), encoding="utf-8")
    for name in LINKS:
        (OUT / f"link-{name.lower()}.svg").write_text(
            link_button(name), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
