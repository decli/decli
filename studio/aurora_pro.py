"""
studio/aurora_pro.py —— 方向 B「极光 Pro」。

跟作品集 decli.github.io 同一套品牌：深海军蓝、紫 → 青的极光、玻璃卡片、渐变标题。
在旧「极光」的基础上把工艺拉满：
  - 首屏和页脚是两块「夜空」—— 亮色主题下也是夜空（极光本来就是夜里的东西），
    白页面上一头一尾两块深色，中间的内容卡片跟着主题走；
  - 极光是一道一道的光帘：底边是一条会发光的 S 形曲线，光束从底边往上长、聚在褶子里，整片缓慢摆动；
  - 字体嵌进图里（Geist + 思源黑体），各平台长得一样，字宽量得准，中文按词折行；
  - 卡片：有渐变的玻璃底、顶边一道高光、亮色主题下烘进去的柔和投影；光晕一律裁在卡片里面；
  - 网格：卡片内边一律 64（32px），标题贴页面边；手机单独排版、单栏；
  - 作品卡用作品集里的真截图。
"""

from __future__ import annotations

import math
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import content as C  # noqa: E402
import kit  # noqa: E402
import zero as Z  # noqa: E402  复用：截图、浏览器框、标签、折行、出场动画
from kit import Doc, Stack, num  # noqa: E402

DW, MW = Z.DW, Z.MW
P, PM = 64, 32        # 卡片内边：桌面 / 手机
PB, PBM = 60, 60      # 段落底部留白：段与段之间一律 116 单位（58px），跟方向 A 一样

STACKS = {
    "sans": Stack(["geist", "sans-sc"], kit.SYS_SANS),
    "sans-m": Stack(["geist-m", "sans-sc-m"], kit.SYS_SANS),
    "sans-b": Stack(["geist-b", "sans-sc-b"], kit.SYS_SANS),
    "black": Stack(["geist-b", "sans-sc-k"], kit.SYS_SANS),
    "mono": Stack(["mono", "sans-sc"], kit.SYS_MONO),
    "mono-m": Stack(["mono-m", "sans-sc-m"], kit.SYS_MONO),
}

AUR = ("#7c5cff", "#06b6d4", "#3b5bd6")
SOLID = ("#3b5bd6", "#7c5cff", "#06b6d4")   # 压白字的实心色块：两套主题都用这组饱和色
NIGHT = dict(sky0="#050816", sky1="#0b1233", text="#f3f6ff", text2="#b9c3dc", text3="#aab4cc",
             line="#c7d4ff", line_op=0.16, glass="#141c3c", glass_op=0.66)
T = {
    "light": dict(
        card0="#ffffff", card1="#f6f7fe", card_line="#dce0f0", hi="#ffffff", shadow=0.08,
        text="#0f1729", text2="#4a5468", text3="#5b6478", brand="#3b5bd6", brand2="#5b3fd6", brand3="#0891b2",
        live="#0b7a45", tile="#eef0ff", chip="#eef1fa", line="#122044", line_op=0.10, glow=0.14,
        # 给 zero.py 里复用的函数（浏览器框、截图）用的几个名字
        frame="#ffffff", frame_line="#122044", frame_op=0.10, ink3="#5b6478", dim=0.0, plate2="#eef1fa", shade=0.1,
    ),
    "dark": dict(
        card0="#151d3b", card1="#0e1430", card_line="#ffffff", hi="#ffffff", shadow=0.0,
        text="#eaf0ff", text2="#a9b4d0", text3="#8b96b2", brand="#8da2ff", brand2="#a78bfa", brand3="#22d3ee",
        live="#34d399", tile="#1a1f3d", chip="#1b2447", line="#96b2f0", line_op=0.14, glow=0.22,
        frame="#10173a", frame_line="#c7d4ff", frame_op=0.16, ink3="#8b96b2", dim=0.06, plate2="#0b1130", shade=0.5,
    ),
}

EASE = Z.EASE
BASE_CSS = Z.BASE_CSS + ".pulse{animation:pulse 2.4s ease-in-out infinite}@keyframes pulse{50%{opacity:.25}}"


def doc(w, h, title):
    d = Doc(w, h, title, STACKS)
    d.style(BASE_CSS)
    return d


delay, lines, label, appear, arrow = Z.delay, Z.lines, Z.label, Z.appear, Z.arrow_ne


def grad(d, x1, x2, stops, y=0):
    gid = d.uid("g")
    d.deff(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{num(x1)}" y1="{num(y)}" x2="{num(x2)}" y2="{num(y)}">'
           + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops) + "</linearGradient>")
    return f"url(#{gid})"


def brand_grad(d, t, x1, x2):
    return grad(d, x1, x2, [(0, t["brand"]), (0.55, t["brand2"]), (1, t["brand3"])])


def solid_grad(d, x1, x2, a=0, b=1):
    return grad(d, x1, x2, [(0, SOLID[a]), (1, SOLID[b])])


def hairline(d, color, op, x1, y, x2):
    d.add(f'<path d="M{num(x1)} {num(y)}H{num(x2)}" stroke="{color}" stroke-opacity="{num(op)}" stroke-width="1.5"/>')


def radial(d, c, op):
    gid = d.uid("r")
    d.deff(f'<radialGradient id="{gid}"><stop offset="0" stop-color="{c}" stop-opacity="{op}"/>'
           f'<stop offset=".55" stop-color="{c}" stop-opacity="{op * 0.35:.3f}"/>'
           f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>')
    return f"url(#{gid})"


def card(d, t, x, y, w, h, rx=24, glows=()):
    """玻璃卡：上亮下暗的渐变底、顶边一道 1px 高光、细描边；亮色主题烘一层柔和投影，卡里再铺两团很淡的品牌色，
    让「玻璃」有东西可透。glows = [(cx, cy, rx, ry, color, op)] —— 光晕一律裁在卡片里面。"""
    if t["shadow"]:
        fid = d.uid("sh")
        d.deff(f'<filter id="{fid}" x="-10%" y="-10%" width="120%" height="140%"><feGaussianBlur stdDeviation="12"/></filter>')
        d.add(f'<rect x="{num(x + 16)}" y="{num(y + 14)}" width="{num(w - 32)}" height="{num(h - 10)}" rx="{rx}" fill="#1e1b4b" '
              f'fill-opacity="{t["shadow"]}" filter="url(#{fid})"/>')
    gid = d.uid("cg")
    d.deff(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["card0"]}"/>'
           f'<stop offset="1" stop-color="{t["card1"]}"/></linearGradient>')
    cid = d.uid("cc")
    d.deff(f'<clipPath id="{cid}"><rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" rx="{rx}"/></clipPath>')
    inner = f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="url(#{gid})"/>'
    if t["shadow"]:
        glows = list(glows) + [(x + w * 0.08, y + h * 0.1, min(w, 900) * 0.5, h * 0.7, "#7c5cff", 0.10),
                               (x + w * 0.95, y + h * 0.95, min(w, 900) * 0.5, h * 0.7, "#22d3ee", 0.08)]
    for gx, gy, grx, gry, c, op in glows:
        inner += f'<ellipse cx="{num(gx)}" cy="{num(gy)}" rx="{num(grx)}" ry="{num(gry)}" fill="{radial(d, c, op)}"/>'
    d.add(f'<g clip-path="url(#{cid})">{inner}</g>')
    if t["shadow"]:
        d.add(f'<rect x="{num(x + .75)}" y="{num(y + .75)}" width="{num(w - 1.5)}" height="{num(h - 1.5)}" rx="{rx - .75}" '
              f'fill="none" stroke="{t["card_line"]}" stroke-width="1.5"/>')
    else:
        lg = d.uid("cl")
        d.deff(f'<linearGradient id="{lg}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".10"/>'
               f'<stop offset="1" stop-color="#fff" stop-opacity=".03"/></linearGradient>')
        d.add(f'<rect x="{num(x + .75)}" y="{num(y + .75)}" width="{num(w - 1.5)}" height="{num(h - 1.5)}" rx="{rx - .75}" '
              f'fill="none" stroke="url(#{lg})" stroke-width="1.5"/>')
    d.add(f'<path d="M{num(x + rx)} {num(y + 1.5)}H{num(x + w - rx)}" stroke="#fff" stroke-opacity="{0.9 if t["shadow"] else 0.09}" '
          f'stroke-width="1.5"/>')


