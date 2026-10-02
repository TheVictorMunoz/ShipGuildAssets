"""Builds the ShipGuild vector brand kit from hand-cleaned geometry."""
import math, os, re
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import resvg_py

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONT = os.path.join(HERE, 'fonts', 'Michroma-Regular.ttf')

# ---------------------------------------------------------------- palette
VOLT = '#EEFC2A'      # top of emblem, primary highlight
LIME = '#C8EE10'      # core brand lime
SIGNAL = '#93D106'    # lower gradient
DEEP = '#4E9A00'      # shadows, keel facet
FOREST = '#24470A'    # lime on light backgrounds
VOID = '#050705'      # background
PANEL = '#0D130C'     # raised surfaces
MIST = '#EAF7E2'      # glass highlight on the SHIP letters
WHITE = '#FFFFFF'

def r(v):
    return f'{v:.1f}'.rstrip('0').rstrip('.')

def svg(w, h, body, vb=None, title='ShipGuild'):
    vb = vb or f'0 0 {r(w)} {r(h)}'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{r(w)}" height="{r(h)}" viewBox="{vb}" '
            f'role="img" aria-label="{title}">\n<title>{title}</title>\n{body}\n</svg>\n')

# ---------------------------------------------------------------- SG emblem
# Native coordinate space: 1254 x 1254, centre x = 627.
EMB = dict(
    ring=('ellipse', 627, 622.5, 465, 493),
    roof='M289,595 L627,436 L965,595 L965,621 L627,472 L289,621Z',
    head_c=('circle', 627, 255, 54.5),
    head_l=('circle', 449, 315, 40.5),
    head_r=('circle', 805, 315, 40.5),
    body_c='M532,433 L532,412 A95,87 0 0 1 722,412 L722,433 L627,394Z',
    body_l='M382,501 L382,432 A64.5,64 0 0 1 511,432 L511,442Z',
    body_r='M872,501 L872,432 A64.5,64 0 0 0 743,432 L743,442Z',
    letter_s=('M604,523 L296,661 L296,800 L309,814 L324,820 L340,820 L525,784 L534,785 L540,791 '
              'L541,830 L532,842 L334,911 L378,952 L387,956 L402,955 L587,886 L600,875 L604,865 '
              'L603,748 L546,723 L527,721 L361,753 L358,749 L358,705 L536,624 L541,626 L541,679 L604,705Z'),
    letter_g=('M650,523 L651,872 L669,887 L853,956 L875,952 L910,925 L942,885 L951,861 L956,806 '
              'L793,738 L793,804 L894,845 L895,870 L891,889 L882,896 L870,896 L718,840 L712,831 '
              'L713,625 L737,632 L895,704 L896,736 L957,762 L957,661 L810,592Z'),
    keel_l='M627,912 L457,978 Q570,1016 627,1105Z',
    keel_r='M627,912 L797,978 Q684,1016 627,1105Z',
)
EMB_VB = (97, 92, 1060, 1060)

def emblem_defs(p, mode):
    if mode == 'color':
        return (f'<linearGradient id="{p}g" x1="0" y1="118" x2="0" y2="1127" gradientUnits="userSpaceOnUse">'
                f'<stop offset="0" stop-color="{VOLT}"/><stop offset=".55" stop-color="{LIME}"/>'
                f'<stop offset="1" stop-color="{SIGNAL}"/></linearGradient>'
                f'<linearGradient id="{p}k" x1="0" y1="912" x2="0" y2="1105" gradientUnits="userSpaceOnUse">'
                f'<stop offset="0" stop-color="{LIME}"/><stop offset="1" stop-color="{DEEP}"/></linearGradient>'
                f'<linearGradient id="{p}k2" x1="0" y1="912" x2="0" y2="1105" gradientUnits="userSpaceOnUse">'
                f'<stop offset="0" stop-color="#B2E20C"/><stop offset="1" stop-color="#3F8500"/></linearGradient>')
    return ''

