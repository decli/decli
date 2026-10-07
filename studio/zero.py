"""
studio/zero.py —— 方向 A「零 · 灰与橙」。

整页只有一条配色规则，版权页里也写明了：
    灰色的代码，是 AI 的产出；橙色，是我的判断。
橙色只用在四样东西上：那个 0、0 里那个从不打字的光标、「三件事」、我说的那一句话。
等宽字体也只给 AI 的产出用（代码、日志、调用次数）；其余的标签一律用无衬线。

首屏铺满 codeless 仓库里 AI 写的真代码，中间按整字挖出一个「0」—— 我手写的代码。

── 网格 ──
桌面画布宽 1692 = GitHub 个人主页 README 栏 846px 的两倍（1 单位 = 0.5px）；手机 648 = 324px 的两倍。
桌面只有两条竖线：页面边 0，和正文线 96（48px）。编号挂在 0，其余所有字都落在 96 上，卡片里也一样。
每一段以一条细线开头，结尾统一留 PB；段与段之间再加上 GitHub 自己的 22px 段距。
"""

from __future__ import annotations

import math
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import content as C  # noqa: E402
import kit  # noqa: E402
from kit import Doc, Stack, esc, num  # noqa: E402

DW, MW = 1692, 648
G = 96          # 桌面正文线
GM = 36         # 手机卡片内边
PB, PBM = 60, 60  # 段落底部留白：加上 GitHub 的段距 + 行尾空隙，段与段之间一律 116 单位（58px）

STACKS = {
    "disp": Stack(["instr", "serif-sc-sb"], kit.SYS_SERIF),
    "disp-it": Stack(["instr-it", "serif-sc-sb"], kit.SYS_SERIF),
    "head": Stack(["serif-sc-b"], kit.SYS_SERIF),
    "sans": Stack(["geist", "sans-sc"], kit.SYS_SANS),
    "sans-m": Stack(["geist-m", "sans-sc-m"], kit.SYS_SANS),
    "mono": Stack(["mono", "sans-sc"], kit.SYS_MONO),
    "mono-m": Stack(["mono-m", "sans-sc-m"], kit.SYS_MONO),
    "quote": Stack(["serif-sc-sb"], kit.SYS_SERIF),
}

T = {
    "light": dict(
        plate="#F2F0EB", plate2="#E8E5DE", ink="#131313", ink2="#45474D", ink3="#6E6A63",
        ai="#AEADA8", ai_k="#9C9B96", ai_s="#BDBBB6", ai_hi="#8C8A85", rule="#131313", rule_op=0.14,
        org="#F0561C", org_t="#C0400F", frame="#FFFFFF", frame_line="#131313", frame_op=0.10, shade=0.10,
        dim=0.0, tone=("#1c1c1c", "#f8f7f3"),
    ),
    "dark": dict(
        plate="#17181C", plate2="#202227", ink="#EDEBE6", ink2="#B5B3AD", ink3="#8E8A83",
        ai="#4B4E55", ai_k="#5A5D65", ai_s="#41444A", ai_hi="#6E727A", rule="#EDEBE6", rule_op=0.14,
        org="#FF6A2B", org_t="#FF8048", frame="#202227", frame_line="#EDEBE6", frame_op=0.12, shade=0.5,
        dim=0.0, tone=("#0f1012", "#8c8a84"),   # 截图最亮处也压在橙字下面
    ),
}

EASE = "cubic-bezier(.16,1,.3,1)"
BASE_CSS = (
    f".up{{animation:up 1s {EASE} both}}"
    "@keyframes up{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}"
    f".fade{{animation:fade 1s {EASE} both}}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    ".blink{animation:blink 1.06s steps(1,end) infinite}"
    "@keyframes blink{0%,55%{opacity:1}56%,100%{opacity:0}}"
    '.halt{font-feature-settings:"halt"}'
)


def doc(w, h, title):
    d = Doc(w, h, title, STACKS)
    d.style(BASE_CSS)
    return d


def delay(s):
    return f'style="animation-delay:{s:.2f}s"'


def rule(d, x1, y, x2, t, op=None, cls=None, extra=""):
    c = f' class="{cls}"' if cls else ""
    d.add(f'<path d="M{num(x1)} {num(y)}H{num(x2)}" stroke="{t["rule"]}" stroke-opacity="{num(op or t["rule_op"])}" '
          f'stroke-width="1.5"{c} {extra}/>')


def arrow_ne(d, x, y, s, color, sw=2.2, down=False):
    """↗（或 ↓）自己画：不同字体里箭头长得不一样。(x, y) 是左下角。"""
    if down:
        cx = x + s / 2
        d.add(f'<path d="M{num(cx)} {num(y - s * 1.1)}V{num(y)}M{num(cx - s * 0.42)} {num(y - s * 0.42)}L{num(cx)} {num(y)}L{num(cx + s * 0.42)} {num(y - s * 0.42)}" '
              f'fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')
        return
    d.add(f'<path d="M{num(x)} {num(y)}L{num(x + s)} {num(y - s)}M{num(x + s * 0.28)} {num(y - s)}H{num(x + s)}V{num(y - s * 0.72)}" '
          f'fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')


LATIN = re.compile(r"[A-Za-z0-9.+/#&·:\-]+(?: [A-Za-z0-9.+/#&·:\-]+)*")


def label(d, x, y, s, color, size=21, stack="sans-m", track=0.12, anchor=None, cls=None, extra=""):
    """小标签：西文大写、加字距；中文不加字距（中文加字距显得拘谨）。返回宽度。"""
    parts, pos = [], 0
    for m in LATIN.finditer(s):
        if m.start() > pos:
            parts.append((s[pos:m.start()], stack, color, 0.02))
        parts.append((m.group().upper(), stack, color, track))
        pos = m.end()
    if pos < len(s):
        parts.append((s[pos:], stack, color, 0.02))
    return d.spans(x, y, parts, size, anchor=anchor, cls=cls, extra=extra)


def lines(d, x, y, text, stack, size, color, width, lh, cls=None, start=None, step=0.05, halt=False, max_lines=None,
          justify=True):
    """多行正文，返回最后一行的基线。
    一两行的短句按词折、右边参差；三行以上的段落改成齐行：按字填满，非末行用 textLength 两端对齐
    （中文正文的老规矩，段落右边是一条直线）。"""
    ls = d.wrap(text, stack, size, width, halt=halt, max_lines=max_lines)
    just = justify and len(ls) >= 3 and not max_lines and width / size >= 22   # 窄栏（手机）齐行会把字距撑散，改用按词参差
    if just:
        # 齐行时「——」换成一个整的两字线（⸺），字距拉开也不会断成两截
        ls = kit.justify(text.replace("——", "⸺"), d.stacks[stack], size, width, halt=halt)
    for i, ln in enumerate(ls):
        extra = delay(start + i * step) if start is not None else ""
        if just and i < len(ls) - 1 and d.width(ln, stack, size) > width * 0.82:
            extra += f' textLength="{num(width)}" lengthAdjust="spacing"'
        d.text(x, y + i * lh, ln, stack, size, color, cls=cls, extra=extra, halt=halt)
    return y + (len(ls) - 1) * lh


# ═══════════════════════════════════════════════════════════════════
#  首屏：代码墙，按整字挖出一个 0
# ═══════════════════════════════════════════════════════════════════

KW = re.compile(r"\b(def|class|return|if|elif|else|for|while|in|not|and|or|is|None|True|False|import|from|as|with|"
                r"try|except|raise|self|lambda|yield|pass|break|continue)\b")
STR = re.compile(r"(\"[^\"]*\"|'[^']*')")


def code_rows(cols, n):
    """把真代码一行行接起来，铺成一面满满的墙：一屏的产出，看不清也不必看清。"""
    stream = "  ".join(ln.strip() for ln in C.code_lines(400))
    rows, i = [], 0
    while len(rows) < n:
        chunk = stream[i:i + cols]
        if len(chunk) < cols:
            i = 0
            continue
        rows.append(chunk)
        i += cols
    return rows


def tint(row):
    """关键字深一档、字符串浅一档 —— 还是灰，只是有了纹理。"""
    out, last = [], 0
    marks = sorted([(m.start(), m.end(), "k") for m in KW.finditer(row)] +
                   [(m.start(), m.end(), "s") for m in STR.finditer(row)])
    for a, b, k in marks:
        if a < last:
            continue
        seg = row[a:b]
        if seg.strip():
            out.append(esc(row[last:a]))
            out.append(f'<tspan class="{k}">{esc(seg)}</tspan>')
            last = b
    out.append(esc(row[last:]))
    return "".join(out)