# ═══════════════════════════════════════════════════════════════════
#  夜空：极光光帘 + 星点 + 颗粒
# ═══════════════════════════════════════════════════════════════════

def cubic_at(p0, p1, p2, p3, u):
    return ((1 - u) ** 3 * p0[0] + 3 * (1 - u) ** 2 * u * p1[0] + 3 * (1 - u) * u ** 2 * p2[0] + u ** 3 * p3[0],
            (1 - u) ** 3 * p0[1] + 3 * (1 - u) ** 2 * u * p1[1] + 3 * (1 - u) * u ** 2 * p2[1] + u ** 3 * p3[1])


class Hem:
    """极光的底边：一串三次贝塞尔。能按 x 查 y，也能吐出 SVG path。"""

    @classmethod
    def through(cls, pts, k=0.18):
        """过一串点的平滑曲线（Catmull-Rom 换算成贝塞尔），每个点处切线连续，不会出现折角。"""
        segs = []
        for i in range(len(pts) - 1):
            p0 = pts[i - 1] if i else pts[i]
            p1, p2 = pts[i], pts[i + 1]
            p3 = pts[i + 2] if i + 2 < len(pts) else p2
            c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
            c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
            segs.append((c1, c2, p2))
        return cls(pts[0], segs)

    def __init__(self, start, segs):
        self.start, self.segs = start, segs          # segs = [(c1, c2, end), ...]
        pts, p = [start], start
        for c1, c2, e in segs:
            pts += [cubic_at(p, c1, c2, e, k / 40) for k in range(1, 41)]
            p = e
        self.pts = pts

    def y(self, x):
        for a, b in zip(self.pts, self.pts[1:]):
            if a[0] <= x <= b[0] and b[0] > a[0]:
                return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
        return self.pts[-1][1] if x > self.pts[-1][0] else self.pts[0][1]

    def d(self):
        out = f"M{num(self.start[0])} {num(self.start[1])}"
        for c1, c2, e in self.segs:
            out += f"C{num(c1[0])} {num(c1[1])} {num(c2[0])} {num(c2[1])} {num(e[0])} {num(e[1])}"
        return out


def curtain(d, hem: Hem, x0, x1, top, seed, n_sheets=13, n_hair=40, sway=26, dur=18, t_in=0.9, rays=True):
    """光帘：一条发光的底边；底边上方是一片片宽窄不一的「光幕」（径向渐变：底边中间最亮，往上、往两边淡出），
    再撒四十来根很淡的细光丝做纹理。光幕全部裁在底边以上 —— 极光不会从地平线下面冒出来。"""
    rnd = random.Random(seed)
    cols = [("#5eead4", "#7c5cff"), ("#22d3ee", "#a78bfa"), ("#818cf8", "#f0abfc")]
    grads = []
    for lo, hi in cols:
        gid = d.uid("sg")
        d.deff(f'<radialGradient id="{gid}" cx=".5" cy="1" r="1" gradientTransform="matrix(.5 0 0 1 .25 0)">'
               f'<stop offset="0" stop-color="{lo}" stop-opacity=".9"/><stop offset=".22" stop-color="{lo}" stop-opacity=".5"/>'
               f'<stop offset=".6" stop-color="{hi}" stop-opacity=".16"/><stop offset="1" stop-color="{hi}" stop-opacity="0"/></radialGradient>')
        grads.append(gid)
    hg = d.uid("hg")
    d.deff(f'<linearGradient id="{hg}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#a5f3fc" stop-opacity=".8"/>'
           f'<stop offset=".5" stop-color="#a78bfa" stop-opacity=".25"/><stop offset="1" stop-color="#a78bfa" stop-opacity="0"/></linearGradient>')
    groups = [[], [], []]
    if rays:
        for i in range(n_sheets):
            u = (i + rnd.uniform(0.2, 0.8)) / n_sheets
            cx = x0 + (x1 - x0) * u
            yb = hem.y(cx)
            w = rnd.uniform(60, 170)
            h = (yb - top) * rnd.uniform(0.55, 1.0)
            k = min(len(grads) - 1, int(u * len(grads)))
            groups[i % 3].append(f'<rect x="{num(cx - w / 2)}" y="{num(yb - h)}" width="{num(w)}" height="{num(h + 16)}" '
                                 f'fill="url(#{grads[k]})" opacity="{rnd.uniform(0.55, 0.95):.2f}"/>')
        for i in range(n_hair):
            cx = x0 + (x1 - x0) * rnd.random()
            yb = hem.y(cx)
            h = (yb - top) * rnd.uniform(0.3, 0.85)
            groups[i % 3].append(f'<rect x="{num(cx)}" y="{num(yb - h)}" width="{rnd.choice((1, 1.5, 2))}" height="{num(h)}" '
                                 f'fill="url(#{hg})" opacity="{rnd.uniform(0.12, 0.3):.2f}"/>')
    # 裁在底边以上
    clip = d.uid("hc")
    d.deff(f'<clipPath id="{clip}"><path d="{hem.d()}L{num(d.w + 80)} {num(hem.pts[-1][1])}L{num(d.w + 80)} -10L{num(hem.start[0])} -10Z"/></clipPath>')
    x_a, x_b = hem.start[0], hem.pts[-1][0]
    rise = (x0 - x_a) / max(1, x_b - x_a)
    eg = grad(d, x_a, x_b, [(0, "#c7d4ff"), (max(0.01, rise * 0.9), "#9fb7ff"), (min(0.99, rise + 0.12), "#5eead4"),
                            (0.8, "#5eead4"), (1, "#a78bfa")])
    gg = d.uid("gg")
    d.deff(f'<linearGradient id="{gg}" gradientUnits="userSpaceOnUse" x1="{num(x_a)}" x2="{num(x_b)}" y1="0" y2="0">'
           f'<stop offset="0" stop-color="#5eead4" stop-opacity="0"/><stop offset="{max(0.01, rise * 0.85):.2f}" stop-color="#5eead4" stop-opacity="0"/>'
           f'<stop offset="{min(0.99, rise + 0.15):.2f}" stop-color="#5eead4"/><stop offset=".8" stop-color="#67e8f9"/>'
           f'<stop offset="1" stop-color="#a78bfa"/></linearGradient>')
    sid = d.uid("sw")
    d.style(f"@keyframes {sid}{{0%,100%{{transform:translateX(0) skewX(0deg)}}50%{{transform:translateX({sway}px) skewX(-3deg)}}}}"
            f".{sid}{{animation:{sid} {dur}s ease-in-out infinite;transform-box:fill-box;transform-origin:50% 100%}}"
            f"@keyframes {sid}s{{0%,100%{{opacity:1}}50%{{opacity:.5}}}}"
            + "".join(f".{sid}s{j}{{animation:{sid}s {4.6 + j * 1.3:.1f}s ease-in-out {-j * 1.7:.1f}s infinite}}" for j in range(3))
            + f"@keyframes {sid}g{{from{{transform:scaleY(0);opacity:0}}to{{transform:none;opacity:1}}}}"
            f".{sid}g{{transform-box:fill-box;transform-origin:50% 100%;animation:{sid}g 1.8s cubic-bezier(.16,1,.3,1) {t_in:.2f}s both}}"
            ".edge{stroke-dasharray:3000;animation:edge 1.6s cubic-bezier(.65,0,.35,1) .15s both}"
            "@keyframes edge{from{stroke-dashoffset:3000}to{stroke-dashoffset:0}}")
    rays_svg = "".join(f'<g class="{sid}s{j}">{"".join(g)}</g>' for j, g in enumerate(groups))
    # 光晕：几层越来越宽、越来越淡的描边叠出来的「模糊」—— 比 blur 滤镜便宜，跟细线一起画出来
    hem_svg = "".join(f'<path class="edge" d="{hem.d()}" fill="none" stroke="url(#{gg})" stroke-width="{sw}" '
                      f'stroke-opacity="{op}" stroke-linecap="round"/>' for sw, op in ((22, .05), (12, .08), (6, .16)))
    hem_svg += f'<path class="edge" d="{hem.d()}" fill="none" stroke="{eg}" stroke-width="2" stroke-opacity=".9" stroke-linecap="round"/>'

    return (f'<g clip-path="url(#{clip})"><g class="{sid}"><g class="{sid}g">{rays_svg}</g></g></g>' if rays else "") + hem_svg