def emblem_body(p='e', mode='color', color=None, ring=True):
    """mode: color | mono (single colour via `color`)"""
    if mode == 'color':
        f, k1, k2 = f'url(#{p}g)', f'url(#{p}k)', f'url(#{p}k2)'
    else:
        f = k1 = k2 = color
    out = [f'<defs>{emblem_defs(p, mode)}</defs>'] if mode == 'color' else []
    _, cx, cy, rx, ry = EMB['ring']
    if ring:
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{f}" stroke-width="23"/>')
    g = [f'<g fill="{f}" stroke="{f}" stroke-width="3" stroke-linejoin="round">']
    for key in ('roof', 'body_c', 'body_l', 'body_r', 'letter_s', 'letter_g'):
        g.append(f'<path d="{EMB[key]}"/>')
    for key in ('head_c', 'head_l', 'head_r'):
        _, x, y, rad = EMB[key]
        g.append(f'<circle cx="{x}" cy="{y}" r="{rad}"/>')
    g.append('</g>')
    out += g
    out.append(f'<path d="{EMB["keel_l"]}" fill="{k1}"/>')
    out.append(f'<path d="{EMB["keel_r"]}" fill="{k2}"/>')
    return '\n'.join(out)

def emblem_group(x, y, size, p='e', mode='color', color=None, opacity=None, ring=True):
    vx, vy, vw, vh = EMB_VB
    s = size / vw
    op = f' opacity="{opacity}"' if opacity is not None else ''
    return (f'<g transform="translate({r(x)} {r(y)}) scale({s:.5f}) translate({-vx} {-vy})"{op}>'
            f'{emblem_body(p, mode, color, ring)}</g>')

# ---------------------------------------------------------------- SHIP mark
# Native coordinate space: the 1448 x 1086 source artwork.
SHIP_LETTERS = [
    # S
    'M346,388 L564,388 L517,450 L369,450 L351,463 L346,489 L498,489 L534,526 L513,613 L451,654 '
    'L219,654 L270,594 L421,594 L439,580 L446,551 L442,545 L288,545 L253,507 L272,436Z',
    # H
    'M585,431 L665,431 L645,503 L737,503 L756,431 L833,431 L779,647 L702,647 L722,563 L630,563 '
    'L609,647 L532,647Z',
    # I
    'M868,431 L944,431 L892,647 L815,647Z',
    # P (with counter)
    'M962,431 L1162,431 L1210,472 L1193,550 L1141,587 L1015,587 L1003,641 L921,656 L968,464 L992,461Z '
    'M1038,489 L1128,489 L1120,528 L1112,533 L1027,533Z',
]
SHIP_SWOOSH = (
    'M181,595 C150,630 143,672 200,702 C330,745 520,780 651,784 C800,784 960,752 1056,724 '
    'C1140,692 1210,650 1291,588 L1305,633 L1348,531 L1373,462 L1291,490 L1238,516 L1265,534 '
    'C1200,585 1120,630 1043,664 C930,700 760,733 620,734 C520,733 450,722 414,715 L393,721 '
    'C480,738 600,748 700,744 C820,738 940,712 1043,676 L1009,725 C900,752 790,772 680,773 '
    'C560,773 420,750 300,726 C230,712 180,690 164,668 C152,648 158,618 181,595Z'
)
SHIP_BITS = [(878, 739, 11), (912, 733, 12), (966, 719, 14), (998, 711, 15), (1030, 701, 16)]
SHIP_VB = (100, 330, 1310, 490)   # tight crop around the mark

from shapely.geometry import Polygon
from shapely.ops import unary_union

def _rings(d):
    """Parse an M/L/Z polygon path into lists of points."""
    return [[tuple(map(float, xy)) for xy in re.findall(r'(-?[\d.]+),(-?[\d.]+)', sub)]
            for sub in d.split('M') if sub.strip()]

def _letters_geom():
    polys = []
    for d in SHIP_LETTERS:
        rings = _rings(d)
        polys.append(Polygon(rings[0], rings[1:]))
    return unary_union(polys)

