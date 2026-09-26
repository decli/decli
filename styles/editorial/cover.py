#!/usr/bin/env python3
"""
刊物风格 · 《零行》。主页是一本每天清晨自己出刊的杂志。

    python3 cover.py                    按今天（San Jose 时间）出一期
    python3 cover.py --date 2026-10-01  出指定日期那一期（看效果用）
    python3 cover.py --home             生成到仓库根目录（上线）

── 交互是怎么跑起来的 ──
这一套不靠点，靠「时间」和「主题」：
1. 每天清晨 6 点（San Jose），Action 出一期新的：期号 +1，封面故事轮到下一件作品，
   封面画面、正文里的「封面故事」一起换。隔几天再来，看到的就不是上次那本。
2. 日刊 / 夜刊：GitHub 亮色主题拿到的是米白纸的日刊，暗色主题拿到的是墨色的夜刊 ——
   不只是换个颜色，封面上的几条导读也不一样。夜刊里有一条写着「你切到了暗色主题」。
3. 正文里的目录、往期、编者按都折叠着，点开来读，像翻杂志。

刊名「零行」：十五个作品，一行代码没写。
"""

import datetime
import hashlib
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import _kit as kit  # noqa: E402

B = kit.base
HERE = pathlib.Path(__file__).resolve().parent
EPOCH = datetime.date(2026, 9, 26)  # 创刊日，这一天是第 1 期。上线那天可以改成上线日期
W, H = 840, 1150
WEEK = "一二三四五六日"

BLACK = "'ZL Black', 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', STSong, SimSun, serif"
SERIF = "'ZL Serif', 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', STSong, SimSun, serif"

ED = {  # 日刊是米白纸黑字，夜刊是墨底米字。朱红是刊物的「印章色」，两版都用
    "light": dict(name="日刊", bg="#f1ece1", ink="#171513", ink2="#5d564c", accent="#d9381e", grain=.09),
    "dark": dict(name="夜刊", bg="#13120f", ink="#ece6d8", ink2="#a59d8f", accent="#ff5a3c", grain=.06),
}
TEASERS = {
    "light": [("特稿", "十五个作品，一行代码没写"), ("实测", "一句话做一个网站，花了 $0.0127"),
              ("家事", "给老爸的象棋，为什么要放大到 14 寸"), ("方法", "人出判断，AI 出产能")],
    "dark": [("夜话", "AI 为了让检查变绿，偷偷改了规则"), ("深读", "报告状态的和做验证的，必须是两个主体"),
             ("彩蛋", "你切到了暗色主题，拿到的是夜刊"), ("预告", "明早六点，换下一张封面")],
}


def sanjose_today():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date()
    except Exception:  # 没有时区数据的环境：UTC 往回拨 8 小时，差不多
        return (datetime.datetime.utcnow() - datetime.timedelta(hours=8)).date()


def cover_work(day):
    """每天轮一件作品当封面。先按 slug 的哈希打乱一次，连着几天不会总是同一类。"""
    order = sorted(B.WORKS, key=lambda w: hashlib.md5(w["slug"].encode()).hexdigest())
    return order[(day - EPOCH).days % len(order)]


# ═══════════════════════════════════════════════════════════════════
#  封面画：每件作品一种构图，颜色取它自己的 tint。瑞士海报那一路 —— 圆、弧、条、格
# ═══════════════════════════════════════════════════════════════════

def c(cx, cy, r, fill, extra=""):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"{extra}/>'


def art_sun(rng, c1, c2, t, x, y, w, h):
    R = h * .44
    cx, cy = x + w - R * .78, y + R + 8
    stripes = "".join(
        f'<rect x="{x}" y="{cy + R * (.12 + i * .15):.1f}" width="{w}" height="{R * (.035 + i * .012):.1f}" fill="{t["bg"]}"/>'
        for i in range(6)
    )
    return (
        f'<defs><clipPath id="sun"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R:.1f}"/></clipPath></defs>'
        + c(cx, cy, R, c1) + f'<g clip-path="url(#sun)">{stripes}</g>'
        + c(x + w * .26, y + h * .74, h * .2, c2, ' fill-opacity=".92"')
        + c(x + w * .16, y + h * .22, 13, t["accent"])
        + f'<line x1="{x}" y1="{y + h}" x2="{x + w * .62}" y2="{y + h * .3}" stroke="{t["ink"]}" stroke-width="3"/>'
    )