def stars(d, w, h, n, seed, top=0, avoid=()):
    """星点：分三组各自明暗 —— 三个动画，而不是每颗星一个。avoid = 文字框，星星不压字。"""
    rnd = random.Random(seed)
    d.style(".tw0{animation:tw 4s ease-in-out infinite}.tw1{animation:tw 5.3s ease-in-out -1.7s infinite}"
            ".tw2{animation:tw 6.1s ease-in-out -3.1s infinite}@keyframes tw{50%{opacity:.2}}")
    groups = [[], [], []]
    k = 0
    while k < n * 6 and sum(len(g) for g in groups) < n:
        k += 1
        x, y = rnd.uniform(0, w), rnd.uniform(top, h)
        if any(ax0 - 24 <= x <= ax1 + 24 and ay0 - 24 <= y <= ay1 + 24 for ax0, ay0, ax1, ay1 in avoid):
            continue
        r = rnd.choice((0.9, 1.1, 1.4, 1.8))
        groups[k % 3].append(f'<circle cx="{num(x)}" cy="{num(y)}" r="{r}" fill-opacity="{rnd.uniform(0.3, 0.9):.2f}"/>')
    return "".join(f'<g class="tw{j}" fill="#fff">{"".join(g)}</g>' for j, g in enumerate(groups))


_NOISE = None


def grain(d, op):
    """胶片颗粒：一块 160px 的噪点小图平铺（比 feTurbulence 便宜：那个每一帧都要重算整张图）。"""
    global _NOISE
    if _NOISE is None:
        import base64
        import io
        from PIL import Image
        rnd = random.Random(3)
        im = Image.new("LA", (160, 160))
        im.putdata([(rnd.choice((0, 255)), rnd.choice((0, 0, 90))) for _ in range(160 * 160)])
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        _NOISE = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    pid = d.uid("gp")
    d.deff(f'<pattern id="{pid}" width="160" height="160" patternUnits="userSpaceOnUse">'
           f'<image width="160" height="160" href="{_NOISE}"/></pattern>')
    return f'<rect width="100%" height="100%" fill="url(#{pid})" opacity="{op}"/>'


PAL = [("#5eead4", "#7c5cff"), ("#22d3ee", "#a78bfa"), ("#818cf8", "#f0abfc")]


def sky(d, W, H, rx=24, seed=7, hem=None, top=60, x0=900, x1=None, rays=True, star_n=64, avoid=(), blobs=True,
        blob_op=(.55, .40, .18), dawn=None):
    """夜空底板：渐变天幕 + 星点 + 三团慢慢漂的色斑 + 光帘 + 颗粒。"""
    cid = d.uid("cl")
    d.deff(f'<clipPath id="{cid}"><rect width="{W}" height="{num(H)}" rx="{rx}"/></clipPath>')
    sg = d.uid("sky")
    d.deff(f'<linearGradient id="{sg}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{NIGHT["sky0"]}"/>'
           f'<stop offset="1" stop-color="{NIGHT["sky1"]}"/></linearGradient>')
    parts = [f'<rect width="{W}" height="{num(H)}" fill="url(#{sg})"/>', stars(d, W, H * 0.8, star_n, seed, avoid=avoid)]
    if blobs:
        for i, (cx, cy, rx_, ry, c, op) in enumerate([(W * .80, H * .05, W * .48, H * .8, AUR[0], blob_op[0]),
                                                       (W * .10, H * .80, W * .45, H * .75, AUR[1], blob_op[1]),
                                                       (W * .96, H * 1.0, W * .42, H * .62, AUR[2], blob_op[2])]):
            parts.append(f'<g class="f{i + 1}"><ellipse cx="{num(cx)}" cy="{num(cy)}" rx="{num(rx_)}" ry="{num(ry)}" '
                         f'fill="{radial(d, c, op)}"/></g>')
        d.style("@keyframes f1{33%{transform:translate(60px,-40px)}66%{transform:translate(-70px,34px)}}"
                "@keyframes f2{33%{transform:translate(-50px,40px)}66%{transform:translate(64px,-26px)}}"
                "@keyframes f3{33%{transform:translate(44px,32px)}66%{transform:translate(-60px,-38px)}}"
                ".f1{animation:f1 40s ease-in-out infinite}.f2{animation:f2 52s ease-in-out -14s infinite}"
                ".f3{animation:f3 46s ease-in-out -26s infinite}")
    if dawn is not None:
        # 黎明：地平线上升起一层青到淡紫的光
        dg = d.uid("dw")
        d.deff(f'<linearGradient id="{dg}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#5eead4" stop-opacity=".26"/>'
               f'<stop offset=".45" stop-color="#a78bfa" stop-opacity=".10"/><stop offset="1" stop-color="#a78bfa" stop-opacity="0"/></linearGradient>')
        glow = (f'<rect x="0" y="{num(dawn - 180)}" width="{W}" height="214" fill="url(#{dg})"/>'
                f'<ellipse cx="{num(W * .55)}" cy="{num(dawn + 20)}" rx="{num(W * .6)}" ry="130" fill="{radial(d, "#5eead4", .18)}"/>')
        if hem is not None:       # 光只在地平线以上：裁在那条波浪线上面，不留一条平直的接缝
            hc = d.uid("hz")
            d.deff(f'<clipPath id="{hc}"><path d="{hem.d()}L{W + 60} -10L-60 -10Z"/></clipPath>')
            glow = f'<g clip-path="url(#{hc})">{glow}</g>'
        parts.append(glow)
    if hem is not None:
        parts.append(curtain(d, hem, x0, x1 if x1 is not None else W + 40, top, seed, rays=rays))
    parts.append(grain(d, 0.07))
    d.add(f'<g clip-path="url(#{cid})">{"".join(parts)}</g>')
    d.add(f'<rect x=".75" y=".75" width="{W - 1.5}" height="{num(H - 1.5)}" rx="{rx - .75}" fill="none" '
          f'stroke="{NIGHT["line"]}" stroke-opacity="{NIGHT["line_op"]}" stroke-width="1.5"/>')


def logo(d, x, y, s):
    """作品集同款的「d」：实心渐变圆角方块，白字。"""
    d.add(f'<rect x="{num(x)}" y="{num(y)}" width="{s}" height="{s}" rx="{num(s * 0.28)}" fill="{solid_grad(d, x, x + s)}"/>')
    d.text(x + s / 2, y + s * 0.7, "d", "black", s * 0.62, "#fff", anchor="middle")