def _geom_d(g):
    geoms = getattr(g, 'geoms', [g])
    out = []
    for poly in geoms:
        for ring in [poly.exterior, *poly.interiors]:
            pts = list(ring.coords)[:-1]
            out.append('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + 'Z')
    return ' '.join(out)

def _offset(g, dist, close=30):
    """Mitred outward offset, then a closing pass so narrow gaps fill solid."""
    o = g.buffer(dist, join_style='mitre', mitre_limit=2.0)
    o = o.buffer(close, join_style='mitre', mitre_limit=2.0).buffer(-close, join_style='mitre', mitre_limit=2.0)
    return Polygon(o.exterior) if o.geom_type == 'Polygon' else unary_union([Polygon(p.exterior) for p in o.geoms])

_LG = _letters_geom()
SHIP_OUTER = _geom_d(_offset(_LG, 27).simplify(0.6))
SHIP_INNER = _geom_d(_offset(_LG, 20).simplify(0.6))

def ship_body(p='s', mode='glow', color=None):
    """mode: glow (full effect, on dark) | flat (no blur, any dark bg) | mono"""
    letters = ''.join(f'<path d="{d}"/>' for d in SHIP_LETTERS)
    bits = ''.join(
        f'<rect x="{x - s/2}" y="{y - s/2}" width="{s}" height="{s * .8:.1f}" '
        f'transform="rotate(-14 {x} {y})"/>' for x, y, s in SHIP_BITS)
    if mode == 'mono':
        return (f'<g fill="{color}" fill-rule="evenodd">{letters}</g>'
                f'<path d="{SHIP_SWOOSH}" fill="{color}"/><g fill="{color}">{bits}</g>')
    defs = (f'<linearGradient id="{p}glass" x1="0" y1="388" x2="0" y2="660" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{WHITE}"/><stop offset=".45" stop-color="{MIST}"/>'
            f'<stop offset=".52" stop-color="#9CE25E"/><stop offset="1" stop-color="#3FA829"/></linearGradient>'
            f'<linearGradient id="{p}sw" x1="150" y1="0" x2="1373" y2="0" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="#2E8A12"/><stop offset=".45" stop-color="#7FD41E"/>'
            f'<stop offset="1" stop-color="{VOLT}"/></linearGradient>'
            f'<filter id="{p}blur" x="-20%" y="-40%" width="140%" height="180%">'
            f'<feGaussianBlur stdDeviation="14"/></filter>')
    out = [f'<defs>{defs}</defs>']
    if mode == 'glow':
        out.append(f'<g filter="url(#{p}blur)" opacity=".75"><path d="{SHIP_OUTER}" fill="#7FE01A"/>'
                   f'<path d="{SHIP_SWOOSH}" fill="#9BE81E"/></g>')
    out.append(f'<path d="{SHIP_OUTER}" fill="#B4F02C"/>')
    out.append(f'<path d="{SHIP_INNER}" fill="{VOID}"/>')
    out.append(f'<g fill="url(#{p}glass)" fill-rule="evenodd" stroke="#DFFFB0" stroke-width="4" stroke-linejoin="round">{letters}</g>')
    out.append(f'<path d="{SHIP_SWOOSH}" fill="url(#{p}sw)"/>')
    out.append(f'<g fill="{VOLT}">{bits}</g>')
    return '\n'.join(out)

def ship_group(x, y, width, p='s', mode='glow', color=None):
    vx, vy, vw, vh = SHIP_VB
    s = width / vw
    return (f'<g transform="translate({r(x)} {r(y)}) scale({s:.5f}) translate({-vx} {-vy})">'
            f'{ship_body(p, mode, color)}</g>')

# ---------------------------------------------------------------- ShipGuild wordmark
# Traced from the banner lettering; translated so the bbox starts at 0,0.
_raw = open(os.path.join(HERE, 'wordmark-trace.txt')).read().split('\n')
def _shift(d, dx, dy):
    return re.sub(r'([\d.]+),([\d.]+)', lambda m: f'{float(m[1]) - dx:.1f},{float(m[2]) - dy:.1f}', d)
WORD_D = ' '.join(_shift(d, 652.0, 194.2) for d in _raw if d)
WORD_W, WORD_H = 1004.2, 190.3

def word_group(x, y, width, p='w', mode='color', color=None):
    s = width / WORD_W
    if mode == 'color':
        defs = (f'<defs><linearGradient id="{p}g" x1="0" y1="0" x2="0" y2="{WORD_H}" gradientUnits="userSpaceOnUse">'
                f'<stop offset="0" stop-color="{VOLT}"/><stop offset=".6" stop-color="{LIME}"/>'
                f'<stop offset="1" stop-color="#A6DC08"/></linearGradient></defs>')
        fill = f'url(#{p}g)'
    else:
        defs, fill = '', color
    return (f'<g transform="translate({r(x)} {r(y)}) scale({s:.5f})">{defs}'
            f'<path d="{WORD_D}" fill="{fill}" fill-rule="evenodd"/></g>')

# ---------------------------------------------------------------- tagline (Michroma outlined)
_font = TTFont(FONT)
_gs = _font.getGlyphSet()
_cmap = _font.getBestCmap()
_upm = _font['head'].unitsPerEm

def text_paths(text, x, y, size, tracking=0.0, colors=None):
    """Returns (svg, width). tracking is in em. colors maps word index -> fill."""
    s = size / _upm
    cur = 0.0
    words = text.split(' ')
    parts = []
    for wi, word in enumerate(words):
        fill = (colors or {}).get(wi)
        ds = []
        for ch in word:
            gname = _cmap[ord(ch)]
            pen = SVGPathPen(_gs)
            _gs[gname].draw(TransformPen(pen, (s, 0, 0, -s, x + cur, y)))
            ds.append(pen.getCommands())
            cur += _gs[gname].width * s + tracking * size
        attr = f' fill="{fill}"' if fill else ''
        parts.append(f'<path d="{" ".join(ds)}"{attr}/>')
        if wi < len(words) - 1:
            cur += _gs[_cmap[32]].width * s + tracking * size
    return ''.join(parts), cur - tracking * size

TAG = 'BUILT TO SCALE. DRIVEN BY COMMUNITY.'
TAG_ACCENT = {1: LIME, 4: LIME}

def tagline(x, y, size, base=WHITE, accent=True, tracking=0.55, anchor='start'):
    _, w = text_paths(TAG, 0, 0, size, tracking)
    if anchor == 'middle':
        x -= w / 2
    body, w = text_paths(TAG, x, y, size, tracking, TAG_ACCENT if accent else None)
    return f'<g fill="{base}">{body}</g>', w

# ---------------------------------------------------------------- backgrounds and decoration
def bg_defs(p, w, h):
    return (f'<radialGradient id="{p}glow" cx="{w*.55}" cy="{h*.42}" r="{w*.6}" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="#132108"/><stop offset=".55" stop-color="#070B05"/>'
            f'<stop offset="1" stop-color="{VOID}"/></radialGradient>'
            f'<linearGradient id="{p}streak" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0" stop-color="{LIME}" stop-opacity="0"/>'
            f'<stop offset=".7" stop-color="{LIME}" stop-opacity=".9"/>'
            f'<stop offset="1" stop-color="{VOLT}" stop-opacity="0"/></linearGradient>'
            f'<filter id="{p}soft" x="-10%" y="-50%" width="120%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>'
            f'<filter id="{p}haze" x="-10%" y="-50%" width="120%" height="200%"><feGaussianBlur stdDeviation="22"/></filter>'
            f'<pattern id="{p}dots" width="24" height="24" patternUnits="userSpaceOnUse">'
            f'<circle cx="2" cy="2" r="1.2" fill="{LIME}" fill-opacity=".18"/></pattern>')

def streaks(p, w, h, y0, amp):
    """Sweeping light trails rising left to right, scaled to the canvas."""
    def curve(off, lift=1.0):
        return (f'M{-w*.05:.0f},{y0 + off + amp*.9:.0f} C{w*.25:.0f},{y0 + off + amp*1.5:.0f} '
                f'{w*.65:.0f},{y0 + off + amp*1.1:.0f} {w*1.05:.0f},{y0 + off - amp*1.6*lift:.0f}')
    out = [f'<g fill="none" stroke="url(#{p}streak)" stroke-linecap="round">']
    out.append(f'<path d="{curve(0)}" stroke-width="{h*.09:.0f}" opacity=".30" filter="url(#{p}haze)"/>')
    out.append(f'<path d="{curve(0)}" stroke-width="{h*.018:.0f}" opacity=".75" filter="url(#{p}soft)"/>')
    for off, sw, op, lift in [(0, 2.6, 1, 1), (h*.025, 1.4, .8, 1.05), (h*.05, 1.0, .6, 1.12),
                              (-h*.03, 1.2, .55, .9), (h*.085, 1.6, .45, 1.2), (-h*.07, .9, .35, .8)]:
        out.append(f'<path d="{curve(off, lift)}" stroke-width="{sw}" opacity="{op}"/>')
    out.append('</g>')
    return '\n'.join(out)

def hud_frame(x, y, w, h, c=LIME, op=.35):
    """Thin technical frame with clipped corners."""
    k = 22
    d = (f'M{x+k},{y} L{x+w*.45},{y} L{x+w*.45+14},{y+10} L{x+w-k},{y+10} L{x+w},{y+10+k} '
         f'L{x+w},{y+h-k} L{x+w-k},{y+h} L{x+k},{y+h} L{x},{y+h-k} L{x},{y+k}Z')
    ticks = ''.join(f'<rect x="{x+12}" y="{y+h*.22+i*26}" width="{14 if i%2 else 8}" height="2.5"/>' for i in range(7))
    return (f'<path d="{d}" fill="none" stroke="{c}" stroke-opacity="{op}" stroke-width="1.5"/>'
            f'<path d="M{x+26},{y+30} L{x+26},{y+14} L{x+46},{y+14}" fill="none" stroke="{c}" stroke-width="3"/>'
            f'<g fill="{c}" fill-opacity=".45">{ticks}</g>')

def pill(x, y, w, h, c=LIME):
    k = h * .45
    d = f'M{x+k},{y} L{x+w-k},{y} L{x+w},{y+h/2} L{x+w-k},{y+h} L{x+k},{y+h} L{x},{y+h/2}Z'
    return (f'<path d="{d}" fill="{PANEL}" fill-opacity=".85" stroke="{c}" stroke-opacity=".55" stroke-width="1.5"/>')

# ---------------------------------------------------------------- compositions
def write(rel, content):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(content)
    return path

def png(svg_path, rel, width=None, height=None, background=None):
    data = resvg_py.svg_to_bytes(svg_path=svg_path, width=width, height=height, background=background)
    out = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'wb') as fh:
        fh.write(bytes(data))

