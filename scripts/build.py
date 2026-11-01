#!/usr/bin/env python3
"""Profil README'sindeki tüm SVG görselleri üretir: python3 scripts/build.py"""
import base64
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "assets" / "brand"
PRODUCTS = BRAND / "products"
OUT = ROOT / "assets"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

THEMES = {
    "light": dict(bg="#ffffff", surface="#f6f8fa", border="#e1e5ea", ink="#0f1419",
                  muted="#57606a", faint="#8c959f", accent="#c96a06", live="#1a7f37"),
    "dark": dict(bg="#0d1117", surface="#151b23", border="#262e38", ink="#e6edf3",
                 muted="#9198a1", faint="#6e7681", accent="#f0a43a", live="#3fb950"),
}

# Koyu temada sembollerdeki koyu mürekkep renkleri açık mürekkebe çevrilir.
DARK_INKS = ["#101218", "#121620", "#1c1a17", "#0e4f55", "#16120f"]


def oklch(l, c, h):
    """OKLCH → sRGB hex (Ovokodo ürün renkleri tokens.css'te OKLCH tanımlı)."""
    a, b = c * math.cos(math.radians(h)), c * math.sin(math.radians(h))
    l_ = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (l - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
           -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
           -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)
    out = []
    for x in rgb:
        x = 12.92 * x if x <= 0.0031308 else 1.055 * max(x, 0) ** (1 / 2.4) - 0.055
        out.append(round(min(max(x, 0), 1) * 255))
    return "#%02x%02x%02x" % tuple(out)


# Ovokodo ailesi: ürün başına --ovk-hue / --ovk-chroma (products/*/resources/css).
OVO = {
    "ovokodo": (158, 0.115), "ovodock": (158, 0.115), "ovokodo-id": (158, 0.115),
    "mailkodo": (262, 0.16), "sitekodo": (225, 0.115), "ovoroom": (345, 0.115),
    "ovoloop": (50, 0.16), "ovolabs": (295, 0.12),
}


def ovo_colors(name, theme):
    if name == "ovodock":
        return "#ffffff", "#111111"
    h, c = OVO[name]
    if theme == "light":
        return oklch(0.5, c, h), oklch(0.95, c * 0.28, h)
    return oklch(0.8, c, h), oklch(0.29, c * 0.45, h)


TOOLS = {
    "relivaro": dict(
        url="https://github.com/cihantopac/relivaro",
        chip="KOD KALİTESİ · GÜVENLİK · SÜRÜM",
        accent={"light": "#0b7285", "dark": "#3fb6c6"},
        lockup_h=32,
        lines=["Kodu denetler, kanıtını gösterir;", "doğrulamadan tek satıra dokunmaz."],
        metrics=[("83", "denetim kuralı"), ("15", "güvenli düzeltici"), ("0", "sessiz “geçti”")],
        cmd="npx relivaro audit .",
    ),
    "searvex": dict(
        url="https://github.com/cihantopac/searvex",
        chip="TEKNİK SEO · GEO",
        accent={"light": "#b8432d", "dark": "#e5694f"},
        lockup_h=32,
        lines=["Google ve yapay zekâ aramaları", "sitenizi nasıl görüyor, gösterir."],
        metrics=[("90", "kural"), ("6", "framework"), ("50→1", "kök neden, tek görev")],
        cmd="searvex audit https://site.com",
    ),
    "jourilo": dict(
        url="https://github.com/cihantopac/jourilo",
        chip="UX · ERİŞİLEBİLİRLİK · DÖNÜŞÜM",
        accent={"light": "#1c1a17", "dark": "#f2efe9"},
        lockup_h=38,
        lines=["Ürününüzde gerçek tarayıcıyla", "yürür, kullanıcının takıldığını bulur."],
        metrics=[("3", "tarayıcı motoru"), ("2.2", "WCAG AA kontrolü"), ("5", "Web Vitals ölçümü")],
        cmd="jourilo audit ./dist --repo .",
    ),
    "markilo": dict(
        url="https://github.com/cihantopac/markilo",
        chip="MARKA KİMLİĞİ",
        accent={"light": "#7e1d2a", "dark": "#c5636b"},
        lockup_h=34,
        lines=["Araştırır, çizer, ölçer, dışa aktarır.", "Diğer üçünün logosunu o çizdi."],
        metrics=[("3", "öneri, seçim sizde"), ("24", "açık font ailesi"), ("0", "sunucu, ücretli API")],
        cmd="/plugin install markilo@markilo",
    ),
}
ORDER = ["relivaro", "searvex", "jourilo", "markilo"]