def glyph_contours(ch, size, x, y_base, sx=1.0, key="instr"):
    """字形轮廓 → (SVG path, [多边形点列])。多边形用来算哪些字格落在 0 里。"""
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    f = kit.face(key)
    gs = f.font.getGlyphSet()
    g = gs[f.cmap[ord(ch)]]
    s = size / f.upm
    tr = (s * sx, 0, 0, -s, x, y_base)
    pen = SVGPathPen(gs)
    g.draw(TransformPen(pen, tr))
    path = re.sub(r"-?\d+\.\d+", lambda m: num(round(float(m.group()), 1)), pen.getCommands())
    rec = RecordingPen()
    g.draw(TransformPen(rec, tr))
    polys, cur, last = [], [], (0, 0)
    for op, args in rec.value:
        if op == "moveTo":
            cur = [args[0]]
            last = args[0]
        elif op == "lineTo":
            cur.append(args[0])
            last = args[0]
        elif op in ("qCurveTo", "curveTo"):
            pts = [last] + list(args)
            for k in range(1, len(pts)):
                a, b = pts[k - 1], pts[k]
                for u in (0.25, 0.5, 0.75, 1.0):
                    cur.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
            last = args[-1]
        elif op in ("closePath", "endPath"):
            if cur:
                polys.append(cur)
            cur = []
    polys.sort(key=lambda p: -(max(q[0] for q in p) - min(q[0] for q in p)))
    return path, polys


def span_at(poly, y):
    xs = []
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    return (min(xs), max(xs)) if xs else None


def carve(rows, x0, y0, lh, cw, holes):
    """把落在 holes 里的字格换成空格。holes = [(多边形 或 矩形 (x0,y0,x1,y1), 外扩)]。"""
    out = []
    for i, row in enumerate(rows):
        top, bot = y0 + i * lh, y0 + (i + 1) * lh
        chars = list(row)
        for hole in holes:
            if hole[0] == "ring":
                _, outer, inner, pad = hole
                ys = (top - pad * 0.6, (top + bot) / 2, bot + pad * 0.6)
                so = [sp for sp in (span_at(outer, yy) for yy in ys) if sp]
                if not so:
                    continue
                a = min(sp[0] for sp in so) - pad
                b = max(sp[1] for sp in so) + pad
                si = [span_at(inner, yy) for yy in ys] if inner else [None]
                if all(si):        # 这一行穿过 0 的内圈：内圈里（往里再收一点）的字留着
                    c = max(sp[0] for sp in si) + pad
                    e = min(sp[1] for sp in si) - pad
                else:
                    c = e = None
                for k in range(len(chars)):
                    cx0 = x0 + k * cw
                    if cx0 + cw > a and cx0 < b and not (c is not None and cx0 >= c and cx0 + cw <= e):
                        chars[k] = " "
                continue
            shape, pad = hole
            if isinstance(shape, tuple):
                rx0, ry0, rx1, ry1 = shape
                if bot < ry0 or top > ry1:
                    continue
                spans = [(rx0, rx1)]
            else:
                spans = [sp for sp in (span_at(shape, yy) for yy in (top - pad * 0.6, (top + bot) / 2, bot + pad * 0.6)) if sp]
                if not spans:
                    continue
            a = min(sp[0] for sp in spans) - pad
            b = max(sp[1] for sp in spans) + pad
            for k in range(len(chars)):
                cx0 = x0 + k * cw
                if cx0 + cw > a and cx0 < b:
                    chars[k] = " "
        out.append("".join(chars))
    return out