def build():
    vx, vy, vw, vh = EMB_VB
    files = {}

    # Emblem variants (square, transparent)
    for name, mode, col in [('color', 'color', None), ('white', 'mono', WHITE),
                            ('black', 'mono', '#000000'), ('lime', 'mono', LIME), ('forest', 'mono', FOREST)]:
        files[f'emblem-{name}'] = write(f'svg/emblem/shipguild-emblem-{name}.svg',
            svg(1060, 1060, emblem_body('e', mode, col), vb=f'{vx} {vy} {vw} {vh}', title='ShipGuild emblem'))
    # App icon: emblem on rounded dark tile
    icon = (f'<defs>{bg_defs("i", 1024, 1024)}</defs><rect width="1024" height="1024" rx="224" fill="url(#iglow)"/>'
            + emblem_group(122, 122, 780, 'e'))
    files['icon'] = write('svg/emblem/shipguild-app-icon.svg', svg(1024, 1024, icon, title='ShipGuild app icon'))
    # Favicon: simplified, square, no rounding so platforms can mask it
    fav = f'<rect width="1024" height="1024" fill="{VOID}"/>' + emblem_group(62, 62, 900, 'e')
    files['favicon'] = write('svg/emblem/shipguild-favicon.svg', svg(1024, 1024, fav, title='ShipGuild'))
    # Small-size mark: roof, SG and keel only, cropped tight so it survives 16 to 48 px
    small = [f'<rect x="250" y="400" width="755" height="755" fill="{VOID}"/>', '<defs>' + emblem_defs('m', 'color') + '</defs>',
             '<g fill="url(#mg)" stroke="url(#mg)" stroke-width="6" stroke-linejoin="round">']
    small += [f'<path d="{EMB[k]}"/>' for k in ('roof', 'letter_s', 'letter_g')]
    small += ['</g>', f'<path d="{EMB["keel_l"]}" fill="url(#mk)"/>', f'<path d="{EMB["keel_r"]}" fill="url(#mk2)"/>']
    files['favicon-small'] = write('svg/emblem/shipguild-favicon-small.svg',
        svg(755, 755, '\n'.join(small), vb='250 400 755 755', title='ShipGuild'))

    # SHIP mark
    sx, sy, sw, sh = SHIP_VB
    for name, mode, col in [('glow', 'glow', None), ('flat', 'flat', None),
                            ('white', 'mono', WHITE), ('black', 'mono', '#000000'), ('lime', 'mono', LIME)]:
        files[f'ship-{name}'] = write(f'svg/ship/ship-mark-{name}.svg',
            svg(sw, sh, ship_body('s', mode, col), vb=f'{sx} {sy} {sw} {sh}', title='SHIP'))

    # Wordmark
    for name, mode, col in [('color', 'color', None), ('white', 'mono', WHITE),
                            ('black', 'mono', '#000000'), ('forest', 'mono', FOREST)]:
        files[f'word-{name}'] = write(f'svg/wordmark/shipguild-wordmark-{name}.svg',
            svg(WORD_W, WORD_H, word_group(0, 0, WORD_W, 'w', mode, col), title='ShipGuild'))

    # Horizontal lockup: emblem | wordmark + tagline
    def lockup_h(theme):
        dark = theme == 'dark'
        W, H = 1600, 400
        em_mode, em_col = ('color', None) if dark else ('mono', FOREST)
        wm_mode, wm_col = ('color', None) if dark else ('mono', FOREST)
        body = ''
        if dark:
            body += f'<rect width="{W}" height="{H}" fill="{VOID}"/>'
        body += emblem_group(40, 40, 320, 'e', em_mode, em_col)
        body += word_group(410, 102, 1150, 'w', wm_mode, wm_col)
        t, _ = tagline(414, 340, 25.5, WHITE if dark else '#1A1F18', accent=True, tracking=.42)
        if not dark:
            t = t.replace(LIME, '#4E9A00')
        body += t
        return svg(W, H, body, title='ShipGuild')
    files['lock-h-dark'] = write('svg/lockup/shipguild-lockup-horizontal-dark.svg', lockup_h('dark'))
    files['lock-h-light'] = write('svg/lockup/shipguild-lockup-horizontal-light.svg', lockup_h('light'))

    # Stacked lockup
    def lockup_v(theme):
        dark = theme == 'dark'
        W, H = 1200, 1260
        mode, col = ('color', None) if dark else ('mono', FOREST)
        body = f'<rect width="{W}" height="{H}" fill="{VOID}"/>' if dark else ''
        body += emblem_group(300, 60, 600, 'e', mode, col)
        body += word_group(110, 760, 980, 'w', mode, col)
        t, _ = tagline(W / 2, 1060, 22, WHITE if dark else '#1A1F18', tracking=.42, anchor='middle')
        if not dark:
            t = t.replace(LIME, '#4E9A00')
        body += t
        return svg(W, H, body, title='ShipGuild')
    files['lock-v-dark'] = write('svg/lockup/shipguild-lockup-stacked-dark.svg', lockup_v('dark'))
    files['lock-v-light'] = write('svg/lockup/shipguild-lockup-stacked-light.svg', lockup_v('light'))

    # ------------------------------------------------ banners
    def banner(W, H, scale, tagsize, include_ship=True, emblem_side=True, y_shift=0):
        p = 'b'
        b = [f'<defs>{bg_defs(p, W, H)}</defs>', f'<rect width="{W}" height="{H}" fill="url(#{p}glow)"/>',
             f'<rect width="{W}" height="{H}" fill="url(#{p}dots)" opacity=".5"/>']
        if emblem_side:
            es = H * 1.25
            b.append(f'<g filter="url(#{p}soft)">' + emblem_group(W - es * .56, -H * .2, es, 'bg', 'mono', '#5FB30A', opacity=.25, ring=False) + '</g>')
            b.append(emblem_group(W - es * .56, -H * .2, es, 'be', 'mono', '#4F9A0A', opacity=.32, ring=False))
        b.append(streaks(p, W, H, H * .55, H * .12))
        # content block width: ship mark + divider + wordmark
        ship_w = 520 * scale if include_ship else 0
        gap = 70 * scale if include_ship else 0
        word_w = 980 * scale
        total = ship_w + gap + word_w
        x0 = (W - total) / 2 - (40 * scale if emblem_side else 0)
        cy = H * .40 + y_shift
        if include_ship:
            sh_h = ship_w * SHIP_VB[3] / SHIP_VB[2]
            b.append(hud_frame(x0 - 30 * scale, cy - sh_h / 2 - 70 * scale, ship_w + 60 * scale, sh_h + 140 * scale))
            b.append(ship_group(x0, cy - sh_h / 2, ship_w, 'bs', 'glow'))
            dx = x0 + ship_w + gap / 2
            b.append(f'<line x1="{dx:.0f}" y1="{cy - 150*scale:.0f}" x2="{dx:.0f}" y2="{cy + 150*scale:.0f}" '
                     f'stroke="{LIME}" stroke-opacity=".35" stroke-width="1.5"/>')
        wx = x0 + ship_w + gap
        wh = word_w * WORD_H / WORD_W
        wy = cy - wh / 2 - 40 * scale
        b.append(f'<g filter="url(#{p}haze)" opacity=".45">{word_group(wx, wy, word_w, "bwg", "mono", LIME)}</g>')
        b.append(word_group(wx, wy, word_w, 'bw'))
        t, tw = tagline(0, 0, tagsize, WHITE, tracking=.55)
        ph = tagsize * 2.2
        pw = max(word_w, tw + tagsize * 4)
        px, py = wx + (word_w - pw) / 2, wy + wh + 32 * scale
        b.append(pill(px, py, pw, ph))
        t, _ = tagline(px + pw / 2, py + ph / 2 + tagsize * .48, tagsize, WHITE, tracking=.55, anchor='middle')
        b.append(t)
        return svg(W, H, '\n'.join(b), title='ShipGuild. Built to scale. Driven by community.')

    files['banner'] = write('svg/banner/shipguild-banner-1950x806.svg', banner(1950, 806, 1.0, 19, y_shift=-20))
    files['x-header'] = write('svg/banner/shipguild-x-header-1500x500.svg', banner(1500, 500, .72, 14))
    def og(W=1200, H=630):
        p = 'o'
        b = [f'<defs>{bg_defs(p, W, H)}</defs>', f'<rect width="{W}" height="{H}" fill="url(#{p}glow)"/>',
             f'<rect width="{W}" height="{H}" fill="url(#{p}dots)" opacity=".5"/>',
             streaks(p, W, H, H * .62, H * .1)]
        es, ww = 250, 700
        x0 = (W - (es + 50 + ww)) / 2
        b.append(emblem_group(x0, 130, es, 'oe'))
        wy = 255 - ww * WORD_H / WORD_W / 2 - 10
        b.append(f'<g filter="url(#{p}haze)" opacity=".45">{word_group(x0 + es + 50, wy, ww, "owg", "mono", LIME)}</g>')
        b.append(word_group(x0 + es + 50, wy, ww, 'ow'))
        t, _ = tagline(x0 + es + 54, wy + ww * WORD_H / WORD_W + 42, 14.5, WHITE, tracking=.42)
        b.append(t)
        return svg(W, H, '\n'.join(b), title='ShipGuild. Built to scale. Driven by community.')
    files['og'] = write('svg/banner/shipguild-og-1200x630.svg', og())
    files['linkedin'] = write('svg/banner/shipguild-linkedin-1584x396.svg', banner(1584, 396, .58, 12))
    return files