_uid = [0]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def embed(path, x, y, w=None, h=None, theme="light", align="xMinYMid", color=None):
    """Bir SVG dosyasını iç içe <svg> olarak yerleştirir; id'leri çakışmasın diye önekler."""
    text = path.read_text()
    vb = re.search(r'viewBox="([^"]+)"', text).group(1)
    inner = re.sub(r"^.*?<svg[^>]*>", "", text, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner)
    inner = re.sub(r"<title>.*?</title>|<!--.*?-->", "", inner, flags=re.S)
    _uid[0] += 1
    for i in set(re.findall(r'id="([^"]+)"', inner)):
        p = f"e{_uid[0]}-{i}"
        inner = inner.replace(f'id="{i}"', f'id="{p}"').replace(f"#{i}\"", f"#{p}\"").replace(f"#{i})", f"#{p})")
    if theme == "dark":
        for c in DARK_INKS:
            inner = inner.replace(f'fill="{c}"', f'fill="{THEMES["dark"]["ink"]}"')
    _, _, vw, vh = map(float, vb.split())
    if w is None:
        w = h * vw / vh
    if h is None:
        h = w * vh / vw
    col = f' color="{color}"' if color else ""
    return (f'<svg x="{x}" y="{y}" width="{w:.1f}" height="{h:.1f}" viewBox="{vb}"{col} '
            f'preserveAspectRatio="{align} meet">{inner}</svg>'), w


def png(path, x, y, w, h, extra=""):
    data = base64.b64encode(path.read_bytes()).decode()
    return (f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMinYMid meet" '
            f'href="data:image/png;base64,{data}"{extra}/>')


def style(t, extra=""):
    return f"""<style>
.sans{{font-family:{SANS}}}
.mono{{font-family:{MONO}}}
.ink{{fill:{t['ink']}}} .muted{{fill:{t['muted']}}} .faint{{fill:{t['faint']}}}
{extra}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
</style>"""


def doc(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(label)}" fill="none">{body}</svg>\n')


def ovo_tile(name, x, y, s, theme, rx=None):
    fg, bg = ovo_colors(name, theme)
    rx = rx if rx is not None else s * 0.26
    mark, _ = embed(PRODUCTS / f"ov-{name}.svg", x + s * 0.22, y + s * 0.22, w=s * 0.56, h=s * 0.56,
                    align="xMidYMid", color=fg)
    edge = ' stroke="#3a414c" stroke-width="1.5"' if name == "ovodock" and theme == "dark" else ""
    return f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{rx}" fill="{bg}"{edge}/>' + mark


def app_tile(kind, x, y, s, theme):
    """Giriş görselindeki ana ekran ızgarası için tek bir uygulama simgesi."""
    t = THEMES[theme]
    rx = s * 0.26
    clip = f"clip{x:.0f}{y:.0f}"
    if kind in OVO:
        return ovo_tile(kind, x, y, s, theme)
    if kind in TOOLS:
        sym, _ = embed(BRAND / f"{kind}-symbol.svg", x + s * 0.2, y + s * 0.2, w=s * 0.6, h=s * 0.6,
                       theme=theme, align="xMidYMid")
        return (f'<rect x="{x + .75}" y="{y + .75}" width="{s - 1.5}" height="{s - 1.5}" rx="{rx}" '
                f'fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.5"/>' + sym)
    defs = f'<clipPath id="{clip}"><rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{rx}"/></clipPath>'
    if kind == "preplay":
        return defs + png(PRODUCTS / "preplay-icon.png", x, y, s, s, f' clip-path="url(#{clip})"')
    if kind == "parkbiz":
        return (defs + f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{rx}" fill="#ffffff" '
                f'stroke="{t["border"]}" stroke-width="1.5"/>'
                + png(PRODUCTS / "parkbiz-icon.png", x + 4, y + 4, s - 8, s - 8, f' clip-path="url(#{clip})"'))
    if kind == "vaybak":
        icon, _ = embed(PRODUCTS / "vaybak-icon.svg", x, y, w=s, h=s, align="xMidYMid")
        return f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{rx}" fill="#44619A"/>' + icon
    raise ValueError(kind)