def code_wall(d, t, x0, y0, w, h, size, lh, holes_fn, fade=None, start=0.0, step=0.018):
    cw = 0.6 * size
    cols = int(w / cw)
    nrows = int(h / lh)
    rows = carve(code_rows(cols, nrows), x0, y0, lh, cw, holes_fn(cw))
    gid = d.uid("cw")

    def paint(name, color):
        if not fade:
            return color
        d.deff(f'<linearGradient id="{gid}{name}" x1="{num(fade[0])}" x2="{num(fade[1])}" y1="0" y2="0" '
               f'gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{color}"/>'
               f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>')
        return f"url(#{gid}{name})"

    base, kw, st = paint("a", t["ai"]), paint("k", t["ai_k"]), paint("s", t["ai_s"])
    d.style(".cl{animation:cl .35s ease-out both}@keyframes cl{from{opacity:0}to{opacity:1}}"
            f".k{{fill:{kw}}}.s{{fill:{st}}}")
    body = []
    for i, ln in enumerate(rows):
        d.note("mono", ln)
        edge = min(i + 1, nrows - i)
        op = f' opacity="{[0.35, 0.7][edge - 1]}"' if edge <= 2 else ""
        body.append(f'<text x="{num(x0)}" y="{num(y0 + (i + 0.78) * lh)}" class="cl" '
                    f'style="animation-delay:{start + i * step:.2f}s"{op} xml:space="preserve">{tint(ln)}</text>')
    d.add(f'<g font-family="{esc(STACKS["mono"].css())}" font-size="{num(size)}" fill="{base}">{"".join(body)}</g>')


def zero_figure(d, t, cx, top, size, sx, sw, cursor, t0=0.6):
    """0 的橙色轮廓（一笔描出）+ 正中一个光标。返回 (path, 外轮廓多边形, 底边 y)。"""
    k = size / 1000
    f = kit.face("instr")
    from fontTools.pens.boundsPen import BoundsPen
    gs = f.font.getGlyphSet()
    bp = BoundsPen(gs)
    gs[f.cmap[ord("0")]].draw(bp)
    bx0, by0, bx1, by1 = bp.bounds
    zx = cx - (bx0 + bx1) / 2 * k * sx
    base = top + by1 * k
    path, polys = glyph_contours("0", size, zx, base, sx)
    d.style(f".zo{{stroke-dasharray:6000;animation:draw 1.1s cubic-bezier(.65,0,.35,1) {t0:.2f}s both}}"
            "@keyframes draw{from{stroke-dashoffset:6000}to{stroke-dashoffset:0}}")
    d.add(f'<path class="zo" d="{path}" fill="none" stroke="{t["org"]}" stroke-width="{sw}" stroke-linejoin="round"/>')
    cy = base - (by1 + by0) / 2 * k
    cw_, ch_ = cursor
    t1 = t0 + 0.7
    d.add(f'<g class="fade" style="animation-delay:{t1:.2f}s"><rect class="blink" style="animation-delay:{t1:.2f}s" '
          f'x="{num(cx - cw_ / 2)}" y="{num(cy - ch_ / 2)}" width="{cw_}" height="{ch_}" fill="{t["org"]}"/></g>')
    area = lambda pl: (max(x for x, _ in pl) - min(x for x, _ in pl)) * (max(y for _, y in pl) - min(y for _, y in pl))  # noqa: E731
    polys = sorted(polys, key=area, reverse=True)
    outer, inner = polys[0], (polys[1] if len(polys) > 1 else None)
    cur = (cx - cw_ / 2, cy - ch_ / 2, cx + cw_ / 2, cy + ch_ / 2)

    def holes(*extra):
        # 只挖 0 的笔画那一圈：0 里面照样是 AI 的代码，正中给光标让出一小块
        return lambda cw: [("ring", outer, inner, cw * 0.9), ((cur[0] - cw * 2.2, cur[1] - ch_ * 0.35, cur[2] + cw * 2.2,
                                                                cur[3] + ch_ * 0.35), 0)] + [(e, 0) for e in extra]
    return path, outer, base - by0 * k, holes


def hero(t, mobile=False):
    title = f"decli — {C.HEAD_A}{C.HEAD_B}" + "".join(C.LEDE)
    lede = C.LEDE[0] + C.LEDE[2]
    cap1 = [("图 0", "sans-m", t["ink3"]), ("  我手写的代码", "sans", t["ink"])]
    kinds = len({w["cat_zh"] for w in C.WORKS})
    stats = [(str(C.N), "个作品", "works"), (str(C.LIVE), "个可在线体验", "live"), (str(kinds), "种形态", "kinds")]
    kick = [("人出判断", "sans-m", t["ink"], 0.04), ("  ·  AI 执行", "sans-m", t["ink3"], 0.04)]
    if not mobile:
        W, H = DW, 1000
        d = doc(W, H + PB + 12, title)
        d.add(f'<rect width="{W}" height="{H}" rx="16" fill="{t["plate"]}"/>')
        yb = 96
        wn = d.text(G, yb, "decli", "disp-it", 58, t["ink"], cls="fade")
        label(d, G + wn + 26, yb - 4, C.ROLE, t["ink3"], 23, cls="fade")
        label(d, W - G - 34, yb - 4, "decli.github.io", t["ink3"], 23, anchor="end", cls="fade")
        arrow_ne(d, W - G - 17, yb - 5, 15, t["ink3"], 2.2)
        rule(d, G, yb + 32, W - G, t)
        wy0, lh = yb + 60, 25
        wh = H - wy0 - 50
        zcx, ztop, zsize, zsx = 470, wy0 + 44, 820, 1.2
        base_y = wy0 + (29 + 0.78) * lh      # 最后一行字的基线，正好落在代码墙的第 30 行上
        cap_w = d.width("其余：AI 为 codeless 写的真代码", "sans", 25) + 24
        cap_box = (G - 4, base_y - 78, G + cap_w, base_y + 16)
        at = len(d.body)
        z = zero_figure(d, t, zcx, ztop, zsize, zsx, 2.2, (18, 56), t0=0.62)
        z_body = d.body[at:]
        d.body = d.body[:at]
        code_wall(d, t, G, wy0, 828 - G, wh, 16, lh, z[3](cap_box),
                  fade=(730, 836), start=0.05)
        d.body += z_body
        zbottom = z[2]
        d.spans(G, base_y - 2 * lh, [(s_, st, c, 0.02) for s_, st, c in cap1], 25, cls="fade", extra=delay(2.0))
        d.text(G, base_y, "其余：AI 为 codeless 写的真代码", "sans", 25, t["ink3"], cls="fade", extra=delay(2.05))
        x0 = 924
        yk = wy0 + 0.78 * lh + 6          # 小标题的字顶跟代码墙第一行对齐
        d.spans(x0, yk, kick, 25, cls="up", extra=delay(1.35))
        hs = 104
        y = yk + 150
        d.text(x0 - 4, y, C.HEAD_A, "head", hs, t["ink"], cls="up", extra=delay(1.5), halt=True)
        y += hs * 1.2
        d.text(x0 - 4, y, C.HEAD_B, "head", hs, t["ink"], cls="up", extra=delay(1.62), halt=True)
        y += 96
        lines(d, x0, y, lede, "sans", 31, t["ink2"], W - G - x0, 50, cls="up", start=1.75, justify=False)
        rule(d, x0, zbottom, W - G, t, cls="fade", extra='style="animation-delay:1.95s"')
        # 三个数：各自的宽度量出来，剩下的空平均分进两个间隔里，最后一个正好收在右边线上
        ws = []
        for n, zh, en in stats:
            nw = d.width(n, "disp", 104)
            ws.append((nw, nw + 14 + max(d.width(zh, "sans", 26), d.width(en.upper(), "sans-m", 20, 0.12))))
        gap = (W - G - x0 - sum(b for _, b in ws)) / (len(ws) - 1)
        x = x0
        for i, ((n, zh, en), (nw, bw)) in enumerate(zip(stats, ws)):
            dl = 2.0 + i * 0.07
            d.text(x, base_y, n, "disp", 104, t["ink"], cls="up", extra=delay(dl))
            label(d, x + nw + 14, base_y - lh - 13, en, t["ink3"], 20, cls="up", extra=delay(dl + 0.04))
            d.text(x + nw + 14, base_y, zh, "sans", 26, t["ink2"], cls="up", extra=delay(dl + 0.04))
            x += bw + gap
        return d
    # ── 手机 ──
    W = MW
    lede_l = kit.wrap(lede, STACKS["sans"], 29, W - 2 * GM)
    yb = 74
    wy0, wh = yb + 46, 600
    y_k = wy0 + wh + 70
    hs = 78
    y_h1 = y_k + 98
    y_h2 = y_h1 + hs * 1.2
    y_l = y_h2 + 78
    y_r = y_l + (len(lede_l) - 1) * 46 + 56
    y_n = y_r + 104
    H = y_n + 84
    d = doc(W, H + PBM, title)
    d.add(f'<rect width="{W}" height="{num(H)}" rx="14" fill="{t["plate"]}"/>')
    d.text(GM, yb, "decli", "disp-it", 50, t["ink"], cls="fade")
    label(d, W - GM, yb - 6, C.ROLE, t["ink3"], 21, anchor="end", cls="fade")
    rule(d, GM, yb + 24, W - GM, t)
    lh = 22
    base_cap = wy0 + (int(wh / lh) - 1 + 0.78) * lh
    cap_w = d.width("其余：AI 写的真代码", "sans", 24) + 20
    cap_box = (GM - 4, base_cap - 70, GM + cap_w, base_cap + 16)
    at = len(d.body)
    z = zero_figure(d, t, W / 2, wy0 + 36, 560, 1.28, 2, (14, 42), t0=0.62)
    z_body = d.body[at:]
    d.body = d.body[:at]
    code_wall(d, t, GM, wy0, W - 2 * GM, wh, 14, lh, z[3](cap_box), start=0.05)
    d.body += z_body
    d.spans(GM, base_cap - 2 * lh - 2, [(s_, st, c, 0.02) for s_, st, c in cap1], 24, cls="fade", extra=delay(2.0))
    d.text(GM, base_cap, "其余：AI 写的真代码", "sans", 24, t["ink3"], cls="fade", extra=delay(2.05))
    d.spans(GM, y_k, kick, 24, cls="up", extra=delay(1.35))
    d.text(GM - 3, y_h1, C.HEAD_A, "head", hs, t["ink"], cls="up", extra=delay(1.5), halt=True)
    d.text(GM - 3, y_h2, C.HEAD_B, "head", hs, t["ink"], cls="up", extra=delay(1.62), halt=True)
    for i, ln in enumerate(lede_l):
        d.text(GM, y_l + i * 46, ln, "sans", 29, t["ink2"], cls="up", extra=delay(1.75 + i * 0.05))
    rule(d, GM, y_r, W - GM, t, cls="fade", extra='style="animation-delay:1.95s"')
    colw = (W - 2 * GM) / 3
    for i, (n, zh, en) in enumerate(stats):
        x = GM + i * colw
        dl = 2.0 + i * 0.07
        d.text(x, y_n, n, "disp", 92, t["ink"], cls="up", extra=delay(dl))
        d.text(x, y_n + 44, zh, "sans", 24, t["ink2"], cls="up", extra=delay(dl + 0.04))
    return d


# ═══════════════════════════════════════════════════════════════════
#  履历：首屏下面的一小段，回答「这些判断是谁做的、凭什么」
#  不编号、不占一章：首屏是标题和导语，这一段是署名；01 起的章节照旧
#  一条时间线 —— 前四家挤在左边，「现在」那家单独隔开、实心点；
#  下面两栏正好分在「过去」和「现在」底下。没有橙色：橙色只标判断，履历不是判断
# ═══════════════════════════════════════════════════════════════════

def about(t, mobile=False):
    title = "履历：" + C.BIO
    past, now = C.CAREER[:-1], C.CAREER[-1]
    if not mobile:
        W = DW
        d = doc(W, 600, title)
        rule(d, 0, 1, W, t)
        d.text(G, 92, "判断从哪来", "head", 44, t["ink"], halt=True)
        label(d, W, 92, "background", t["ink3"], 23, anchor="end")
        yt = 196                                   # 时间线
        xn = G + 0.56 * (W - G)                    # 「现在」那个点；右栏也从这里起
        step = (xn - G - 260) / (len(past) - 1)       # 前四家挤一挤，跟「现在」之间空出一段
        xs = [G + i * step for i in range(len(past))]
        d.add(f'<path d="M{G} {yt}H{num(xn)}" stroke="{t["rule"]}" stroke-opacity=".30" stroke-width="2"/>')
        d.add(f'<path d="M{num(xn)} {yt}H{W}" stroke="{t["rule"]}" stroke-opacity=".22" stroke-width="2" stroke-dasharray="2 9"/>')
        for i, (x, name) in enumerate(zip(xs, past)):
            d.add(f'<circle cx="{num(x)}" cy="{yt}" r="6" fill="{t["ink3"]}"/>')
            d.text(x - 2, yt + 52, name, "sans-m", 28, t["ink2"], cls="up", extra=delay(0.2 + i * 0.08))
        d.add(f'<circle cx="{num(xn)}" cy="{yt}" r="19" fill="none" stroke="{t["ink"]}" stroke-opacity=".22" stroke-width="2"/>'
              f'<circle cx="{num(xn)}" cy="{yt}" r="9" fill="{t["ink"]}"/>')
        label(d, xn - 2, yt - 38, "现在 · now", t["ink3"], 20)
        d.text(xn - 2, yt + 52, now, "sans-m", 28, t["ink"], cls="up", extra=delay(0.52))
        yh = yt + 150
        colL = xn - G - 72
        for x, (head, body), w_, dl in ((G, C.CAREER_PAST, colL, 0.6), (xn, C.CAREER_NOW, W - xn, 0.7)):
            d.text(x - 2, yh, head, "head", 36, t["ink"], cls="up", extra=delay(dl), halt=True)
            yb = lines(d, x, yh + 56, body, "sans", 28, t["ink2"], w_, 46, justify=False, cls="up", start=dl + 0.06)
        d.h = max(yb, yh + 56 + 46) + PB + 10
        return d
    W = MW
    d = doc(W, 2000, title)
    rule(d, 0, 1, W, t)
    d.text(0, 80, "判断从哪来", "head", 40, t["ink"], halt=True)
    label(d, W, 80, "background", t["ink3"], 20, anchor="end")
    yt = 176
    xn = W - 110
    step = (xn - 170) / (len(past) - 1)
    xs = [i * step + 7 for i in range(len(past))]
    d.add(f'<path d="M7 {yt}H{num(xn)}" stroke="{t["rule"]}" stroke-opacity=".30" stroke-width="2"/>')
    d.add(f'<path d="M{num(xn)} {yt}H{W}" stroke="{t["rule"]}" stroke-opacity=".22" stroke-width="2" stroke-dasharray="2 8"/>')
    for x, name in zip(xs, past):
        d.add(f'<circle cx="{num(x)}" cy="{yt}" r="5" fill="{t["ink3"]}"/>')
        d.text(x - 6, yt + 46, name, "sans-m", 24, t["ink2"])
    d.add(f'<circle cx="{num(xn)}" cy="{yt}" r="16" fill="none" stroke="{t["ink"]}" stroke-opacity=".22" stroke-width="2"/>'
          f'<circle cx="{num(xn)}" cy="{yt}" r="8" fill="{t["ink"]}"/>')
    label(d, xn - 6, yt - 32, "现在", t["ink3"], 19)
    d.text(xn - 6, yt + 46, now, "sans-m", 24, t["ink"])
    y = yt + 136
    for k, (head, body) in enumerate((C.CAREER_NOW, C.CAREER_PAST)):   # 手机上先说现在
        d.text(0, y, head, "head", 32, t["ink"], halt=True)
        y = lines(d, 0, y + 50, body, "sans", 26, t["ink2"], W, 42, justify=False)
        y += 76
    d.h = y - 76 + PBM + 10
    return d


# ═══════════════════════════════════════════════════════════════════
#  段落标题
# ═══════════════════════════════════════════════════════════════════

def section_head(d, t, no, zh, en, mobile=False):
    W = d.w
    rule(d, 0, 1, W, t)
    if mobile:
        by = 78
        d.text(0, by, no, "disp-it", 44, t["ink3"])
        d.text(62, by, zh, "head", 46, t["ink"], halt=True)
        label(d, W, by, en, t["ink3"], 20, anchor="end")
        return by + 46
    by = 96
    d.text(0, by, no, "disp-it", 54, t["ink3"])
    d.text(G, by, zh, "head", 60, t["ink"], halt=True)
    label(d, W, by, en, t["ink3"], 23, anchor="end")
    return by + 60


def head_only(t, no, zh, en, mobile=False):
    d = doc(MW if mobile else DW, 10, f"{no} {zh}")
    y = section_head(d, t, no, zh, en, mobile=mobile)
    d.h = y - (8 if mobile else 14)
    return d


# ═══════════════════════════════════════════════════════════════════
#  01 方法：两条泳道
# ═══════════════════════════════════════════════════════════════════

def cubic_pts(p0, p1, p2, p3, n=48):
    out = []
    for i in range(n + 1):
        u = i / n
        out.append(((1 - u) ** 3 * p0[0] + 3 * (1 - u) ** 2 * u * p1[0] + 3 * (1 - u) * u ** 2 * p2[0] + u ** 3 * p3[0],
                    (1 - u) ** 3 * p0[1] + 3 * (1 - u) ** 2 * u * p1[1] + 3 * (1 - u) * u ** 2 * p2[1] + u ** 3 * p3[1]))
    return out


class Path:
    def __init__(self, x, y):
        self.d = [f"M{num(x)} {num(y)}"]
        self.p = (x, y)
        self.len = 0.0
        self.marks = {}

    def _cubic(self, c1, c2, x, y):
        pts = cubic_pts(self.p, c1, c2, (x, y))
        self.len += sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
        self.d.append(f"C{num(c1[0])} {num(c1[1])} {num(c2[0])} {num(c2[1])} {num(x)} {num(y)}")
        self.p = (x, y)
        return self

    def line(self, x, y):
        self.len += math.hypot(x - self.p[0], y - self.p[1])
        self.d.append(f"L{num(x)} {num(y)}")
        self.p = (x, y)
        return self

    def s(self, x, y):
        """横向 S：水平离开、水平到达。"""
        x0, y0 = self.p
        return self._cubic((x0 + (x - x0) * 0.45, y0), (x - (x - x0) * 0.45, y), x, y)

    def v(self, x, y):
        """竖向 S：竖着离开、竖着到达。"""
        x0, y0 = self.p
        return self._cubic((x0, y0 + (y - y0) * 0.62), (x, y - (y - y0) * 0.62), x, y)

    def mark(self, key):
        self.marks[key] = self.len
        return self

    def __str__(self):
        return "".join(self.d)


def pulse(d, t, path: Path, dur=7.5, move=0.62, seg=56, width=3, runs=3, hits=()):
    """沿路径跑一小段灰色亮线（带渐弱的尾巴），跑三趟就停。经过人的节点时，那个橙点闪一下。"""
    L = path.len
    pid = d.uid("pl")
    m = move * 100
    d.style(f"@keyframes {pid}{{0%{{stroke-dashoffset:{num(seg)}}}{m:.1f}%,100%{{stroke-dashoffset:-{num(L)}}}}}")
    for k, (op, lag) in enumerate([(1.0, 0), (0.45, 0.6 * seg), (0.18, 1.2 * seg)]):
        d.add(f'<path d="{path}" fill="none" stroke="{t["ai_hi"]}" stroke-opacity="{op}" stroke-width="{width}" '
              f'stroke-linecap="round" stroke-dasharray="{num(seg * 0.6)} {num(L + seg * 2)}" '
              f'style="animation:{pid} {dur}s cubic-bezier(.45,0,.55,1) {lag / L * dur * move:.2f}s {runs} both"/>')
    for (x, y), at in hits:
        f = at / L * m
        hid = d.uid("hit")
        d.style(f"@keyframes {hid}{{0%,{max(0, f - 2):.1f}%{{opacity:0;transform:scale(.6)}}{f + 1:.1f}%{{opacity:.55}}"
                f"{f + 9:.1f}%,100%{{opacity:0;transform:scale(1.9)}}}}")
        d.add(f'<circle cx="{num(x)}" cy="{num(y)}" r="12" fill="none" stroke="{t["org"]}" stroke-width="2" opacity="0" '
              f'style="transform-box:fill-box;transform-origin:center;animation:{hid} {dur}s linear {runs}"/>')


def human_node(d, t, x, y, r=9):
    d.add(f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r * 2.1)}" fill="{t["org"]}" fill-opacity=".14"/>'
          f'<circle cx="{num(x)}" cy="{num(y)}" r="{r}" fill="{t["org"]}"/>')