PALETTE = [
    ('Volt', VOLT, 'Highlights, top of gradients'),
    ('Lime', LIME, 'Core brand colour'),
    ('Signal', SIGNAL, 'Gradient base, accents'),
    ('Deep', DEEP, 'Shadows, keel facet'),
    ('Forest', FOREST, 'Brand colour on light backgrounds'),
    ('Void', VOID, 'Primary background'),
    ('Panel', PANEL, 'Cards and raised surfaces'),
    ('Mist', MIST, 'Glass highlight, light text'),
]

def brand_sheet():
    W, H = 1920, 1500
    p = 'g'
    label = lambda x, y, t, size=16, fill='#8FA08A', tr=.3: text_paths(t, x, y, size, tr)[0].replace('<path', f'<path fill="{fill}"')
    b = [f'<defs>{bg_defs(p, W, H)}</defs>', f'<rect width="{W}" height="{H}" fill="{VOID}"/>']
    b.append(word_group(80, 70, 520, 'gw'))
    b.append(label(84, 210, 'BRAND KIT', 18, LIME, .5))
    # logos row
    b.append(f'<rect x="80" y="260" width="560" height="560" rx="18" fill="{PANEL}"/>')
    b.append(emblem_group(130, 310, 460, 'ge'))
    b.append(label(80, 860, 'EMBLEM'))
    b.append(f'<rect x="680" y="260" width="1160" height="260" rx="18" fill="{PANEL}"/>')
    b.append(ship_group(760, 275, 560, 'gs', 'glow'))
    b.append(word_group(1360, 340, 420, 'gw2'))
    b.append(label(680, 560, 'SHIP MARK'))
    b.append(label(1360, 560, 'WORDMARK'))
    b.append(f'<rect x="680" y="600" width="560" height="220" rx="18" fill="#FFFFFF"/>')
    b.append(emblem_group(720, 625, 170, 'gf', 'mono', FOREST))
    b.append(word_group(910, 680, 300, 'gf2', 'mono', FOREST))
    b.append(f'<rect x="1280" y="600" width="560" height="220" rx="18" fill="{LIME}"/>')
    b.append(emblem_group(1320, 625, 170, 'gk', 'mono', VOID))
    b.append(word_group(1510, 680, 300, 'gk2', 'mono', VOID))
    b.append(label(680, 860, 'ON LIGHT'))
    b.append(label(1280, 860, 'ON LIME'))
    # palette
    b.append(label(80, 950, 'COLOUR', 18, LIME, .5))
    sw = 205
    for i, (name, hexv, use) in enumerate(PALETTE):
        x = 80 + i * (sw + 18)
        stroke = ' stroke="#2A3527" stroke-width="2"' if hexv in (VOID, PANEL) else ''
        b.append(f'<rect x="{x}" y="980" width="{sw}" height="200" rx="14" fill="{hexv}"{stroke}/>')
        b.append(label(x, 1218, name.upper(), 17, WHITE, .2))
        b.append(label(x, 1246, hexv, 15, '#8FA08A', .1))
    # type
    b.append(label(80, 1330, 'TYPE', 18, LIME, .5))
    t, _ = tagline(80, 1395, 26, WHITE, tracking=.55)
    b.append(t)
    b.append(label(80, 1440, 'TAGLINE: MICHROMA, TRACKED WIDE, TWO WORDS IN LIME.  WORDMARK: CUSTOM LETTERING, USE THE ARTWORK.', 14))
    return svg(W, H, '\n'.join(b), title='ShipGuild brand kit')