def icon(d, t, w, x, y, size):
    """作品图标：有自己 favicon 的借它的，没有的用线条图形 + tint。"""
    rx = size * 0.28
    ic = w["icon"]
    if ic.startswith("@"):
        f = kit.ROOT / "src" / "icons" / ic[1:]
        uri = kit.png_uri(f)
        if f.suffix == ".svg":
            d.add(f'<image x="{num(x)}" y="{num(y)}" width="{size}" height="{size}" href="{uri}"/>')
            return
        cid = d.uid("ic")
        d.deff(f'<clipPath id="{cid}"><rect x="{num(x)}" y="{num(y)}" width="{size}" height="{size}" rx="{num(rx)}"/></clipPath>')
        d.add(f'<rect x="{num(x)}" y="{num(y)}" width="{size}" height="{size}" rx="{num(rx)}" fill="#fff"/>'
              f'<image x="{num(x)}" y="{num(y)}" width="{size}" height="{size}" href="{uri}" clip-path="url(#{cid})"/>'
              f'<rect x="{num(x + .75)}" y="{num(y + .75)}" width="{num(size - 1.5)}" height="{num(size - 1.5)}" rx="{num(rx)}" '
              f'fill="none" stroke="{t["line"]}" stroke-opacity="{t["line_op"]}" stroke-width="1.5"/>')
        return
    a, b = w["tint"]
    g = grad(d, x, x + size, [(0, a), (1, b)])
    k = size * 0.54 / 24
    off = size * 0.23
    d.add(f'<rect x="{num(x)}" y="{num(y)}" width="{size}" height="{size}" rx="{num(rx)}" fill="{g}"/>'
          f'<g transform="translate({num(x + off)} {num(y + off)}) scale({k:.3f})" fill="none" stroke="#fff" '
          f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{C.ICONS[ic]}</g>')


def line_icon(d, name, x, y, size, stroke, width=2):
    k = size / 24
    d.add(f'<g transform="translate({num(x)} {num(y)}) scale({k:.3f})" fill="none" stroke="{stroke}" '
          f'stroke-width="{width / k:.2f}" stroke-linecap="round" stroke-linejoin="round">{C.ICONS[name]}</g>')


def button(d, t, x, y, label_, solid=True, h=56, size=24):
    """主按钮：实心渐变（打开 / 下载）；次按钮：描边（源码）。返回宽度。"""
    tw = d.width(label_, "sans-b", size)
    bw = tw + 22 + 22 + 26
    if solid:
        d.add(f'<rect x="{num(x)}" y="{num(y)}" width="{num(bw)}" height="{h}" rx="14" fill="{solid_grad(d, x, x + bw)}"/>')
        c = "#fff"
    else:
        d.add(f'<rect x="{num(x + .75)}" y="{num(y + .75)}" width="{num(bw - 1.5)}" height="{h - 1.5}" rx="13.25" fill="none" '
              f'stroke="{t["text"]}" stroke-opacity=".28" stroke-width="1.5"/>')
        c = t["text"]
    d.text(x + 22, y + h / 2 + size * 0.36, label_, "sans-b", size, c)
    arrow(d, x + bw - 36, y + h / 2 + 7, 12, c, 2.4, down=label_ == "下载")
    return bw


# ═══════════════════════════════════════════════════════════════════
#  首屏
# ═══════════════════════════════════════════════════════════════════

HEAD_GRAD = [(0, "#9db0ff"), (0.5, "#b79bff"), (1, "#5ee6f0")]


def hero(t, mobile=False):
    title = f"decli — {C.HEAD_A}{C.HEAD_B}" + "".join(C.LEDE)
    N = NIGHT
    lede = [C.LEDE[0], C.LEDE[2]]
    kinds = len({w["cat_zh"] for w in C.WORKS})
    stats = [(str(C.N), "个作品"), (str(C.LIVE), "个点开就能用"), (str(kinds), "种形态")]
    if not mobile:
        W, H, X = DW, 1000, 96
        d = doc(W, H + PB, title)
        hs = 136
        y1 = 470
        y2 = y1 + hs * 1.14
        yl = y2 + 96
        div = H - 186                     # 分隔线：在字下面是一条平直的细线，过了字就升起来，变成极光的底边
        hem = Hem.through([(X, div), (520, div), (880, div), (1010, div - 60), (1160, 620), (1290, 618),
                           (1400, 704), (1560, 650), (W + 40, 760)])
        sky(d, W, H, hem=hem, top=40, x0=950, avoid=[(X, y1 - hs, 940, yl + 60), (X, H - 160, 1000, H - 60), (X, 60, 700, 140)])
        logo(d, X, 76, 60)
        d.text(X + 80, 118, "decli", "sans-b", 34, N["text"], cls="fade")
        label(d, X + 80 + d.width("decli", "sans-b", 34) + 22, 116, f"AI native · {C.ROLE}", N["text3"], 21, cls="fade")
        pw = d.width("decli.github.io", "sans-m", 23) + 82
        d.add(f'<rect x="{num(W - X - pw)}" y="78" width="{num(pw)}" height="56" rx="28" fill="{N["glass"]}" '
              f'fill-opacity="{N["glass_op"]}" stroke="{N["line"]}" stroke-opacity=".22" stroke-width="1.5"/>')
        d.text(W - X - pw + 24, 114, "decli.github.io", "sans-m", 23, N["text"])
        arrow(d, W - X - 38, 112, 12, N["text"], 2.4)
        d.text(X - 6, y1, C.HEAD_A, "black", hs, N["text"], track=-0.02, cls="up", extra=delay(0.5), halt=True)
        g = grad(d, X, X + d.width(C.HEAD_B, "black", hs, -0.02, halt=True), HEAD_GRAD)
        d.text(X - 6, y2, C.HEAD_B, "black", hs, g, track=-0.02, cls="up", extra=delay(0.62), halt=True)
        for i, ln in enumerate(lede):
            d.text(X, yl + i * 50, ln, "sans", 31, N["text2"], cls="up", extra=delay(0.8 + i * 0.06))
        y = H - 80
        x = X
        for i, (n, lab) in enumerate(stats):     # 三组之间的空一样大（量出来的），不是按固定列宽摆
            fill = N["text"]
            nw = d.text(x, y, n, "black", 64, fill, cls="up", extra=delay(1.0 + i * 0.08))
            lw_ = d.text(x + nw + 16, y - 6, lab, "sans-m", 26, N["text2"], cls="up", extra=delay(1.04 + i * 0.08))
            x += nw + 16 + lw_ + 104
        return d
    W, M = MW, 36
    lede_l = kit.wrap("".join(lede), STACKS["sans"], 28, W - 2 * M)
    hs = 84
    y_h1 = 470
    y_h2 = y_h1 + hs * 1.16
    y_l = y_h2 + 80
    y_r = y_l + (len(lede_l) - 1) * 45 + 60
    y_n = y_r + 100
    H = y_n + 92
    d = doc(W, H + PBM, title)
    hem = Hem.through([(-20, 372), (150, 352), (330, 296), (470, 330), (W + 30, 344)])
    sky(d, W, H, rx=22, hem=hem, top=100, x0=-20, x1=W + 20, star_n=34, avoid=[(M, 40, 300, 110), (M, y_h1 - hs, W, H)])
    logo(d, M, 48, 52)
    d.text(M + 68, 84, "decli", "sans-b", 30, N["text"])
    label(d, W - M, 82, C.ROLE, N["text3"], 21, anchor="end")
    d.text(M - 4, y_h1, C.HEAD_A, "black", hs, N["text"], track=-0.02, cls="up", extra=delay(0.5), halt=True)
    g = grad(d, M, M + d.width(C.HEAD_B, "black", hs, -0.02, halt=True), HEAD_GRAD)
    d.text(M - 4, y_h2, C.HEAD_B, "black", hs, g, track=-0.02, cls="up", extra=delay(0.6), halt=True)
    for i, ln in enumerate(lede_l):
        d.text(M, y_l + i * 45, ln, "sans", 28, N["text2"], cls="up", extra=delay(0.75 + i * 0.05))
    hairline(d, N["line"], 0.18, M, y_r, W - M)
    colw = (W - 2 * M) / 3
    for i, (n, lab) in enumerate(stats):
        x = M + i * colw
        fill = N["text"]
        d.text(x, y_n, n, "black", 64, fill, cls="up", extra=delay(0.9 + i * 0.08))
        d.text(x, y_n + 46, lab, "sans", 25, N["text2"], cls="up", extra=delay(0.95 + i * 0.08))
    return d


# ═══════════════════════════════════════════════════════════════════
#  段落标题：一行小字 + 一句标题
# ═══════════════════════════════════════════════════════════════════

def section_head(d, t, eyebrow, title, mobile=False):
    if mobile:
        label(d, 0, 34, eyebrow, t["brand2"], 20, stack="mono-m", track=0.14)
        d.text(-2, 102, title, "sans-b", 52, t["text"], track=-0.01)
        return 102 + 66
    label(d, 0, 36, eyebrow, t["brand2"], 23, stack="mono-m", track=0.16)
    d.text(-4, 128, title, "sans-b", 80, t["text"], track=-0.02)
    return 128 + 66


def head_only(t, eyebrow, title, mobile=False):
    d = doc(MW if mobile else DW, 10, title)
    y = section_head(d, t, eyebrow, title, mobile=mobile)
    d.h = y - 56                      # 加上段距和行尾空隙，正好是标题到内容的 66
    return d


# ═══════════════════════════════════════════════════════════════════
#  方法：三张玻璃卡 + 一条 AI 带
# ═══════════════════════════════════════════════════════════════════

def ai_pill(d, x, y, h, size):
    w = h * 1.55
    d.add(f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{h}" rx="{h / 2}" fill="{solid_grad(d, x, x + w, 1, 2)}"/>')
    d.text(x + w / 2, y + h / 2 + size * 0.36, "AI", "black", size, "#fff", anchor="middle")
    return w


def method(t, mobile=False):
    title = "方法：我只做三件事 —— 定方向、设规则、验结果；UI 交互设计、写代码、跑测试、修 bug、部署上线，全部交给 AI。"
    if not mobile:
        W = DW
        d = doc(W, 900, title)
        y = section_head(d, t, "01 · method", "我只做三件事")
        gap = 24
        cw = (W - 2 * gap) / 3
        ch = 276
        for i, (name, desc, ic) in enumerate(C.STEPS):
            x = i * (cw + gap)
            card(d, t, x, y, cw, ch, glows=[(x + 96, y + 96, 220, 170, AUR[i % 3], t["glow"])])
            d.add(f'<rect x="{num(x + P)}" y="{num(y + 48)}" width="64" height="64" rx="18" fill="{solid_grad(d, x + P, x + P + 64)}"/>')
            line_icon(d, ic, x + P + 16, y + 48 + 16, 32, "#fff", 2.2)
            d.text(x + P, y + 48 + 64 + 62, name, "sans-b", 42, t["text"])
            d.text(x + P, y + 48 + 64 + 110, desc, "sans", 28, t["text2"])
        y += ch + gap
        bh = 116
        card(d, t, 0, y, W, bh, rx=bh / 2)
        flow = d.uid("fl")
        d.deff(f'<linearGradient id="{flow}" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{t["brand3"]}" stop-opacity="0"/>'
               f'<stop offset=".5" stop-color="{t["brand2"]}" stop-opacity="{t["glow"] * 1.2:.2f}"/>'
               f'<stop offset="1" stop-color="{t["brand3"]}" stop-opacity="0"/></linearGradient>')
        cid = d.uid("fc")
        d.deff(f'<clipPath id="{cid}"><rect x="0" y="{num(y)}" width="{W}" height="{bh}" rx="{bh / 2}"/></clipPath>')
        d.style(f"@keyframes {flow}{{from{{transform:translateX(-500px)}}to{{transform:translateX({W}px)}}}}"
                f".{flow}{{animation:{flow} 6s cubic-bezier(.45,0,.55,1) 3}}")
        d.add(f'<g clip-path="url(#{cid})"><rect class="{flow}" x="0" y="{num(y)}" width="500" height="{bh}" fill="url(#{flow})"/></g>')
        pw = ai_pill(d, 26, y + 26, 64, 30)
        lead = "其余，全部交给它"
        lx = 26 + pw + 28
        lwid = d.text(lx, y + bh / 2 + 11, lead, "sans-b", 31, brand_grad(d, t, lx, lx + 260))
        sep = lx + lwid + 40
        d.add(f'<path d="M{num(sep)} {num(y + 34)}V{num(y + bh - 34)}" stroke="{t["text3"]}" stroke-opacity=".35" stroke-width="1.5"/>')
        items = C.AI_DOES
        size = 29
        ws = [d.width(c, "sans-m", size) for c in items]
        x = sep + 44
        gap2 = (W - 48 - x - sum(ws)) / (len(items) - 1)
        for k, (c, w_) in enumerate(zip(items, ws)):
            d.text(x, y + bh / 2 + 10, c, "sans-m", size, t["text"])
            if k < len(items) - 1:
                ax = x + w_ + gap2 / 2
                d.add(f'<path d="M{num(ax - 5)} {num(y + bh / 2 - 9)}l8 9-8 9" fill="none" stroke="#8b93b8" stroke-width="2.6" '
                      f'stroke-linecap="round" stroke-linejoin="round"/>')
            x += w_ + gap2
        d.h = y + bh + PB
        return d
    W = MW
    d = doc(W, 2000, title)
    y = section_head(d, t, "01 · method", "我只做三件事", mobile=True)
    for i, (name, desc, ic) in enumerate(C.STEPS):
        ch = 150
        card(d, t, 0, y, W, ch, rx=22, glows=[(70, y + 70, 160, 120, AUR[i % 3], t["glow"])])
        d.add(f'<rect x="{PM}" y="{num(y + 43)}" width="64" height="64" rx="18" fill="{solid_grad(d, PM, PM + 64)}"/>')
        line_icon(d, ic, PM + 16, y + 59, 32, "#fff", 2.2)
        d.text(PM + 88, y + 70, name, "sans-b", 36, t["text"])
        d.text(PM + 88, y + 112, desc, "sans", 26, t["text2"])
        y += ch + 16
    n = len(C.AI_DOES)
    ch = 116 + n * 58 + 30
    card(d, t, 0, y, W, ch, rx=22)
    ai_pill(d, PM, y + 30, 56, 26)
    d.text(PM + 110, y + 68, "其余，全部交给它", "sans-b", 30, brand_grad(d, t, PM + 110, PM + 380))
    yy = y + 140
    d.add(f'<path d="M{PM + 10} {num(yy)}V{num(yy + (n - 1) * 58)}" stroke="{t["text3"]}" stroke-opacity=".4" stroke-width="2"/>')
    for c in C.AI_DOES:
        d.add(f'<circle cx="{PM + 10}" cy="{num(yy)}" r="6" fill="{t["brand2"]}"/>')
        d.text(PM + 40, yy + 10, c, "sans-m", 28, t["text"])
        yy += 58
    d.h = y + ch + PBM
    return d


# ═══════════════════════════════════════════════════════════════════
#  正在做：codeless —— $0.0127 领衔
# ═══════════════════════════════════════════════════════════════════

def codeless(t, mobile=False):
    w = C.BY["codeless"]
    title = f"正在做：codeless —— {w['desc']} 实测：一句「做一个咖啡店单页官网」，13 次模型调用、一轮通过、全部成本 $0.0127。"
    steps = C.POC["steps"]
    blurb = w["desc"].split("。")[1] + "。"          # 「全程不用碰 IDE，做完接着说「换成卡片风格」就能改。」
    if not mobile:
        W = DW
        d = doc(W, 1400, title)
        y0 = section_head(d, t, "02 · now", "正在做：一句话，一个网站")
        at = len(d.body)
        X = P
        y = y0 + P
        icon(d, t, w, X, y, 64)
        d.text(X + 88, y + 46, "codeless", "sans-b", 44, t["text"])
        y += 64 + 54
        x = X
        for tg in ["AI Agent", "自托管", "Docker + CI"]:
            tw = d.width(tg, "sans-m", 23) + 36
            d.add(f'<rect x="{num(x)}" y="{num(y - 34)}" width="{num(tw)}" height="48" rx="24" fill="{t["chip"]}"/>')
            d.text(x + 18, y - 2, tg, "sans-m", 23, t["text2"])
            x += tw + 10
        y += 78
        y = lines(d, X, y, blurb, "sans", 30, t["text2"], 720, 48)
        y += 70
        sx, sy, gap = X + 12, y, 70
        n = len(steps)
        d.add(f'<path d="M{sx} {sy}V{sy + gap * (n - 1)}" stroke="{t["text3"]}" stroke-opacity=".35" stroke-width="2"/>')
        pid = d.uid("pp")
        d.style(f"@keyframes {pid}{{0%{{transform:translateY(0);opacity:0}}8%{{opacity:1}}85%{{transform:translateY({gap * (n - 1)}px);opacity:1}}"
                f"100%{{transform:translateY({gap * (n - 1)}px);opacity:0}}}}.{pid}{{animation:{pid} 3.2s cubic-bezier(.45,0,.55,1) .6s 2 both}}")
        for i, (k, v) in enumerate(steps):
            yy = sy + i * gap
            last = i == n - 1
            col = t["live"] if last else t["brand"]
            d.add(f'<circle cx="{sx}" cy="{yy}" r="11" fill="{t["card1"]}" stroke="{col}" stroke-width="3"/><circle cx="{sx}" cy="{yy}" r="4.5" fill="{col}"/>')
            d.text(sx + 36, yy + 10, k, "sans-b", 28, t["live"] if last else t["text"])
            d.text(X + 200, yy + 9, v, "sans", 27, t["text2"])
        d.add(f'<circle class="{pid}" cx="{sx}" cy="{sy}" r="17" fill="{t["brand3"]}" fill-opacity=".3"/>')
        yb = sy + gap * (n - 1) + 74
        bw_ = button(d, t, X, yb, "源码", solid=False)
        d.text(X + bw_ + 20, yb + 36, "github.com/decli/codeless", "sans", 23, t["text3"])
        left_end = yb + 56
        bx = 900
        bw = W - P - bx
        cy = y0 + P + 96
        g = brand_grad(d, t, bx, bx + 460)
        nw = d.text(bx - 4, cy, "$0.0127", "black", 120, g, track=-0.03)
        lx = bx + nw + 28
        d.text(lx, cy - 50, "一个网站的", "sans-b", 29, t["text"])
        d.text(lx, cy - 12, "全部成本", "sans-b", 29, t["text"])
        d.text(bx, cy + 52, "DeepSeek · 一轮通过 · 数字出自仓库里的实测记录", "sans", 26, t["text2"])
        by = cy + 92
        bh = Z.browser(d, t, bx, by, bw, "codeless", "它做出来的咖啡店官网", reveal=None)
        ce = by + bh
        end = max(left_end, ce) + 56
        body = d.body[at:]
        d.body = d.body[:at]
        card(d, t, 0, y0, W, end - y0, rx=28, glows=[(W * .05, y0 + 60, 520, 380, AUR[0], t["glow"]),
                                                     (W * .98, end - 40, 620, 420, AUR[1], t["glow"])])
        d.body += body
        d.h = end + PB
        return d
    W = MW
    d = doc(W, 2600, title)
    y0 = section_head(d, t, "02 · now", "一句话，一个网站", mobile=True)
    at = len(d.body)
    X = PM
    y = y0 + PM + 4
    icon(d, t, w, X, y, 60)
    d.text(X + 80, y + 43, "codeless", "sans-b", 40, t["text"])
    y += 60 + 92
    g = brand_grad(d, t, X, X + 300)
    d.text(X - 3, y, "$0.0127", "black", 88, g, track=-0.03)
    y += 50
    d.text(X, y, "一个网站的全部成本 · DeepSeek · 一轮通过", "sans", 24, t["text2"])
    y += 44
    bh = Z.browser(d, t, X, y, W - 2 * X, "codeless", "它做出来的咖啡店官网")
    y += bh + 64
    y = lines(d, X, y, blurb, "sans", 27, t["text2"], W - 2 * X, 44, justify=False)
    y += 60
    d.add(f'<path d="M{X + 10} {num(y - 9)}V{num(y - 9 + 54 * (len(steps) - 1))}" stroke="{t["text3"]}" stroke-opacity=".35" stroke-width="2"/>')
    for i, (k, v) in enumerate(steps):
        last = i == len(steps) - 1
        col = t["live"] if last else t["brand"]
        d.add(f'<circle cx="{X + 10}" cy="{num(y - 9)}" r="9" fill="{t["card1"]}" stroke="{col}" stroke-width="2.5"/>'
              f'<circle cx="{X + 10}" cy="{num(y - 9)}" r="3.5" fill="{col}"/>')
        d.text(X + 34, y, k, "sans-b", 26, t["live"] if last else t["text"])
        d.text(X + 154, y, v, "sans", 25, t["text2"])
        y += 54
    y += 14
    button(d, t, X, y, "源码", solid=False, h=52, size=22)
    end = y + 52 + PM
    body = d.body[at:]
    d.body = d.body[:at]
    card(d, t, 0, y0, W, end - y0, rx=22, glows=[(60, y0 + 60, 300, 260, AUR[0], t["glow"]), (W - 40, end - 80, 340, 300, AUR[1], t["glow"])])
    d.body += body
    d.h = end + PBM
    return d


# ═══════════════════════════════════════════════════════════════════
#  作品：一件一张，左右交替
# ═══════════════════════════════════════════════════════════════════

ORDER, FEATURED, NO = Z.ORDER, Z.FEATURED, Z.NO
REST = [s for s in ORDER if s not in FEATURED and s != "codeless"]


def framed_shot(d, t, x, y, w, h, slug, mobile=False):
    Z.cover(d, t, x, y, w, h, slug, clip=(x, y, w, h, 14), mobile=mobile)
    d.add(f'<rect x="{num(x + .75)}" y="{num(y + .75)}" width="{num(w - 1.5)}" height="{num(h - 1.5)}" rx="13.25" fill="none" '
          f'stroke="{t["frame_line"]}" stroke-opacity="{t["frame_op"]}" stroke-width="1.5"/>')


def tile_icon(d, t, w, x, y, size):
    """索引里的图标统一成一种品牌底：深 / 浅底块 + 紫到青的线条图形。颜色只留给分类圆点。"""
    rx = size * 0.28
    g = grad(d, x, x + size, [(0, "#8b7cf6"), (1, "#22d3ee")] if not t["shadow"] else [(0, "#5b3fd6"), (1, "#0e7490")])
    k = size * 0.54 / 24
    off = size * 0.23
    d.add(f'<rect x="{num(x)}" y="{num(y)}" width="{size}" height="{size}" rx="{num(rx)}" fill="{t["tile"]}"/>'
          f'<g transform="translate({num(x + off)} {num(y + off)}) scale({k:.3f})" fill="none" stroke="{g}" '
          f'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{C.ICONS[w["icon"]]}</g>')


def plate(w, t, i, mobile=False, last=False):
    title = C.alt_work(w)
    kind, where = Z.link_label(w)
    a, b = w["tint"]
    meta = f"{w['cat_zh']} · {w['for_']}"
    gap = 40 if not last else PB
    if not mobile:
        W, H = DW, 678
        d = doc(W, H + gap, title)
        left = i % 2 == 0
        sw, sh = 880, 550
        sx = P if left else W - P - sw
        card(d, t, 0, 0, W, H, rx=28, glows=[(sx + sw / 2, H * 0.55, sw * 0.62, H * 0.62, a, t["glow"] * 1.1),
                                             (sx + sw * 0.9, H * 0.9, sw * 0.4, H * 0.4, b, t["glow"])])
        framed_shot(d, t, sx, P, sw, sh, w["slug"])
        X = sx + sw + 72 if left else P
        tw = W - sw - 2 * P - 72
        names = d.wrap(w["name"], "sans-b", 50, tw)
        desc = d.wrap(w["desc"], "sans", 28, tw, max_lines=4)
        block = 72 + 48 + len(names) * 62 + 40 + len(desc) * 46 + 40 + 56
        y = (H - block) / 2
        icon(d, t, w, X, y, 72)
        if w.get("href"):
            lw = d.width("在线", "sans-b", 22) + 50
            bx = X + tw - lw
            d.add(f'<rect x="{num(bx)}" y="{num(y + 16)}" width="{num(lw)}" height="42" rx="21" fill="none" stroke="{t["live"]}" '
                  f'stroke-opacity=".5" stroke-width="1.5"/><circle class="pulse" cx="{num(bx + 21)}" cy="{num(y + 37)}" r="5.5" fill="{t["live"]}"/>')
            d.text(bx + 36, y + 45, "在线", "sans-b", 22, t["live"])
        y += 72 + 48 + 50
        for ln in names:
            d.text(X - 2, y, ln, "sans-b", 50, t["text"])
            y += 62
        d.text(X, y - 14, meta, "sans", 25, t["text3"])
        y += 40
        for k, ln in enumerate(desc):
            d.text(X, y + k * 46, ln, "sans", 28, t["text2"])
        yb = y + (len(desc) - 1) * 46 + 40
        bw = button(d, t, X, yb, kind, solid=kind != "源码")
        if d.width(where, "sans", 23) > tw - bw - 20:
            where = "GitHub 仓库"
        wl = [where]
        for k, ln in enumerate(wl):
            d.text(X + bw + 20, yb + (36 if len(wl) == 1 else 22 + k * 30), ln, "sans", 23, t["text3"])
        return d
    W = MW
    tmp = doc(W, 10, "")
    bl = tmp.wrap(w["brief"], "sans", 28, W - 2 * PM)
    sh = round((W - 2 * PM) / 1.6)          # 截图跟下面的字同一条左边线
    H = PM + sh + 40 + 56 + 50 + (len(bl) - 1) * 45 + 40 + 52 + PM
    d = doc(W, H + gap, title)
    card(d, t, 0, 0, W, H, rx=22, glows=[(W * .5, sh * .6, W * .6, sh * .7, a, t["glow"])])
    framed_shot(d, t, PM, PM, W - 2 * PM, sh, w["slug"], mobile=True)
    y = PM + sh + 40
    icon(d, t, w, PM, y, 56)
    d.text(PM + 74, y + 26, w["name"], "sans-b", 32, t["text"])
    d.text(PM + 74, y + 60, meta, "sans", 24, t["text3"])
    if w.get("href"):
        lw = d.width("在线", "sans-b", 20) + 44
        bx = W - PM - lw
        d.add(f'<rect x="{num(bx)}" y="{num(y + 2)}" width="{num(lw)}" height="38" rx="19" fill="none" stroke="{t["live"]}" '
              f'stroke-opacity=".5" stroke-width="1.5"/><circle cx="{num(bx + 19)}" cy="{num(y + 21)}" r="5" fill="{t["live"]}"/>')
        d.text(bx + 32, y + 28, "在线", "sans-b", 20, t["live"])
    y += 56 + 50
    for ln in bl:
        d.text(PM, y, ln, "sans", 28, t["text2"])
        y += 45
    button(d, t, PM, y - 45 + 40, kind, solid=kind != "源码", h=52, size=22)
    return d


# ═══════════════════════════════════════════════════════════════════
#  另外几个：图标 + 名字 + 一句话 + 分类
# ═══════════════════════════════════════════════════════════════════

CAT_COL = {"web": 0, "ext": 1, "script": 2, "desktop": "#f59e0b", "app": "#ec4899"}


def cat_color(t, cat):
    c = CAT_COL[cat]
    return (t["brand"], t["brand2"], t["brand3"])[c] if isinstance(c, int) else c


def index_row(w, t, mobile=False, last=False):
    title = C.alt_work(w)
    kind, where = Z.link_label(w)
    pad = PB if last else 0
    ic = tile_icon if not w["icon"].startswith("@") else icon
    if not mobile:
        W = DW
        bx, bw = 470, 1380 - 470
        bl = kit.wrap(w["brief"], STACKS["sans"], 28, bw)
        H = 110 + (len(bl) - 1) * 44
        d = doc(W, H + pad, title)
        hairline(d, t["line"], t["line_op"], 0, 1, W)
        if last:
            hairline(d, t["line"], t["line_op"], 0, H + 1, W)
        y = 66
        ic(d, t, w, 0, y - 38, 56)
        d.text(84, y, w["name"], "sans-b", 31, t["text"])
        for k, ln in enumerate(bl):
            d.text(bx, y + k * 44, ln, "sans", 28, t["text2"])
        d.add(f'<circle cx="1418" cy="{y - 9}" r="6" fill="{cat_color(t, w["cat"])}"/>')
        d.text(1436, y, w["cat_zh"], "sans", 26, t["text3"])
        d.text(W - 32, y, kind, "sans-m", 27, t["text"], anchor="end")
        arrow(d, W - 16, y - 3, 12, t["text"], 2.4, down=kind == "下载")
        return d
    W = MW
    bl = kit.wrap(w["brief"], STACKS["sans"], 27, W - 76)
    H = 110 + (len(bl) - 1) * 41 + 28
    d = doc(W, H + pad, title)
    hairline(d, t["line"], t["line_op"], 0, 1, W)
    if last:
        hairline(d, t["line"], t["line_op"], 0, H + 1, W)
    ic(d, t, w, 0, 26, 52)
    d.text(76, 58, w["name"], "sans-b", 30, t["text"])
    d.text(W - 30, 58, kind, "sans-m", 24, t["text"], anchor="end")
    arrow(d, W - 15, 55, 12, t["text"], 2.2, down=kind == "下载")
    for k, ln in enumerate(bl):
        d.text(76, 100 + k * 41, ln, "sans", 27, t["text2"])
    return d


# ═══════════════════════════════════════════════════════════════════
#  我相信的几件事 / 页脚
# ═══════════════════════════════════════════════════════════════════

def beliefs(t, mobile=False):
    items = C.PRINCIPLES[1:]          # 第一条「人出判断，AI 出产能」整页都在讲，这里只留另外两条
    title = "我相信的两件事：" + "".join(h + b for h, b in items)
    if not mobile:
        W = DW
        d = doc(W, 900, title)
        y = section_head(d, t, "05 · beliefs", "我相信的两件事")
        gap = 24
        cw = (W - gap) / 2
        bodies = [d.wrap(b, "sans", 29, cw - 2 * P) for _, b in items]
        ch = 48 + 5 + 72 + 62 + (max(len(b) for b in bodies) - 1) * 48 + 48 + 10
        for i, ((head, _), bl) in enumerate(zip(items, bodies)):
            x = i * (cw + gap)
            card(d, t, x, y, cw, ch, glows=[(x + cw, y, 300, 220, AUR[(i + 1) % 3], t["glow"] * 0.8)])
            d.add(f'<rect x="{num(x + P)}" y="{num(y + 48)}" width="44" height="5" rx="2.5" fill="{solid_grad(d, x + P, x + P + 44, 1, 2)}"/>')
            d.text(x + P, y + 48 + 72, head, "sans-b", 40, t["text"])
            for k, ln in enumerate(bl):
                d.text(x + P, y + 48 + 72 + 62 + k * 48, ln, "sans", 29, t["text2"])
        d.h = y + ch + PB
        return d
    W = MW
    d = doc(W, 2000, title)
    y = section_head(d, t, "05 · beliefs", "我相信的两件事", mobile=True)
    for head, body in items:
        bl = d.wrap(body, "sans", 27, W - 2 * PM)
        ch = PM + 96 + len(bl) * 43 + PM - 16
        card(d, t, 0, y, W, ch, rx=22)
        d.add(f'<rect x="{PM}" y="{num(y + PM)}" width="40" height="5" rx="2.5" fill="{solid_grad(d, PM, PM + 40, 1, 2)}"/>')
        d.text(PM, y + PM + 62, head, "sans-b", 35, t["text"])
        for k, ln in enumerate(bl):
            d.text(PM, y + PM + 112 + k * 43, ln, "sans", 27, t["text2"])
        y += ch + 16
    d.h = y - 16 + PBM
    return d


def footer(t, mobile=False):
    """页脚：同一片夜空的「黎明」—— 没有光帘了，只剩一条发光的地平线。"""
    title = "这一页，同样一行代码没手写：版式、配色、动效和生成它的代码，都是 AI 写的。作品集 decli.github.io"
    N = NIGHT
    if not mobile:
        W, H, X = DW, 560, 96
        d = doc(W, H, title)
        d.add('<g transform="translate(0 28)">')
        hy = H - 116
        hem = Hem((-30, hy + 10), [((400, hy + 30), (800, hy - 26), (1100, hy - 10)), ((1350, hy + 4), (1550, hy + 20), (W + 30, hy - 8))])
        sky(d, W, H, seed=11, hem=hem, rays=False, star_n=34, avoid=[(X, 60, 1400, 440)], blob_op=(.3, .35, .12), dawn=hy)
        label(d, X, 112, "decli · colophon", N["text3"], 21, stack="mono-m", track=0.16)
        d.text(X - 4, 222, "这一页，同样一行代码没手写。", "black", 72, N["text"], track=-0.02)
        d.text(X, 288, "版式、配色、动效和生成它的代码，都是 AI 写的；我只选了方向、验了收。", "sans", 29, N["text2"])
        bx, by = X, 334
        bw = d.width("去作品集", "sans-b", 27) + 92
        d.add(f'<rect x="{bx}" y="{by}" width="{num(bw)}" height="70" rx="18" fill="{solid_grad(d, bx, bx + bw)}"/>')
        d.text(bx + 30, by + 45, "去作品集", "sans-b", 27, "#fff")
        arrow(d, bx + bw - 46, by + 43, 13, "#fff", 2.6)
        d.text(bx + bw + 26, by + 45, "decli.github.io", "sans-m", 27, N["text2"])
        d.text(X, H - 48, f"© 2026 decli · {C.ROLE}", "sans", 22, N["text3"])
        d.text(W - X, H - 48, "字体 Geist · 思源黑体（SIL OFL）", "sans", 22, N["text3"], anchor="end")
        d.add("</g>")
        d.h = H + 28
        return d
    W, H = MW, 620
    d = doc(W, H, title)
    d.add('<g transform="translate(0 20)">')
    hy = H - 132
    hem = Hem((-30, hy + 8), [((200, hy + 26), (400, hy - 20), (W + 30, hy - 4))])
    sky(d, W, H, rx=22, seed=11, hem=hem, rays=False, star_n=18, avoid=[(36, 40, W, 420)], blob_op=(.3, .35, .12), dawn=hy)
    X = 36
    label(d, X, 84, "decli · colophon", N["text3"], 20, stack="mono-m", track=0.14)
    d.text(X - 3, 162, "这一页，", "black", 54, N["text"])
    d.text(X - 3, 228, "同样一行代码没手写。", "black", 54, N["text"])
    lines(d, X, 290, "版式、配色、动效和代码，都是 AI 写的；我只选了方向、验了收。", "sans", 26, N["text2"], W - 2 * X, 42, justify=False)
    by = 380
    bw = W - 2 * X
    d.add(f'<rect x="{X}" y="{by}" width="{bw}" height="68" rx="16" fill="{solid_grad(d, X, X + bw)}"/>')
    tw = d.width("去作品集 decli.github.io", "sans-b", 25)
    d.text(W / 2 - 14, by + 43, "去作品集 decli.github.io", "sans-b", 25, "#fff", anchor="middle")
    arrow(d, W / 2 + tw / 2 - 4, by + 41, 12, "#fff", 2.4)
    d.text(X, H - 40, f"© 2026 decli · {C.ROLE}", "sans", 22, N["text3"])
    d.add("</g>")
    d.h = H + 20
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
    emit("method", method)
    emit("codeless", codeless)
    emit("works", lambda t, mobile: head_only(t, f"03 · selected works · {len(FEATURED)} / {C.N}", "作品", mobile=mobile))
    for i, s in enumerate(FEATURED):
        emit(f"work-{s}", lambda t, mobile, s=s, i=i: plate(C.BY[s], t, i, mobile=mobile, last=i == len(FEATURED) - 1))
    emit("index", lambda t, mobile: head_only(t, "04 · more", f"另外 {len(REST)} 个", mobile=mobile))
    for k, s in enumerate(REST):
        emit(f"row-{s}", lambda t, mobile, s=s, k=k: index_row(C.BY[s], t, mobile=mobile, last=k == len(REST) - 1))
    emit("beliefs", beliefs)
    emit("footer", footer)
    kit.save_seg()

    Pc = lambda *a, **k: kit.picture(*a, prefix=prefix, **k)  # noqa: E731
    md = ["<!-- 由 studio/aurora_pro.py 生成，别手改。改文案改 build.py 的数据，再跑 python3 studio/build.py -->", ""]
    md.append(Pc("hero", f"decli — {C.HEAD_A}{C.HEAD_B}" + "".join(C.LEDE), "100%", C.SITE))
    md += ["", Pc("method", "我只做三件事：定方向、设规则、验结果。UI 交互设计、写代码、跑测试、修 bug、部署上线，全部交给 AI。", "100%")]
    cl = C.BY["codeless"]
    md += ["", Pc("codeless", f"正在做：codeless —— {cl['desc']}", "100%", cl["link"])]
    md += ["", Pc("works", "03 作品", "100%")]
    md += ["", "<p>" + "".join(Pc(f"work-{s}", C.alt_work(C.BY[s]), "100%", C.BY[s]["link"]) for s in FEATURED) + "</p>"]
    md += ["", Pc("index", f"另外 {len(REST)} 个作品", "100%")]
    md += ["", "<p>" + "".join(Pc(f"row-{s}", C.alt_work(C.BY[s]), "100%", C.BY[s]["link"]) for s in REST) + "</p>"]
    md += ["", Pc("beliefs", "我相信的两件事：" + " ".join(h + b for h, b in C.PRINCIPLES[1:]), "100%")]
    md += ["", Pc("footer", "这一页同样一行代码没手写。作品集 decli.github.io", "100%", C.SITE), ""]
    (out / "README.md").write_text("\n".join(md))
    tot = {}
    for k, v in sizes.items():
        key = "-".join(k.split("-")[-2:])
        tot[key] = tot.get(key, 0) + v
    big = sorted(sizes.items(), key=lambda kv: -kv[1])[:5]
    print("  一页加载：" + "  ".join(f"{k} {v / 1024:.0f} KB" for k, v in tot.items()))
    print("  最大的几张：" + "  ".join(f"{k} {v / 1024:.0f} KB" for k, v in big))


if __name__ == "__main__":
    build(kit.ROOT if "--home" in sys.argv else kit.ROOT / "styles" / "aurora-pro")