def ai_node(d, t, x, y, s=9):
    d.add(f'<rect x="{num(x - s / 2)}" y="{num(y - s / 2)}" width="{s}" height="{s}" fill="{t["ink3"]}"/>')


def zero_line(d, t, x, y, size, anchor=None):
    """「我手写的代码：0 行」—— 0 跟前后的字同一字体、同一基线，只换成橙色。"""
    parts = [("我手写的代码：", "sans", t["ink2"], 0), ("0", "head", t["org"], 0), (" 行", "sans", t["ink2"], 0)]
    return d.spans(x, y, parts, size, anchor=anchor)


def draw_on(d, path: Path, dur=2.8, t0=0.3):
    """路径一笔画出来（只画一遍），返回「画到某个长度时是第几秒」的函数，节点就在那一刻冒出来。"""
    L = path.len
    pid = d.uid("dr")
    d.style(f"@keyframes {pid}{{from{{stroke-dashoffset:{num(L)}}}to{{stroke-dashoffset:0}}}}"
            f".{pid}{{stroke-dasharray:{num(L)};animation:{pid} {dur}s cubic-bezier(.45,0,.35,1) {t0}s both}}")
    return pid, (lambda at: t0 + dur * (at / L) ** 0.95)


def pop(d, at):
    cid = d.uid("pp")
    d.style(f"@keyframes {cid}{{from{{opacity:0;transform:scale(.4)}}to{{opacity:1;transform:none}}}}"
            f".{cid}{{transform-box:fill-box;transform-origin:center;animation:{cid} .45s cubic-bezier(.34,1.56,.64,1) {at:.2f}s both}}")
    return cid