def art_arcs(rng, c1, c2, t, x, y, w, h):
    cx, cy = x + w, y + h
    cols = [c1, t["bg"], c2, t["bg"], t["ink"], t["bg"], t["accent"]]
    rmax = min(w, h) * 1.02
    out = "".join(c(cx, cy, rmax * (1 - i * .135), cols[i % len(cols)]) for i in range(7))
    return out + c(x + w * .18, y + h * .2, h * .12, c2) + c(x + w * .18, y + h * .2, h * .05, t["bg"])


def art_grid(rng, c1, c2, t, x, y, w, h):
    n = 4
    s = min(w, h) / n
    ox, oy = x + (w - s * n) / 2, y + (h - s * n) / 2
    out = []
    for j in range(n):
        for i in range(n):
            px, py = ox + i * s, oy + j * s
            col = rng.choice([c1, c1, c2, t["ink"], t["accent"]] if (i + j) % 3 else [c1, c2])
            kind = rng.choice(["q0", "q1", "q2", "q3", "half", "dot", "full", "none"])
            if kind == "none":
                continue
            if kind == "full":
                out.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{s:.1f}" height="{s:.1f}" fill="{col}"/>')
            elif kind == "dot":
                out.append(c(px + s / 2, py + s / 2, s * .32, col))
            elif kind == "half":
                out.append(f'<path d="M{px:.1f} {py + s:.1f} A{s / 2:.1f} {s / 2:.1f} 0 0 1 {px + s:.1f} {py + s:.1f} Z" fill="{col}"/>')
            else:
                k = int(kind[1])
                corner = [(px, py), (px + s, py), (px + s, py + s), (px, py + s)][k]
                a = [(px + s, py), (px + s, py + s), (px, py + s), (px, py)][k]
                b = [(px, py + s), (px, py), (px + s, py), (px + s, py + s)][k]
                sweep = 1
                out.append(f'<path d="M{corner[0]:.1f} {corner[1]:.1f} L{a[0]:.1f} {a[1]:.1f} A{s:.1f} {s:.1f} 0 0 {sweep} '
                           f'{b[0]:.1f} {b[1]:.1f} Z" fill="{col}"/>')
    return "".join(out)


def art_bars(rng, c1, c2, t, x, y, w, h):
    out = [c(x + w * .62, y + h * .36, h * .34, c2, ' fill-opacity=".35"')]
    n, gap = 7, 10
    bw = (w - gap * (n - 1)) / n
    hot = rng.randrange(n)
    for i in range(n):
        bh = h * rng.uniform(.28, .96)
        col = t["accent"] if i == hot else (c1 if i % 2 == 0 else c2)
        out.append(f'<rect x="{x + i * (bw + gap):.1f}" y="{y + h - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{col}"/>')
    return "".join(out) + f'<rect x="{x}" y="{y + h - 3}" width="{w}" height="3" fill="{t["ink"]}"/>'


ARTS = [art_sun, art_arcs, art_grid, art_bars]


def barcode(x, y, w, h, seed, ink):
    rng = random.Random(seed)
    out, cx = [], x
    while cx < x + w - 4:
        bw = rng.choice([1.5, 1.5, 3, 4.5])
        out.append(f'<rect x="{cx:.1f}" y="{y}" width="{bw}" height="{h}" fill="{ink}"/>')
        cx += bw + rng.choice([1.5, 3, 3, 4.5])
    return "".join(out)


# ═══════════════════════════════════════════════════════════════════
#  封面
# ═══════════════════════════════════════════════════════════════════