PNG_JOBS = [
    # (svg relative path, png relative path, width)
    *[(f'svg/emblem/shipguild-emblem-{v}.svg', f'png/emblem/shipguild-emblem-{v}-{w}.png', w)
      for v in ('color', 'white', 'black', 'lime', 'forest') for w in (512, 1024, 2048, 4096)],
    ('svg/emblem/shipguild-app-icon.svg', 'png/emblem/shipguild-app-icon-1024.png', 1024),
    ('svg/emblem/shipguild-app-icon.svg', 'png/emblem/shipguild-app-icon-512.png', 512),
    *[(f'svg/ship/ship-mark-{v}.svg', f'png/ship/ship-mark-{v}-{w}.png', w)
      for v in ('glow', 'flat', 'white', 'black', 'lime') for w in (1200, 3000)],
    *[(f'svg/wordmark/shipguild-wordmark-{v}.svg', f'png/wordmark/shipguild-wordmark-{v}-{w}.png', w)
      for v in ('color', 'white', 'black', 'forest') for w in (1200, 3000)],
    *[(f'svg/lockup/shipguild-lockup-{v}.svg', f'png/lockup/shipguild-lockup-{v}-{w}.png', w)
      for v in ('horizontal-dark', 'horizontal-light') for w in (1600, 3200)],
    *[(f'svg/lockup/shipguild-lockup-{v}.svg', f'png/lockup/shipguild-lockup-{v}-{w}.png', w)
      for v in ('stacked-dark', 'stacked-light') for w in (1200, 2400)],
    ('svg/banner/shipguild-banner-1950x806.svg', 'png/banner/shipguild-banner-1950x806.png', 1950),
    ('svg/banner/shipguild-banner-1950x806.svg', 'png/banner/shipguild-banner-3900x1612.png', 3900),
    ('svg/banner/shipguild-x-header-1500x500.svg', 'png/banner/shipguild-x-header-1500x500.png', 1500),
    ('svg/banner/shipguild-x-header-1500x500.svg', 'png/banner/shipguild-x-header-3000x1000.png', 3000),
    ('svg/banner/shipguild-og-1200x630.svg', 'png/banner/shipguild-og-1200x630.png', 1200),
    ('svg/banner/shipguild-og-1200x630.svg', 'png/banner/shipguild-og-2400x1260.png', 2400),
    ('svg/banner/shipguild-linkedin-1584x396.svg', 'png/banner/shipguild-linkedin-1584x396.png', 1584),
    ('svg/banner/shipguild-linkedin-1584x396.svg', 'png/banner/shipguild-linkedin-3168x792.png', 3168),
    ('brand-sheet.svg', 'brand-sheet.png', 1920),
]

def export_pngs():
    for src, dst, w in PNG_JOBS:
        png(os.path.join(ROOT, src), dst, width=w)
    # favicon set
    fav = os.path.join(ROOT, 'svg/emblem/shipguild-favicon.svg')
    small = os.path.join(ROOT, 'svg/emblem/shipguild-favicon-small.svg')
    for w in (16, 32, 48, 180, 192, 512):
        name = 'apple-touch-icon.png' if w == 180 else f'favicon-{w}.png'
        png(small if w <= 48 else fav, f'png/favicon/{name}', width=w)
    from PIL import Image
    icons = [Image.open(os.path.join(ROOT, f'png/favicon/favicon-{w}.png')) for w in (16, 32, 48)]
    icons[2].save(os.path.join(ROOT, 'png/favicon/favicon.ico'), sizes=[(16, 16), (32, 32), (48, 48)],
                  append_images=icons[:2])

if __name__ == '__main__':
    files = build()
    write('brand-sheet.svg', brand_sheet())
    export_pngs()
    for k, v in files.items():
        print(k, os.path.relpath(v, ROOT))