def method(t, mobile=False):
    # AI 的第一步（写需求）落在定方向和设规则之间，其余几步排在设规则和验结果之间
    first, run = C.AI_DOES[0], C.AI_DOES[1:]
    title = ("方法：人出判断，AI 执行。我只做三件事：定方向、设规则、验结果；"
             f"流程一步不少，{'、'.join(C.AI_DOES)}全部由 AI 执行。")
    if not mobile:
        W = DW
        d = doc(W, 800, title)
        y0 = section_head(d, t, "01", "方法", "method")
        yh, ya = y0 + 168, y0 + 380
        for yy in (yh, ya):
            d.add(f'<path d="M{G + 150} {num(yy)}H{W}" stroke="{t["rule"]}" stroke-opacity=".09" stroke-width="1.5" '
                  f'stroke-dasharray="2 9"/>')
        d.text(0, yh + 15, "人", "head", 46, t["ink"])
        d.text(G, yh - 2, "判断", "sans-m", 26, t["ink2"])
        label(d, G, yh + 30, "judgment", t["ink3"], 20)
        d.text(0, ya + 16, "AI", "disp", 52, t["ink3"])
        d.text(G, ya - 2, "执行", "sans-m", 26, t["ink3"])
        label(d, G, ya + 30, "execution", t["ink3"], 20)
        # 四次人 ↔ AI 的换道一样长（165），AI 的五步等距（130）
        A, AI1, B = 382, 547, 712
        size = 25
        # AI 后面几步：字和字之间的空一样大（不是点和点等距 ——「UI 交互设计」比「写代码」长一倍）
        lw = [d.width(c, "sans", size) for c in run]
        span0, span1 = 877 - lw[0] / 2, 1397 + lw[-1] / 2
        g_ = (span1 - span0 - sum(lw)) / (len(lw) - 1)
        xs, xx = [], span0
        for w_ in lw:
            xs.append(xx + w_ / 2)
            xx += w_ + g_
        Cx = xs[-1] + 165
        p = Path(A, yh).mark("A").s(AI1, ya).mark("a1").s(B, yh).mark("B").s(xs[0], ya)
        for k, x in enumerate(xs):
            if k:
                p.line(x, ya)
            p.mark(f"x{k}")
        p.s(Cx, yh).mark("C")
        d.add(f'<path d="{p}" fill="none" stroke="{t["rule"]}" stroke-opacity=".10" stroke-width="2"/>')
        pid, when = draw_on(d, p)
        d.add(f'<path class="{pid}" d="{p}" fill="none" stroke="{t["rule"]}" stroke-opacity=".30" stroke-width="2"/>')
        for (name, desc, _), x, key in zip(C.STEPS, (A, B, Cx), ("A", "B", "C")):
            anchor = "middle"
            tx = min(x, W - max(d.width(name, "head", 40), d.width(desc, "sans", 26)) / 2)
            d.add(f'<g class="{pop(d, when(p.marks[key]))}">')
            human_node(d, t, x, yh)
            d.add("</g>")
            d.text(tx, yh - 80, name, "head", 40, t["ink"], anchor=anchor)
            d.text(tx, yh - 38, desc, "sans", 26, t["ink2"], anchor=anchor)
        for c, x, key in [(first, AI1, "a1")] + [(c, x, f"x{k}") for k, (c, x) in enumerate(zip(run, xs))]:
            d.add(f'<g class="{pop(d, when(p.marks[key]))}">')
            ai_node(d, t, x, ya)
            d.add("</g>")
            d.text(x, ya + 54, c, "sans", size, t["ink3"], anchor="middle")
        d.h = ya + 54 + PB + 16
        return d
    W = MW
    d = doc(W, 1200, title)
    y0 = section_head(d, t, "01", "方法", "method", mobile=True)
    y = y0 + 48
    human_node(d, t, 14, y - 8, 6)
    d.text(36, y, "人 · 判断", "sans-m", 23, t["ink2"])
    ai_node(d, t, 214, y - 8, 9)
    d.text(232, y, "AI · 执行", "sans-m", 23, t["ink3"])
    y += 96
    xh, xa = 14, 74
    seq = [("h", 0), ("a", first), ("h", 1)] + [("a", c) for c in run] + [("h", 2)]
    pts, prev = [], None
    for kind, v in seq:
        if prev is not None:
            y += 128 if prev == "h" else (84 if kind == "h" else 56)
        pts.append((xh if kind == "h" else xa, y, kind, v))
        prev = kind
    p = Path(pts[0][0], pts[0][1])
    at = [0.0]
    for (x, yy, k, v), pr in zip(pts[1:], pts[:-1]):
        if pr[2] == k:
            p.line(x, yy)
        elif pr[2] == "h":
            p.line(pr[0], pr[1] + 74)
            p.v(x, yy)
        else:
            p.v(x, yy)
        at.append(p.len)
    d.add(f'<path d="{p}" fill="none" stroke="{t["rule"]}" stroke-opacity=".10" stroke-width="2"/>')
    pid, when = draw_on(d, p, dur=2.6)
    d.add(f'<path class="{pid}" d="{p}" fill="none" stroke="{t["rule"]}" stroke-opacity=".30" stroke-width="2"/>')
    for (x, yy, k, v), a in zip(pts, at):
        d.add(f'<g class="{pop(d, when(a))}">')
        (human_node(d, t, x, yy, 8) if k == "h" else ai_node(d, t, x, yy, 8))
        d.add("</g>")
        if k == "h":
            name, desc, _ = C.STEPS[v]
            d.text(x + 32, yy + 12, name, "head", 36, t["ink"])
            d.text(x + 32, yy + 54, desc, "sans", 26, t["ink2"])
        else:
            d.text(x + 26, yy + 9, v, "sans", 26, t["ink3"])
    d.h = pts[-1][1] + 54 + PBM
    return d


# ═══════════════════════════════════════════════════════════════════
#  02 正在做：codeless —— 一句话进去，一个网站出来（只播一遍，停在完成的样子）
# ═══════════════════════════════════════════════════════════════════

def appear(d, at, dur=0.45, dy=6):
    """只播一遍的出场：动画结束 = 默认样子，所以不播动画的地方看到的就是完成态。"""
    cid = d.uid("ap")
    d.style(f"@keyframes {cid}{{from{{opacity:0;transform:translateY({dy}px)}}to{{opacity:1;transform:none}}}}"
            f".{cid}{{animation:{cid} {dur}s {EASE} {at:.2f}s both}}")
    return cid


def shot_ref(slug):
    return C.SHOT[slug]


def browser(d, t, x, y, w, slug, title, reveal=None, appear_at=None):
    """极简浏览器框 + 真截图。reveal=秒：截图从上往下擦出来（只播一遍）；appear_at：框本身淡入的时刻。"""
    bar = 42
    sp = shot_ref(slug)
    uri, iw, ih = kit.shot_uri(sp["rel"], int(w), crop=sp.get("crop"), redact=sp.get("redact", ()),
                               stack=sp.get("stack"), tone=t.get("tone"))
    ih_u = w * ih / iw
    h = bar + ih_u
    cid = d.uid("bw")
    if appear_at is not None:
        d.add(f'<g class="{appear(d, appear_at, 0.5, 0)}">')
    d.deff(f'<clipPath id="{cid}"><rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" rx="12"/></clipPath>')
    d.add(f'<g clip-path="url(#{cid})"><rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="{t["frame"]}"/>')
    for i in range(3):
        d.add(f'<circle cx="{num(x + 26 + i * 20)}" cy="{num(y + bar / 2)}" r="5.5" fill="{t["ink3"]}" fill-opacity=".35"/>')
    d.text(x + w / 2, y + bar / 2 + 7, title, "sans", 21, t["ink3"], anchor="middle")
    if reveal is not None:
        wid = d.uid("wp")
        d.style(f"@keyframes {wid}{{from{{transform:scaleY(0)}}to{{transform:none}}}}"
                f".{wid}{{transform-box:fill-box;transform-origin:50% 0;animation:{wid} .9s cubic-bezier(.65,0,.35,1) {reveal:.2f}s both}}")
        mid = d.uid("wm")
        d.deff(f'<clipPath id="{mid}"><rect class="{wid}" x="{num(x)}" y="{num(y + bar)}" width="{num(w)}" height="{num(ih_u)}"/></clipPath>')
        d.add(f'<image clip-path="url(#{mid})" x="{num(x)}" y="{num(y + bar)}" width="{num(w)}" height="{num(ih_u)}" href="{uri}"/>')
    else:
        d.add(f'<image x="{num(x)}" y="{num(y + bar)}" width="{num(w)}" height="{num(ih_u)}" href="{uri}"/>')
    if t.get("dim"):
        d.add(f'<rect x="{num(x)}" y="{num(y + bar)}" width="{num(w)}" height="{num(ih_u)}" fill="#000" fill-opacity="{t["dim"]}"/>')
    d.add("</g>")
    d.add(f'<rect x="{num(x + 0.75)}" y="{num(y + 0.75)}" width="{num(w - 1.5)}" height="{num(h - 1.5)}" rx="11.25" '
          f'fill="none" stroke="{t["frame_line"]}" stroke-opacity="{t["frame_op"]}" stroke-width="1.5"/>')
    if appear_at is not None:
        d.add("</g>")
    return h