def hero(theme):
    t = THEMES[theme]
    W, H = 1200, 440
    parts = [style(t, """
.pulse{animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{50%{opacity:.25}}
""")]
    parts.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="20" fill="{t["surface"]}" stroke="{t["border"]}"/>')
    parts.append(f'<defs><pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">'
                 f'<circle cx="2" cy="2" r="1" fill="{t["border"]}"/></pattern>'
                 f'<linearGradient id="fade" x1="0" x2="1"><stop offset=".35" stop-color="#fff" stop-opacity="0"/>'
                 f'<stop offset="1" stop-color="#fff"/></linearGradient>'
                 f'<mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask></defs>')
    parts.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="20" fill="url(#dots)" mask="url(#m)"/>')

    # sol: kim, ne yapıyor
    parts.append(f'<rect x="56" y="64" width="10" height="10" rx="2" fill="{t["accent"]}"/>')
    parts.append(f'<text x="76" y="74" class="mono muted" font-size="13" letter-spacing="2.4">İSTANBUL  /  ÜRÜN GELİŞTİRİCİ</text>')
    parts.append(f'<text x="53" y="150" class="sans ink" font-size="60" font-weight="700" letter-spacing="-2">Cihan Topaç</text>')
    parts.append(f'<text x="56" y="196" class="sans muted" font-size="19">Fikirden canlıya, gerçek kullanıcıların her gün</text>')
    parts.append(f'<text x="56" y="223" class="sans muted" font-size="19">kullandığı ürünler geliştiriyorum.</text>')

    areas = [("mobile", "Mobil uygulamalar"), ("web", "Web uygulamaları · SaaS"),
             ("site", "Kurumsal web siteleri"), ("tool", "Geliştirici araçları")]
    for i, (kind, label) in enumerate(areas):
        x, y = 56 + (i % 2) * 262, 262 + (i // 2) * 56
        parts.append(f'<rect x="{x}" y="{y}" width="248" height="44" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>')
        ix, iy = x + 16, y + 12
        g = f'<g transform="translate({ix} {iy})" stroke="{t["accent"]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        g += {
            "mobile": '<rect x="4" y="0" width="12" height="20" rx="3"/><path d="M8.5 16.5h3"/>',
            "web": '<rect x="0" y="2" width="20" height="16" rx="3"/><path d="M0 7h20M3.5 4.5h.01M6 4.5h.01"/>',
            "site": '<path d="M2 18V7l8-5 8 5v11zM7 18v-6h6v6"/>',
            "tool": '<path d="M7 5L1 10l6 5M13 5l6 5-6 5"/>',
        }[kind] + "</g>"
        parts.append(g)
        parts.append(f'<text x="{x + 48}" y="{y + 27.5}" class="sans ink" font-size="15" font-weight="500">{esc(label)}</text>')
    parts.append(f'<text x="56" y="404" class="mono faint" font-size="13">cihanca.com  ·  Visiosoft</text>')

    # sağ: canlıdaki ürünlerin simgeleri, bir ana ekran gibi
    grid = ["ovodock", "ovokodo", "mailkodo", "sitekodo", "ovoroom",
            "ovoloop", "ovolabs", "preplay", "parkbiz", "vaybak",
            "relivaro", "searvex", "jourilo", "markilo", None]
    s, gap, gx, gy = 76, 20, 642, 62
    for i, kind in enumerate(grid):
        x, y = gx + (i % 5) * (s + gap), gy + (i // 5) * (s + gap)
        if kind is None:
            parts.append(f'<rect x="{x + .75}" y="{y + .75}" width="{s - 1.5}" height="{s - 1.5}" rx="{s * .26}" '
                         f'stroke="{t["faint"]}" stroke-width="1.5" stroke-dasharray="4 5"/>')
            parts.append(f'<path d="M{x + s/2} {y + s/2 - 9}v18M{x + s/2 - 9} {y + s/2}h18" stroke="{t["faint"]}" '
                         f'stroke-width="2" stroke-linecap="round"/>')
            continue
        parts.append(app_tile(kind, x, y, s, theme))
    cy = gy + 3 * (s + gap) + 14
    parts.append(f'<circle cx="{gx + 5}" cy="{cy - 4.5}" r="4.5" fill="{t["live"]}" class="pulse"/>')
    parts.append(f'<text x="{gx + 18}" y="{cy}" class="mono muted" font-size="12.5">canlıda · ovokodo.com · preplay.cc · parkbiz.com.tr · vaybak.app</text>')
    return doc(W, H, "".join(parts), "Cihan Topaç — Fikirden canlıya ürün geliştiriyorum: mobil uygulamalar, web uygulamaları ve SaaS, kurumsal web siteleri, geliştirici araçları.")


def card(name, theme):
    t = THEMES[theme]
    tool = TOOLS[name]
    a = tool["accent"][theme]
    W, H = 600, 340
    parts = [style(t)]
    parts.append(f'<defs><clipPath id="c"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18"/></clipPath></defs>')
    parts.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="{t["surface"]}" stroke="{t["border"]}"/>')
    sym, _ = embed(BRAND / f"{name}-symbol.svg", W - 215, H - 205, w=270, h=270, theme=theme, align="xMidYMid")
    parts.append(f'<g clip-path="url(#c)" opacity="{0.07 if theme == "light" else 0.09}">{sym}</g>')
    parts.append(f'<rect x="0" y="0" width="5" height="{H}" fill="{a}" clip-path="url(#c)"/>')
    lock, _ = embed(BRAND / f"{name}-lockup-{theme}.svg", 38, 34, h=tool["lockup_h"])
    parts.append(lock)
    parts.append(f'<text x="{W - 36}" y="54" text-anchor="end" class="mono" fill="{a}" font-size="12" font-weight="600" letter-spacing="1.4">{esc(tool["chip"])}</text>')
    for i, line in enumerate(tool["lines"]):
        parts.append(f'<text x="38" y="{124 + i * 31}" class="sans ink" font-size="23" font-weight="600" letter-spacing="-.4">{esc(line)}</text>')
    for i, (num, label) in enumerate(tool["metrics"]):
        x = 38 + i * 178
        parts.append(f'<line x1="{x}" y1="196" x2="{x}" y2="246" stroke="{t["border"]}" stroke-width="1.5"/>')
        parts.append(f'<text x="{x + 14}" y="226" class="sans" fill="{a}" font-size="30" font-weight="700" letter-spacing="-.8">{esc(num)}</text>')
        parts.append(f'<text x="{x + 14}" y="249" class="sans muted" font-size="14">{esc(label)}</text>')
    parts.append(f'<rect x="38" y="274" width="{min(18 + 8.4 * (len(tool["cmd"]) + 2), 420):.0f}" height="34" rx="9" fill="{t["bg"]}" stroke="{t["border"]}"/>')
    parts.append(f'<text x="52" y="296" class="mono" font-size="13.5"><tspan class="faint">$ </tspan><tspan class="ink">{esc(tool["cmd"])}</tspan></text>')
    parts.append(f'<text x="{W - 36}" y="296" text-anchor="end" class="mono faint" font-size="12">repo ↗</text>')
    return doc(W, H, "".join(parts), f"{name.capitalize()} — {' '.join(tool['lines'])}")


def family(theme):
    """Ovokodo ailesi: aile merkezi, ana ürün Ovodock (22 uygulama) ve bağımsız ürünler."""
    t = THEMES[theme]
    W, H = 1200, 400
    green, _ = ovo_colors("ovokodo", theme)
    parts = [style(t, """
.app{animation:blink 3.3s ease-in-out infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}
""")]
    parts.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="20" fill="{t["surface"]}" stroke="{t["border"]}"/>')

    # sol: aile merkezi
    parts.append(ovo_tile("ovokodo", 48, 48, 52, theme))
    parts.append(f'<text x="116" y="83" class="sans ink" font-size="30" font-weight="700" letter-spacing="-.8">ovokodo</text>')
    parts.append(f'<text x="48" y="140" class="mono" fill="{green}" font-size="12" font-weight="600" letter-spacing="1.6">AİLE MERKEZİ · OVOKODO.COM</text>')
    for i, line in enumerate(["Yapay zekâ destekli iş işletim sistemi.", "Tek repoda yedi site; ana ürün Ovodock",
                              "web, masaüstü ve mobilde yayında."]):
        parts.append(f'<text x="48" y="{176 + i * 25}" class="sans muted" font-size="16.5">{esc(line)}</text>')
    for i, (num, label) in enumerate([("7", "site"), ("22", "uygulama"), ("4600+", "test")]):
        x = 48 + i * 112
        parts.append(f'<line x1="{x}" y1="276" x2="{x}" y2="334" stroke="{t["border"]}" stroke-width="1.5"/>')
        parts.append(f'<text x="{x + 14}" y="308" class="sans" fill="{green}" font-size="30" font-weight="700" letter-spacing="-.8">{num}</text>')
        parts.append(f'<text x="{x + 14}" y="331" class="sans muted" font-size="14">{label}</text>')

    # orta: Ovodock ve çevresinde 22 uygulama
    cx, cy, ring = 640, 178, 104
    for k in range(22):
        ang = -math.pi / 2 + 2 * math.pi * k / 22
        x, y = cx + ring * math.cos(ang), cy + ring * math.sin(ang)
        parts.append(f'<rect class="app" style="animation-delay:{k * 0.15:.2f}s" x="{x - 6:.1f}" y="{y - 6:.1f}" '
                     f'width="12" height="12" rx="3.5" fill="{t["ink"]}" fill-opacity=".8"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{ring}" stroke="{t["ink"]}" stroke-opacity=".15" stroke-width="1"/>')
    parts.append(ovo_tile("ovodock", cx - 44, cy - 44, 88, theme, rx=24))
    parts.append(f'<text x="{cx}" y="{cy + ring + 44}" text-anchor="middle" class="sans ink" font-size="19" font-weight="700">ovodock.com</text>')
    parts.append(f'<text x="{cx}" y="{cy + ring + 68}" text-anchor="middle" class="sans muted" font-size="14.5">ana ürün · tek oturumda 22 uygulama</text>')
    parts.append(f'<path d="M100 74 C 300 74, 420 {cy}, {cx - ring - 14} {cy}" stroke="{t["faint"]}" stroke-width="1.3" stroke-dasharray="3 5"/>')

    # sağ: bağımsız ürünler
    items = [("mailkodo", "mailkodo.com", "işletme postası"), ("sitekodo", "sitekodo.com", "site + barındırma"),
             ("ovoroom", "ovoroom.com", "görüşme odası"), ("ovoloop", "ovoloop.com", "topluluk"),
             ("ovolabs", "ovolabs.dev", "AI / Ar-Ge"), ("ovokodo-id", "id.ovokodo.com", "ortak kimlik")]
    px, pw, ph, top, step = 836, 320, 44, 44, 54
    for i, (mark, domain, desc) in enumerate(items):
        y = top + i * step
        fg, _ = ovo_colors(mark, theme)
        parts.append(f'<path d="M{cx + ring + 14} {cy} C {cx + ring + 70} {cy}, {px - 60} {y + ph / 2}, {px} {y + ph / 2}" '
                     f'stroke="{fg}" stroke-opacity=".45" stroke-width="1.3"/>')
        parts.append(f'<rect x="{px}" y="{y}" width="{pw}" height="{ph}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>')
        parts.append(ovo_tile(mark, px + 8, y + 7, 30, theme, rx=8))
        parts.append(f'<text x="{px + 50}" y="{y + 27.5}" class="sans ink" font-size="15" font-weight="600">{domain}</text>')
        parts.append(f'<text x="{px + pw - 16}" y="{y + 27.5}" text-anchor="end" class="sans muted" font-size="13.5">{esc(desc)}</text>')
    return doc(W, H, "".join(parts), "Ovokodo ailesi: ovokodo.com aile merkezi, ana ürün ovodock.com içinde 22 uygulama; mailkodo.com, sitekodo.com, ovoroom.com, ovoloop.com, ovolabs.dev ve id.ovokodo.com.")


LIVE = {
    "preplay": dict(domain="preplay.cc", status=("canlı", "live"),
                    lines=["Android TV'den web'e, tüm platformlarda", "çalışan medya oynatıcı."],
                    tag="TV · telefon · tablet · masaüstü · web"),
    "vaybak": dict(domain="vaybak.app", status=("mağaza incelemesinde", "accent"),
                   lines=["Çocuklar ve gençler için ebeveyn", "kontrollü, güvenli keşif uygulaması."],
                   tag="Android · iOS · web"),
}

CORP = {
    "rbm": dict(domain="rbmsigorta.com", plate="#232a3a", lines=["RBM Sigorta ve Danışmanlık"],
                tag="Next.js · SEO · mobil öncelikli"),
    "bessi": dict(domain="bessisigorta.com", plate="#183f63", lines=["Bessi Sigorta"],
                  tag="Next.js · Tailwind · içerik modeli"),
    "parkbiz": dict(domain="parkbiz.com.tr", plate="#ffffff", lines=["Otopark bul, plakayla öde, abone ol"],
                    tag="Laravel · Inertia · React"),
    "visiosoft": dict(domain="visiosoft.com.tr", plate="#171b99", lines=["İnsansız otopark yönetim sistemleri"],
                      tag="Next.js · MDX · çok dilli"),
}

PULSE = ".pulse{animation:pulse 2.4s ease-in-out infinite}@keyframes pulse{50%{opacity:.25}}"


def status_pill(right, y, status, color, t):
    sw = 36 + len(status) * 7.3
    sx = right - sw
    return (f'<rect x="{sx:.1f}" y="{y}" width="{sw:.1f}" height="28" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>'
            f'<circle cx="{sx + 14:.1f}" cy="{y + 14}" r="4" fill="{color}" class="pulse"/>'
            f'<text x="{sx + 24:.1f}" y="{y + 18.5}" class="mono" fill="{color}" font-size="12">{esc(status)}</text>')


def live_tile(kind, theme):
    """Kendi markası ve alan adıyla yayında olan bir ürün."""
    t = THEMES[theme]
    item = LIVE[kind]
    W, H = 600, 290
    parts = [style(t, PULSE)]
    parts.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="{t["surface"]}" stroke="{t["border"]}"/>')
    lx, ly = 30, 32
    if kind == "preplay":
        parts.append(png(PRODUCTS / "preplay-logo.png", lx - 4, ly - 4, 159, 56))
    else:
        logo, _ = embed(PRODUCTS / f"vaybak-logo{'-dark' if theme == 'dark' else ''}.svg", lx - 4, ly + 4, h=40)
        parts.append(logo)
    status, scol = item["status"]
    parts.append(status_pill(W - 26, 40, status, t[scol], t))
    parts.append(f'<text x="30" y="126" class="mono ink" font-size="15" font-weight="600">{item["domain"]} <tspan class="faint">↗</tspan></text>')
    for j, line in enumerate(item["lines"]):
        parts.append(f'<text x="30" y="{166 + j * 24}" class="sans muted" font-size="16">{esc(line)}</text>')
    parts.append(f'<line x1="30" y1="222" x2="{W - 30}" y2="222" stroke="{t["border"]}" stroke-dasharray="3 4"/>')
    parts.append(f'<text x="30" y="254" class="mono faint" font-size="12.5">{esc(item["tag"])}</text>')
    return doc(W, H, "".join(parts), f"{item['domain']} — {' '.join(item['lines'])}")


def corp_tile(kind, theme):
    """Kurumsal web sitesi: solda markanın kendi zemininde logosu, sağda bilgiler."""
    t = THEMES[theme]
    item = CORP[kind]
    W, H = 600, 180
    parts = [style(t, PULSE)]
    parts.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="{t["surface"]}" stroke="{t["border"]}"/>')
    px, py, pw, ph = 20, 20, 236, 140
    parts.append(f'<clipPath id="plate"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="12"/></clipPath>')
    edge = f' stroke="{t["border"]}"' if item["plate"] == "#ffffff" else ""
    parts.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="12" fill="{item["plate"]}"{edge}/>')
    if kind == "rbm":
        parts.append(png(PRODUCTS / "rbm-plate.png", px + 6, py + 22, pw - 12, 96, ' clip-path="url(#plate)"'))
    elif kind == "bessi":
        parts.append(png(PRODUCTS / "bessi-logo.png", px + 22, py + ph / 2 - 14, pw - 44, 28))
    elif kind == "parkbiz":
        parts.append(png(PRODUCTS / "parkbiz-logo.png", px + 38, py + ph / 2 - 30, pw - 76, 60))
    else:
        logo, lw = embed(PRODUCTS / "visiosoft-logo.svg", 0, 0, h=40)
        logo = logo.replace('fill="#171b99"', 'fill="#ffffff"').replace('x="0" y="0"', f'x="{px + (pw - lw) / 2:.1f}" y="{py + ph / 2 - 20}"', 1)
        parts.append(logo)
    x = px + pw + 28
    parts.append(f'<text x="{x}" y="58" class="mono ink" font-size="15" font-weight="600">{item["domain"]} <tspan class="faint">↗</tspan></text>')
    for j, line in enumerate(item["lines"]):
        parts.append(f'<text x="{x}" y="{92 + j * 24}" class="sans muted" font-size="16">{esc(line)}</text>')
    parts.append(f'<line x1="{x}" y1="116" x2="{W - 28}" y2="116" stroke="{t["border"]}" stroke-dasharray="3 4"/>')
    parts.append(f'<text x="{x}" y="146" class="mono faint" font-size="12.5">{esc(item["tag"])}</text>')
    parts.append(status_pill(W - 24, 36, "canlı", t["live"], t))
    return doc(W, H, "".join(parts), f"{item['domain']} — {item['lines'][0]}, kurumsal web sitesi")


def divider(theme, title, note):
    t = THEMES[theme]
    W, H = 1200, 56
    parts = [style(t)]
    parts.append(f'<rect x="2" y="23" width="10" height="10" rx="2" fill="{t["accent"]}"/>')
    parts.append(f'<text x="24" y="33" class="mono ink" font-size="14" font-weight="600" letter-spacing="2.4">{esc(title)}</text>')
    tw = 24 + len(title) * 10.8
    parts.append(f'<line x1="{tw + 14}" y1="28" x2="{W - 12 - len(note) * 8.2}" y2="28" stroke="{t["border"]}" stroke-width="1.5"/>')
    parts.append(f'<text x="{W - 2}" y="33" text-anchor="end" class="mono faint" font-size="13">{esc(note)}</text>')
    return doc(W, H, "".join(parts), title)


def stack(theme):
    t = THEMES[theme]
    W, H = 1200, 44
    items = ["TypeScript", "Laravel", "React · Next.js", "Kotlin", "Flutter", "Tauri", "Playwright", "Claude Code"]
    parts = [style(t)]
    text = "   /   ".join(items)
    parts.append(f'<text x="{W / 2}" y="27" text-anchor="middle" class="mono muted" font-size="14" letter-spacing=".4">{esc(text)}</text>')
    return doc(W, H, "".join(parts), "Teknolojiler: " + ", ".join(items))


def main():
    files = {}
    for theme in THEMES:
        files[f"hero-{theme}.svg"] = hero(theme)
        for name in ORDER:
            files[f"card-{name}-{theme}.svg"] = card(name, theme)
        files[f"div-tools-{theme}.svg"] = divider(theme, "AÇIK KAYNAK", "yeni yayınlandı · CLI + Claude Code eklentisi")
        files[f"div-family-{theme}.svg"] = divider(theme, "OVOKODO AİLESİ", "tek repo · 7 site · 22 uygulama")
        files[f"div-live-{theme}.svg"] = divider(theme, "YAYINDA", "kendi markası, kendi alan adı")
        files[f"family-{theme}.svg"] = family(theme)
        for kind in LIVE:
            files[f"live-{kind}-{theme}.svg"] = live_tile(kind, theme)
        for kind in CORP:
            files[f"corp-{kind}-{theme}.svg"] = corp_tile(kind, theme)
        files[f"div-corp-{theme}.svg"] = divider(theme, "KURUMSAL WEB", "Next.js ile kurumsal siteler")
        files[f"stack-{theme}.svg"] = stack(theme)
    for old in OUT.glob("*.svg"):
        if old.name not in files:
            old.unlink()
    for fn, content in files.items():
        (OUT / fn).write_text(content)
    print(f"{len(files)} dosya yazıldı → {OUT}")


if __name__ == "__main__":
    main()