def cover(mode, day):
    t = ED[mode]
    w = cover_work(day)
    issue = (day - EPOCH).days + 1
    black_text, serif_text = [], []

    def txt(x, y, s, size, fill, font="serif", anchor="start", extra=""):
        (black_text if font == "black" else serif_text).append(s)
        fam = "b" if font == "black" else "s"
        return (f'<text class="{fam}" x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
                f'text-anchor="{anchor}"{extra}>{B.e(s)}</text>')

    p = [
        '<defs><filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/>'
        '<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.4 1.1"/></filter>'
        f'<clipPath id="page"><rect width="{W}" height="{H}" rx="6"/></clipPath></defs>',
        f'<g clip-path="url(#page)"><rect width="{W}" height="{H}" fill="{t["bg"]}"/>',
    ]
    # 报头
    date_line = f"第 {issue} 期 · {day.year} 年 {day.month} 月 {day.day} 日 · 星期{WEEK[day.weekday()]}"
    p.append(txt(40, 42, "decli 的个人刊物 · San Jose", 15, t["ink2"]))
    p.append(txt(W - 40, 42, date_line, 15, t["ink2"], anchor="end"))
    p.append(f'<rect x="40" y="58" width="{W - 80}" height="1.5" fill="{t["ink"]}"/>')
    p.append(txt(30, 300, "零行", 252, t["accent"], "black", extra=' letter-spacing="-6"'))
    p.append(txt(574, 142, "ZERO LINES", 30, t["ink"], "black", extra=' letter-spacing="1"'))
    p.append(txt(574, 176, "从界面到每一行代码，", 16, t["ink2"]))
    p.append(txt(574, 200, "全部由 AI 完成。", 16, t["ink2"]))
    # 印章：日刊 / 夜刊
    ring = ' stroke="%s" stroke-width="1.5"' % t["bg"]
    p.append(f'<g transform="rotate(-11 736 266)">{c(736, 266, 46, t["accent"])}{c(736, 266, 40, "none", ring)}'
             + txt(736, 277, t["name"], 30, t["bg"], "black", "middle") + "</g>")
    p.append(f'<rect x="40" y="326" width="{W - 80}" height="4" fill="{t["ink"]}"/>'
             f'<rect x="40" y="334" width="{W - 80}" height="1" fill="{t["ink"]}"/>')
    # 封面画
    ax, ay, aw, ah = 320, 366, 480, 440
    rng = random.Random(w["slug"])
    art = ARTS[int(hashlib.md5(w["slug"].encode()).hexdigest(), 16) % len(ARTS)]
    p.append(f'<defs><clipPath id="art"><rect x="{ax}" y="{ay}" width="{aw}" height="{ah}"/></clipPath></defs>'
             f'<g clip-path="url(#art)">{art(rng, w["tint"][0], w["tint"][1], t, ax, ay, aw, ah)}</g>')
    p.append(B.icon(w, ax + aw - 84, ay + ah - 84, 64, dict(panel=t["bg"], line=t["ink"], line_op=.15)))
    # 导读：夜刊的几条更长、折行更多，条与条之间的间距按剩下的空间收一收，别撞到下面的「封面故事」
    blocks = [(label, B.wrap(line, 22, 268)) for label, line in TEASERS[mode]]

    def last_rule(step):
        ty = 392
        for _, ls in blocks:
            last = ty + 34 + (len(ls) - 1) * 31
            ty = last + step
        return last + step * .36

    step = 62
    while step > 36 and last_rule(step) > 812:
        step -= 1
    ty = 392
    for label, ls in blocks:
        p.append(txt(40, ty, label, 14, t["accent"], extra=' letter-spacing="3" font-weight="700"'))
        for k, ln in enumerate(ls):
            p.append(txt(40, ty + 34 + k * 31, ln, 22, t["ink"]))
        last = ty + 34 + (len(ls) - 1) * 31
        p.append(f'<rect x="40" y="{last + step * .36:.1f}" width="36" height="2" fill="{t["ink"]}"/>')
        ty = last + step
    # 封面故事
    p.append(txt(40, 852, f"封面故事 · {dict(B.CATS)[w['cat']]}", 15, t["accent"], extra=' letter-spacing="2" font-weight="700"'))
    fs = min(118, 760 / (B.tw(w["name"], 1, True) or 1))
    p.append(txt(34, 858 + fs * .92, w["name"], round(fs), t["ink"], "black", extra=' letter-spacing="-2"'))
    for k, ln in enumerate(B.wrap(w["brief"], 20, 760, max_lines=2)):
        p.append(txt(40, 858 + fs * .92 + 44 + k * 30, ln, 20, t["ink2"]))
    # 底栏：定价、网址、条码
    p.append(f'<rect x="40" y="1062" width="{W - 80}" height="1.5" fill="{t["ink"]}"/>')
    p.append(txt(40, 1098, "定价　0 行代码", 21, t["ink"], "black"))
    p.append(f'<text class="m" x="40" y="1124" font-size="13" fill="{t["ink2"]}">decli.github.io</text>')
    p.append(barcode(600, 1076, 200, 40, f"{day}", t["ink"]))
    p.append(f'<text class="m" x="700" y="1134" font-size="11" fill="{t["ink2"]}" text-anchor="middle" '
             f'letter-spacing="2">{day:%Y%m%d}{issue:04d}</text>')
    p.append(f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity="{t["grain"]}"/></g>')
    css = (
        kit.font_face_subset("ZL Black", HERE / "fonts" / "serif-black.woff2", "".join(black_text))
        + kit.font_face_subset("ZL Serif", HERE / "fonts" / "serif-medium.woff2", "".join(serif_text))
        + f".b{{font-family:{BLACK};font-weight:900}}.s{{font-family:{SERIF}}}.m{{font-family:{B.MONO}}}"
    )
    title = (f"《零行》{t['name']} 第 {issue} 期，{day.year} 年 {day.month} 月 {day.day} 日。"
             f"封面故事：{w['name']} —— {w['brief']} 导读：" + "；".join(f"{a}：{b}" for a, b in TEASERS[mode]))
    return kit.svg(W, H, title, "\n".join(p), css), title


# ═══════════════════════════════════════════════════════════════════
#  README：封面下面是正文
# ═══════════════════════════════════════════════════════════════════

def readme(day, pre, names, alt):
    w = cover_work(day)
    n, live = B.stats()
    issue = (day - EPOCH).days + 1
    links = []
    if w.get("href"):
        links.append(f"[在线打开]({w['href']})")
    if w.get("dl"):
        links.append(f"[下载]({w['dl']})")
    links.append(f"[源码]({B.GH}/{w['repo']})")
    md = [B.GENERATED.replace("build.py", "styles/editorial/cover.py"), ""]
    md.append(
        f'<a href="{B.SITE}"><picture><source media="(prefers-color-scheme: dark)" srcset="{pre}{names["dark"]}">'
        f'<img alt="{B.e(alt)}" src="{pre}{names["light"]}" width="100%"></picture></a>'
    )
    md += ["", f'<p align="center"><sub>《零行》第 {issue} 期 · 每天清晨六点（San Jose）自动出刊 · '
               "切换 GitHub 的明暗主题，拿到的是日刊或夜刊</sub></p>", ""]
    md += [f"## 封面故事 · {w['name']}", "", f"> {w['brief']}", "", w["desc"], "",
           f"<sub>{' · '.join(w['tags'])}</sub>", "", " · ".join(links), ""]
    md += ["## 特稿 · 十五个作品，一行代码没写", "", "".join(B.LEDE[:1]), "",
           "我只做三件事：**提出问题**、**选择方案**、**验收结果**。剩下的 —— 从界面设计到每一行代码 —— 全部交给 AI。"
           "不是尝鲜，这是 AI Native 时代工作的新范式。", ""]
    md += ["## 实测 · 一句话做一个网站，花了 $0.0127", "",
           "codeless 的一次 POC：一句「做一个咖啡店单页官网」，AI 在断网的沙箱里调了 13 次模型，验收测试一轮全绿，"
           "推送后 CI 自动部署，点开链接就能访问。", "",
           "```mermaid", "flowchart LR",
           "  A[一句话需求] --> B[断网沙箱里写代码<br/>13 次模型调用]",
           "  B --> C{验收测试}", "  C -- 全绿 --> D[CI 部署] --> E[上线，$0.0127]",
           "  C -- 没过 --> F[AI 自己修] --> C", "```", "",
           f"[看 codeless 的源码]({B.GH}/codeless) · [POC 实测记录]({B.GH}/codeless/blob/main/docs/06-poc-findings.md)", ""]
    md += [f"<details><summary><b>往期 · 全部 {n} 件作品</b></summary>", "", B.works_table(), "", "</details>", ""]
    md += ["<details><summary><b>编者按 · 我相信的几件事</b></summary>", "", B.principles_md(), "", "</details>", ""]
    md += ["---", "", f"<sub>撰文 AI · 审校 decli · 排版 cover.py · 本期出刊于 {day:%Y-%m-%d}</sub>", ""]
    return "\n".join(md)


def render(day, home=False):
    assets = HERE / "assets"
    names, alt = {}, ""
    for mode in ED:
        s, title = cover(mode, day)
        names[mode] = kit.write_hashed(assets, f"cover-{mode}", s)
        if mode == "light":
            alt = title
    pre = "styles/editorial/assets/" if home else "assets/"
    out = kit.ROOT / "README.md" if home else HERE / "README.md"
    out.write_text(readme(day, pre, names, alt))


def chars():
    """这套风格可能用到的所有字 —— tools/fonts.py 按它切宋体子集。"""
    fixed = ("零行ZERO LINES日刊夜刊定价　0 行代码封面故事 · decli 的个人刊物 San Jose 第期年月日星期"
             + WEEK + "从界面到每一行代码，全部由 AI 完成。0123456789")
    teasers = "".join(a + b for v in TEASERS.values() for a, b in v)
    works = "".join(w["name"] + w["brief"] for w in B.WORKS) + "".join(label for _, label in B.CATS)
    ascii_ = "".join(chr(i) for i in range(32, 127))
    return fixed + teasers + works + ascii_


if __name__ == "__main__":
    day = sanjose_today()
    if "--date" in sys.argv:
        day = datetime.date.fromisoformat(sys.argv[sys.argv.index("--date") + 1])
    render(day, "--home" in sys.argv)