LOG = [("写代码", "断网沙箱 · 13 次模型调用"), ("跑测试", "验收测试一轮全绿"), ("CI 部署", "推送即构建"), ("上线", "点开链接就能访问")]


def prompt(d, t, x, y, size, t0=0.1):
    """我说的那一句话：橙色，一个字一个字打出来；开头的「挂进左边距，让「做」对齐正文线。"""
    text = C.POC["task"]
    hang = d.width("「", "head", size)
    cx = x - hang
    for i, ch in enumerate("「" + text + "」"):
        cx += d.text(cx, y, ch, "head", size, t["org_t"], cls=appear(d, t0 + i * 0.045, 0.25, 0))


def codeless(t, mobile=False):
    w = C.BY["codeless"]
    title = f"正在做：codeless —— {w['desc']} 实测：一句「做一个咖啡店单页官网」，13 次模型调用、一轮通过、全部成本 $0.0127。"
    note = "数字出自 codeless 仓库 docs/06-poc-findings.md 的实测"

    def log(x, y, size, col2, lh):
        for i, (k_, v) in enumerate(LOG):
            cls = appear(d, 0.8 + i * 0.16, 0.4)
            d.add(f'<g class="{cls}">')
            d.text(x, y, "›", "mono", size, t["ink3"])
            d.text(x + size * 1.2, y, k_, "mono", size, t["ink3"])
            d.text(x + col2, y, v, "mono", size, t["ink3"])
            d.add("</g>")
            y += lh
        return y - lh

    if not mobile:
        W = DW
        d = doc(W, 1200, title)
        y0 = section_head(d, t, "02", "正在做", "now")
        py = y0 + 30
        at = len(d.body)
        y = py + 100
        label(d, G, y, "AI 编码流水线 · 自托管 · Docker + CI", t["ink3"], 23)
        y += 112
        d.text(G - 4, y, "codeless", "disp", 104, t["ink"])
        y += 70
        y = lines(d, G, y, w["desc"], "sans", 30, t["ink2"], 700, 50)
        y += 56
        rule(d, G, y, 800, t)
        y += 66
        label(d, G, y, "我说的一句话", t["ink3"], 23)
        y += 76
        prompt(d, t, G, y, 48)
        y += 76
        left_end = log(G, y, 24, 180, 44)
        bx = 900
        bw = W - G - bx
        by = py + 72
        bh = browser(d, t, bx, by, bw, "codeless", "它做出来的咖啡店官网 · 真截图", reveal=1.45, appear_at=1.25)
        cy = max(by + bh + 128, left_end - 62)
        cls = appear(d, 2.1, 0.5)
        d.add(f'<g class="{cls}">')
        nw = d.text(bx - 4, cy, "$0.0127", "disp", 112, t["ink"])
        d.text(bx + nw + 22, cy - 46, "这一次的全部成本", "sans", 28, t["ink2"])
        d.text(bx + nw + 22, cy - 8, "DEEPSEEK · 13 CALLS · 1 ROUND", "mono", 20, t["ink3"], track=0.06)
        d.text(bx, cy + 62, note, "sans", 23, t["ink3"])
        d.add("</g>")
        end = max(left_end, cy + 62) + 84
        d.body.insert(at, f'<rect x="0" y="{num(py)}" width="{W}" height="{num(end - py)}" rx="16" fill="{t["plate"]}"/>')
        d.h = end + PB + 12
        return d
    W = MW
    d = doc(W, 2400, title)
    y0 = section_head(d, t, "02", "正在做", "now", mobile=True)
    py = y0 + 48
    at = len(d.body)
    y = py + 70
    label(d, GM, y, "AI 编码流水线 · 自托管", t["ink3"], 23, track=0.06)
    y += 104
    d.text(GM - 4, y, "codeless", "disp", 96, t["ink"])
    y += 60
    y = lines(d, GM, y, w["desc"], "sans", 28, t["ink2"], W - 2 * GM, 46)
    y += 40
    bh = browser(d, t, GM, y, W - 2 * GM, "codeless", "它做出来的咖啡店官网", reveal=1.45, appear_at=1.25)
    y += bh + 70
    label(d, GM, y, "我说的一句话", t["ink3"], 23, track=0.06)
    y += 64
    prompt(d, t, GM, y, 40)
    y += 62
    y = log(GM, y, 24, 160, 42)
    y += 124
    cls = appear(d, 2.1, 0.5)
    d.add(f'<g class="{cls}">')
    nw = d.text(GM - 3, y, "$0.0127", "disp", 92, t["ink"])
    d.text(GM + nw + 16, y - 34, "这一次的全部成本", "sans", 24, t["ink2"])
    d.text(GM + nw + 16, y - 4, "13 CALLS · 1 ROUND", "mono", 20, t["ink3"], track=0.04)
    d.add("</g>")
    end = y + 56
    d.body.insert(at, f'<rect x="0" y="{num(py)}" width="{W}" height="{num(end - py)}" rx="14" fill="{t["plate"]}"/>')
    d.h = end + PBM
    return d


# ═══════════════════════════════════════════════════════════════════
#  03 作品：六件，左右交替的大图（真截图）
# ═══════════════════════════════════════════════════════════════════

ORDER = ["codeless", "ftms", "ems", "logicc", "codehelper", "chinesechess", "wxformat3", "macpleco", "ip-geo",
         "jobornot", "wx-export", "tabinfocopy", "pagescroll", "bing-wallpaper", "ip-display"]
NO = {s: i + 1 for i, s in enumerate(ORDER)}
FEATURED = ["ftms", "ems", "logicc", "wxformat3", "macpleco", "ip-geo"]
assert sorted(ORDER) == sorted(C.BY), "ORDER 跟作品数据对不上"


def link_label(w):
    if w.get("href"):
        return "打开", w["href"].replace("https://", "").rstrip("/")
    if w.get("dl"):
        return "下载", "GitHub Releases"
    return "源码", f"github.com/decli/{w['repo']}"


def link_lines(where, d, stack, size, width):
    """链接地址太长就在「decli/」后面折一次。"""
    if d.width(where, stack, size) <= width or "decli/" not in where:
        return [where]
    a, b = where.split("decli/", 1)
    return [a + "decli/", b]


def cover(d, t, x, y, w, h, slug, clip=None, fade_to=None, mobile=False):
    """截图放进 w×h 的框。
    普通截图：预设里已经裁成跟框同比例的一块（content.SHOT），这里只缩放；手机版可以用更小的一块（mcrop）。
    exhibit：几块真截图像展品一样摆在一块底色上，各带一行小标签（插件这种小窗口用）。
    clip=(x, y, w, h, rx) 用来跟卡片圆角一起裁；fade_to=颜色：底边 60 单位渐隐到这个颜色。"""
    sp = shot_ref(slug)
    rel, red = sp["rel"], sp.get("redact", ())
    small = mobile and sp.get("mcrop")
    crop = sp["mcrop"] if small else sp.get("crop")
    stack = sp.get("mstack") if small else sp.get("stack")
    tone = t.get("tone")
    cid = d.uid("cv")
    cx_, cy_, cw_, ch_, crx = clip or (x, y, w, h, 0)
    d.deff(f'<clipPath id="{cid}"><rect x="{num(cx_)}" y="{num(cy_)}" width="{num(cw_)}" height="{num(ch_)}" rx="{crx}"/></clipPath>')
    if sp.get("exhibit"):
        fid = d.uid("ps")
        d.deff(f'<filter id="{fid}" x="-20%" y="-20%" width="140%" height="180%"><feGaussianBlur stdDeviation="16"/></filter>')
        d.add(f'<g clip-path="url(#{cid})"><rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="{t["plate2"]}"/>')
        # 跟浏览器里真实的样子一样：工具栏在上，弹窗从徽标底下掉下来 —— 两块右边对齐
        spots = [(0.19, 0.17, 0.62), (0.19, 0.43, 0.62)] if not mobile else [(0.10, 0.12, 0.80), (0.10, 0.40, 0.80)]
        size = 22 if not mobile else 20
        for part, (fx, fy, fw) in zip(sp["exhibit"], spots):
            pw = w * fw
            uri, iw, ih = kit.shot_uri(rel, int(pw * 1.5), crop=part.get("crop"), stack=part.get("stack"), tone=tone)
            ph = pw * ih / iw
            px, py = x + w * fx, y + h * fy
            d.add(f'<rect x="{num(px + 8)}" y="{num(py + 18)}" width="{num(pw - 16)}" height="{num(ph)}" rx="8" fill="#000" '
                  f'fill-opacity="{0.10 if t["shade"] < 0.3 else 0.45}" filter="url(#{fid})"/>'
                  f'<image x="{num(px)}" y="{num(py)}" width="{num(pw)}" height="{num(ph)}" href="{uri}"/>'
                  f'<rect x="{num(px + .75)}" y="{num(py + .75)}" width="{num(pw - 1.5)}" height="{num(ph - 1.5)}" fill="none" '
                  f'stroke="{t["frame_line"]}" stroke-opacity="{t["frame_op"] * 1.4:.2f}" stroke-width="1.5"/>')
            d.text(px, py - 14, part["label"], "sans", size, t["ink3"])
        d.add("</g>")
        return
    uri, _, _ = kit.shot_uri(rel, int(w), crop=crop, redact=red, tone=tone, stack=stack, aspect=w / h)
    fade = ""
    if fade_to:
        fg = d.uid("ff")
        d.deff(f'<linearGradient id="{fg}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{fade_to}" stop-opacity="0"/>'
               f'<stop offset="1" stop-color="{fade_to}"/></linearGradient>')
        fade = f'<rect x="{num(x)}" y="{num(y + h - 60)}" width="{num(w)}" height="60" fill="url(#{fg})"/>'
    d.add(f'<g clip-path="url(#{cid})"><image x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" href="{uri}" '
          f'preserveAspectRatio="xMidYMid slice"/>'
          + (f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="#000" fill-opacity="{t["dim"]}"/>' if t.get("dim") else "")
          + fade + "</g>")


def plate(w, t, i, mobile=False, last=False):
    """一件作品一张：桌面左右交替（图在左 / 图在右），手机上图在上、字在下。
    截图去色 —— 那是 AI 的产出，按本页的规矩是灰的；每张卡上唯一的橙色，是我给这件作品下的那一句定义：它替谁解决什么。"""
    title = C.alt_work(w)
    kind, where = link_label(w)
    meta = f"{w['cat_zh']} · {w['for_']}"
    gap = 28 if not last else 28 + 44
    if not mobile:
        W, H = DW, 640
        d = doc(W, H + gap, title)
        d.add(f'<rect width="{W}" height="{H}" rx="16" fill="{t["plate"]}"/>')
        sw = 1024
        left = i % 2 == 0
        sx = 0 if left else W - sw
        cover(d, t, sx, 0, sw, H, w["slug"], clip=(0, 0, W, H, 16))
        d.add(f'<path d="M{num(sx + (sw if left else 0))} 0V{H}" stroke="{t["frame_line"]}" stroke-opacity="{t["frame_op"]}" stroke-width="1.5"/>')
        X = sw + 80 if left else G
        tw = W - sw - 80 - G
        names = d.wrap(w["name"], "head", 56, tw)
        quote = d.wrap(w["brief"], "quote", 32, tw, halt=True)      # 32：六句都正好两行
        wl = link_lines(where, d, "sans", 26, tw)
        block = 36 + 34 + len(names) * 70 + 22 + len(quote) * 48 + 64 + 30 + len(wl) * 36
        y = (H - block) / 2 + 30
        label(d, X, y, meta, t["ink3"], 25)
        y += 34 + 66
        for ln in names:
            d.text(X - 2, y, ln, "head", 56, t["ink"])
            y += 70
        y += 8
        for ln in quote:
            d.text(X, y, ln, "quote", 32, t["org_t"], halt=True)
            y += 48
        y += 50
        kw_ = d.text(X, y, kind, "sans-m", 30, t["ink"])
        arrow_ne(d, X + kw_ + 12, y - 3, 15, t["ink"], 2.4, down=kind == "下载")
        for k, ln in enumerate(wl):
            d.text(X, y + 44 + k * 36, ln, "sans", 26, t["ink3"])
        return d
    W = MW
    sh = 405
    tmp = doc(W, 10, "")
    quote = tmp.wrap(w["brief"], "quote", 31, W - 2 * GM, halt=True)
    wl = link_lines(where, tmp, "sans", 24, W - 2 * GM - 120)
    H = sh + 66 + 64 + len(quote) * 46 + 40 + 40 + len(wl) * 34 + 34
    d = doc(W, H + gap, title)
    d.add(f'<rect width="{W}" height="{num(H)}" rx="14" fill="{t["plate"]}"/>')
    cover(d, t, 0, 0, W, sh, w["slug"], clip=(0, 0, W, H, 14), mobile=True)
    rule(d, 0, sh, W, t, t["frame_op"])
    y = sh + 64
    label(d, GM, y, meta, t["ink3"], 24, track=0.04)
    y += 64
    d.text(GM - 2, y, w["name"], "head", 44, t["ink"])
    y += 56
    for ln in quote:
        d.text(GM, y, ln, "quote", 31, t["org_t"], halt=True)
        y += 46
    y += 40
    kw_ = d.text(GM, y, kind, "sans-m", 28, t["ink"])
    arrow_ne(d, GM + kw_ + 10, y - 3, 13, t["ink"], 2.2, down=kind == "下载")
    for k, ln in enumerate(wl):
        d.text(GM + kw_ + 42, y + k * 34, ln, "sans", 24, t["ink3"])
    return d


# ═══════════════════════════════════════════════════════════════════
#  04 全部作品：一行一件，每行都是一个链接，一个字都不截断
# ═══════════════════════════════════════════════════════════════════

def index_row(w, t, mobile=False, last=False):
    kind, where = link_label(w)
    title = C.alt_work(w)
    pad = PB if last else 0
    if not mobile:
        W = DW
        bx, bw = 476, 1380 - 476
        bl = kit.wrap(w["brief"], STACKS["sans"], 28, bw)
        H = 100 + (len(bl) - 1) * 44
        d = doc(W, H + pad, title)
        rule(d, 0, 1, W, t)
        if last:
            rule(d, 0, H + 1, W, t)
        y = 62
        label(d, 0, y, f"{NO[w['slug']]:02d}", t["ink3"], 25)
        d.text(G, y, w["name"], "head", 34, t["ink"])
        for k, ln in enumerate(bl):
            d.text(bx, y + k * 44, ln, "sans", 28, t["ink2"])
        d.text(1410, y, w["cat_zh"], "sans", 26, t["ink3"])
        d.text(W - 32, y, kind, "sans", 27, t["ink2"], anchor="end")
        arrow_ne(d, W - 16, y - 3, 13, t["ink2"], 2.2, down=kind == "下载")
        return d
    W = MW
    bl = kit.wrap(w["brief"], STACKS["sans"], 27, W - 56)
    H = 96 + (len(bl) - 1) * 42 + 34
    d = doc(W, H + pad, title)
    rule(d, 0, 1, W, t)
    if last:
        rule(d, 0, H + 1, W, t)
    y = 56
    label(d, 0, y, f"{NO[w['slug']]:02d}", t["ink3"], 22)
    d.text(56, y, w["name"], "head", 33, t["ink"])
    d.text(W - 30, y, kind, "sans", 25, t["ink2"], anchor="end")
    arrow_ne(d, W - 15, y - 3, 12, t["ink2"], 2, down=kind == "下载")
    for k, ln in enumerate(bl):
        d.text(56, y + 46 + k * 42, ln, "sans", 27, t["ink2"])
    return d


# ═══════════════════════════════════════════════════════════════════
#  05 我相信的几件事
# ═══════════════════════════════════════════════════════════════════

def beliefs(t, mobile=False):
    # 第一条「人出判断，AI 执行」整页都在讲，这里只留另外两条
    items = C.PRINCIPLES[1:]
    title = "我相信的两件事：" + "".join(h + b for h, b in items)
    nums = ["i.", "ii.", "iii."]
    if not mobile:
        W = DW
        d = doc(W, 900, title)
        y0 = section_head(d, t, "05", "我相信的两件事", "beliefs")
        gap = 96
        colw = (W - G - G - gap) / 2
        end = 0
        for i, (head, body) in enumerate(items):
            x = G + i * (colw + gap)
            y = y0 + 84
            d.text(x, y, nums[i], "disp-it", 56, t["ink3"])
            y += 88
            d.text(x, y, head, "head", 46, t["ink"])
            y += 64
            y = lines(d, x, y, body, "sans", 30, t["ink2"], colw, 50, justify=False)   # 短的主张按词断，右边参差
            end = max(end, y)
        d.h = end + PB + 10
        return d
    W = MW
    d = doc(W, 2000, title)
    y = section_head(d, t, "05", "我相信的两件事", "beliefs", mobile=True) + 34
    for i, (head, body) in enumerate(items):
        y += 44
        d.text(0, y, nums[i], "disp-it", 46, t["ink3"])
        d.text(62, y, head, "head", 38, t["ink"])
        y += 54
        y = lines(d, 62, y, body, "sans", 28, t["ink2"], W - 62, 46, justify=False)
        y += 40
    d.h = y - 40 + PBM + 10
    return d


# ═══════════════════════════════════════════════════════════════════
#  版权页
# ═══════════════════════════════════════════════════════════════════

def colophon(t, mobile=False):
    title = ("版权页：灰色的代码，是 AI 的产出；橙色，是我的判断。这一页也一样 —— 版式、配色、动效和生成它的代码都是 AI 写的，"
             f"我只选了方向、验了收。作品集：decli.github.io；联系方式：{C.EMAIL}")
    rule_txt = [("灰色的代码，", "head", t["ink3"]), ("是 AI 的产出；", "head", t["ink"]), ("橙色，", "head", t["org"]),
                ("是我的判断。", "head", t["ink"])]
    where = "页面上的橙色只标我做的判断：那个 0 和 0 里的光标、三个判断点、我对 codeless 说的那句话、每件精选作品替谁解决什么。"
    note = "截图也是 AI 的产出，所以一律去了色。这一页本身也一样：版式、配色、动效和生成它的代码，都是 AI 写的；我只选了方向、验了收。"
    fonts = "字体：Instrument Serif、Geist、思源宋体、思源黑体（SIL OFL 1.1，按页切字嵌入）"
    if not mobile:
        W, H = DW, 640
        d = doc(W, H, title)
        d.add(f'<rect width="{W}" height="{H}" rx="16" fill="{t["plate"]}"/>')
        cid = d.uid("cc")
        d.deff(f'<clipPath id="{cid}"><rect width="{W}" height="{H}" rx="16"/></clipPath>')
        d.add(f'<g clip-path="url(#{cid})">')
        zero_figure(d, t, W - 150, 70, 860, 1.2, 2, (16, 50), t0=0.2)
        d.add("</g>")
        label(d, G, 116, "版权页 · colophon", t["ink3"], 23)
        d.spans(G - 2, 214, [(s_, st, c, 0) for s_, st, c in rule_txt], 56)
        y = lines(d, G, 292, where, "sans", 29, t["ink2"], 1150, 48, justify=False)
        y = lines(d, G, y + 48, note, "sans", 29, t["ink2"], 1150, 48, justify=False)
        d.text(G, y + 66, fonts, "sans", 24, t["ink3"])
        rule(d, G, H - 118, 1300, t)
        wn = d.text(G, H - 56, "decli", "disp-it", 54, t["ink"])
        label(d, G + wn + 22, H - 60, f"© 2026 · {C.ROLE}", t["ink3"], 21)
        sw = label(d, 1300 - 34, H - 60, "作品集 decli.github.io", t["ink"], 23, anchor="end")
        arrow_ne(d, 1300 - 17, H - 61, 15, t["ink"], 2.2)
        # 联系方式跟作品集链接并排，同一种标签字；图片里的字点不了，所以 README 的替代文字里也写了一遍
        d.spans(1300 - 34 - sw - 56, H - 60, [("联系方式：", "sans-m", t["ink3"], 0.02),
                                              (C.EMAIL.upper(), "sans-m", t["ink"], 0.12)], 23, anchor="end")
        return d
    W = MW
    d = doc(W, 2000, title)
    X = GM
    label(d, X, 82, "版权页 · colophon", t["ink3"], 20)
    y = 176
    d.text(X - 2, y, "灰色的代码，", "head", 44, t["ink3"])
    d.spans(X - 2, y + 62, [(s_, st, c, 0) for s_, st, c in rule_txt[1:2]], 44)
    d.spans(X - 2, y + 124, [(s_, st, c, 0) for s_, st, c in rule_txt[2:]], 44)
    y += 196
    y = lines(d, X, y, where, "sans", 27, t["ink2"], W - 2 * X, 44)
    y = lines(d, X, y + 44, note, "sans", 27, t["ink2"], W - 2 * X, 44)
    y = lines(d, X, y + 56, fonts, "sans", 24, t["ink3"], W - 2 * X, 38, justify=False)
    y += 50
    rule(d, X, y, W - X, t)
    y += 74
    d.text(X, y, "decli", "disp-it", 50, t["ink"])
    label(d, W - X - 32, y - 6, "decli.github.io", t["ink"], 21, anchor="end")
    arrow_ne(d, W - X - 16, y - 7, 13, t["ink"], 2)
    y += 48
    label(d, X, y, f"© 2026 · {C.ROLE}", t["ink3"], 21)
    y += 40
    d.spans(X, y, [("联系方式：", "sans-m", t["ink3"], 0.02), (C.EMAIL.upper(), "sans-m", t["ink"], 0.12)], 21)
    H = y + 46
    d.h = H
    cid = d.uid("cc")
    d.deff(f'<clipPath id="{cid}"><rect width="{W}" height="{num(H)}" rx="14"/></clipPath>')
    body = d.body
    d.body = []
    d.add(f'<rect width="{W}" height="{num(H)}" rx="14" fill="{t["plate"]}"/><g clip-path="url(#{cid})">')
    zero_figure(d, t, W - 116, 34, 300, 1.2, 1.6, (8, 24), t0=0.2)
    d.add("</g>")
    d.body += body
    return d


# ═══════════════════════════════════════════════════════════════════
#  生成
# ═══════════════════════════════════════════════════════════════════

def build(out: pathlib.Path, prefix="assets/"):
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for f in assets.glob("*.svg"):
        f.unlink()
    sizes = {}

    def emit(name, fn):
        for mode, t in T.items():
            for dev in ("d", "m"):
                svg = fn(t, mobile=dev == "m").render()
                sizes[f"{name}-{dev}-{mode}"] = kit.write(assets, f"{name}-{dev}-{mode}", svg)

    emit("hero", hero)
    emit("about", about)
    emit("method", method)
    emit("codeless", codeless)
    emit("works", lambda t, mobile: head_only(t, "03", "作品", f"selected · {len(FEATURED)} / {C.N}", mobile=mobile))
    for i, s in enumerate(FEATURED):
        emit(f"work-{s}", lambda t, mobile, s=s, i=i: plate(C.BY[s], t, i, mobile=mobile, last=i == len(FEATURED) - 1))
    emit("index", lambda t, mobile: head_only(t, "04", "全部作品", f"index · {C.N}", mobile=mobile))
    for k, s in enumerate(ORDER):
        emit(f"row-{s}", lambda t, mobile, s=s, k=k: index_row(C.BY[s], t, mobile=mobile, last=k == len(ORDER) - 1))
    emit("beliefs", beliefs)
    emit("colophon", colophon)
    kit.save_seg()

    P = lambda *a, **k: kit.picture(*a, prefix=prefix, **k)  # noqa: E731
    md = ["<!-- 由 studio/zero.py 生成，别手改。改文案改 build.py 的数据，再跑 python3 studio/build.py --home zero -->", ""]
    md.append(P("hero", f"decli — {C.HEAD_A}{C.HEAD_B}" + "".join(C.LEDE), "100%", C.SITE))
    md += ["", P("about", "履历：" + C.BIO, "100%")]
    md += ["", P("method", "方法：人出判断，AI 执行。我只做三件事：定方向、设规则、验结果；"
                           f"其余的 —— {'、'.join(C.AI_DOES)} —— 流程一步不少，全部由 AI 执行。", "100%")]
    cl = C.BY["codeless"]
    md += ["", P("codeless", f"正在做：codeless —— {cl['desc']}", "100%", cl["link"])]
    md += ["", P("works", "03 作品", "100%")]
    md += ["", "<p>" + "".join(P(f"work-{s}", C.alt_work(C.BY[s]), "100%", C.BY[s]["link"]) for s in FEATURED) + "</p>"]
    md += ["", P("index", f"04 全部 {C.N} 个作品", "100%")]
    md += ["", "<p>" + "".join(P(f"row-{s}", C.alt_work(C.BY[s]), "100%", C.BY[s]["link"]) for s in ORDER) + "</p>"]
    md += ["", P("beliefs", "我相信的两件事：" + " ".join(h + b for h, b in C.PRINCIPLES[1:]), "100%")]
    md += ["", P("colophon", f"版权页：灰色的代码是 AI 的产出，橙色是我的判断。作品集 decli.github.io；联系方式：{C.EMAIL}", "100%", C.SITE), ""]
    (out / "README.md").write_text("\n".join(md))
    tot = {}
    for k, v in sizes.items():
        key = "-".join(k.split("-")[-2:])
        tot[key] = tot.get(key, 0) + v
    big = sorted(sizes.items(), key=lambda kv: -kv[1])[:5]
    print("  一页加载：" + "  ".join(f"{k} {v / 1024:.0f} KB" for k, v in tot.items()))
    print("  最大的几张：" + "  ".join(f"{k} {v / 1024:.0f} KB" for k, v in big))


if __name__ == "__main__":
    build(kit.ROOT if "--home" in sys.argv else kit.ROOT / "styles" / "zero")
