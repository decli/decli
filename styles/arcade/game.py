#!/usr/bin/env python3
"""
街机风格 · 人机五子棋。主页不是用来看的，是用来玩的。

    python3 game.py render                          按 state.json 重画 README 和图
    python3 game.py play "五子棋｜落子 E5" alice 42   人类落子 → AI 回一手 → 重画（Action 里调用）
    加 --home                                       README 生成到仓库根目录，也就是上线

── 交互是怎么跑起来的 ──
README 里没法跑脚本，但链接可以带参数：棋盘上每个空位都是一个链接，指向
「新建 issue」页面，标题已经预填好「五子棋｜落子 E5」。访客只需要点一下 Submit。
仓库里的 Action 盯着新 issue：解析坐标、落子、让 AI 回一手、重画棋盘、提交，
再在 issue 里回一句「AI 回了 F6，轮到你」并关掉它。整个来回大约半分钟。

人执粉，AI 执蓝 —— 「人出判断，AI 出产能」，这次是真的在对弈。
"""

import json
import pathlib
import random
import re
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import _kit as kit  # noqa: E402

B = kit.base
HERE = pathlib.Path(__file__).resolve().parent
STATE = HERE / "state.json"
N = 9
COLS = "ABCDEFGHI"
EMPTY, HUMAN, AI = 0, 1, 2

# PICO-8 的 16 色。像素画就该用有限的调色板，颜色一多就不像了。
P = dict(
    black="#000000", navy="#1D2B53", plum="#7E2553", green="#008751", brown="#AB5236",
    dgray="#5F574F", lgray="#C2C3C7", white="#FFF1E8", red="#FF004D", orange="#FFA300",
    yellow="#FFEC27", lime="#00E436", blue="#29ADFF", lav="#83769C", pink="#FF77A8", peach="#FFCCAA",
)
PX = "'PX', 'Fusion Pixel', ui-monospace, monospace"
CART_ART = {  # 每个作品卡带标签的两种颜色
    "codeless": ("plum", "pink"), "ftms": ("navy", "blue"), "ems": ("blue", "lav"),
    "logicc": ("orange", "yellow"), "wxformat3": ("lav", "pink"), "macpleco": ("green", "lime"),
}
CARTS = ["codeless", "ftms", "ems", "logicc", "wxformat3", "macpleco"]
LIGHT = {"orange", "yellow", "lime", "pink", "peach", "blue", "lgray", "white"}  # 这些底色上压黑字
ISSUE_BODY = "直接点下面的「Submit new issue」就行。大约半分钟后 AI 会回一手，回到 github.com/decli 刷新就能看到。"


# ═══════════════════════════════════════════════════════════════════
#  棋局
# ═══════════════════════════════════════════════════════════════════

def new_state():
    return dict(game=1, board=[[EMPTY] * N for _ in range(N)], moves=[], over=False,
                winner=None, win_cells=[], score=dict(human=0, ai=0, draw=0),
                players={}, winners=[], recent=[])


def load():
    return json.loads(STATE.read_text()) if STATE.exists() else new_state()


def save(s):
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n")


def coord(x, y):
    return f"{COLS[x]}{y + 1}"


DIRS = [(1, 0), (0, 1), (1, 1), (1, -1)]


def run(board, x, y, dx, dy, who):
    """假设 (x, y) 是 who 的子，沿一个方向数连子数和两头有几个空位。"""
    cnt, cells, open_ends = 1, [(x, y)], 0
    for s in (1, -1):
        i = 1
        while True:
            nx, ny = x + s * dx * i, y + s * dy * i
            if 0 <= nx < N and 0 <= ny < N and board[ny][nx] == who:
                cnt += 1
                cells.append((nx, ny))
                i += 1
                continue
            if 0 <= nx < N and 0 <= ny < N and board[ny][nx] == EMPTY:
                open_ends += 1
            break
    return cnt, open_ends, cells


def five(board, x, y, who):
    for dx, dy in DIRS:
        cnt, _, cells = run(board, x, y, dx, dy, who)
        if cnt >= 5:
            return sorted(cells)
    return None


def shape(cnt, open_ends):
    if cnt >= 5:
        return 100000
    table = {4: (0, 1000, 10000), 3: (0, 100, 1000), 2: (0, 10, 100), 1: (0, 1, 10)}
    return table[cnt][open_ends]


def ai_move(board, seed):
    """经典的棋型打分：每个空位同时算「我下这儿能成什么」和「对手下这儿能成什么」。
    进攻分略高于防守分，同分里随机挑一个 —— 不然每局都一模一样，背一遍谱就能赢。"""
    rng = random.Random(seed)
    best, pool = -1.0, []
    for y in range(N):
        for x in range(N):
            if board[y][x] != EMPTY:
                continue
            atk = sum(shape(*run(board, x, y, dx, dy, AI)[:2]) for dx, dy in DIRS)
            dfn = sum(shape(*run(board, x, y, dx, dy, HUMAN)[:2]) for dx, dy in DIRS)
            score = atk * 1.1 + dfn + (4 - max(abs(x - 4), abs(y - 4))) * 0.3
            if score > best + 1e-6:
                best, pool = score, [(x, y)]
            elif abs(score - best) < 1e-6:
                pool.append((x, y))
    return rng.choice(pool)


def place(s, x, y, who, player=None, issue=None):
    s["board"][y][x] = who
    s["moves"].append([x, y, who, player, issue])
    win = five(s["board"], x, y, who)
    if win:
        s["over"], s["winner"], s["win_cells"] = True, ("human" if who == HUMAN else "ai"), win
        s["score"][s["winner"]] += 1
        if who == HUMAN:
            s["winners"].insert(0, dict(player=player, game=s["game"], issue=issue))
            s["winners"] = s["winners"][:10]
    elif all(c != EMPTY for row in s["board"] for c in row):
        s["over"], s["winner"] = True, "draw"
        s["score"]["draw"] += 1


def play(s, title, player, issue):
    """返回要回到 issue 里的那段话。"""
    m = re.search(r"([A-Ia-i])\s*([1-9])", title.split("落子")[-1])
    if not m:
        return f"没看懂这一手。标题要像「五子棋｜落子 E5」这样，列 A–I、行 1–9。回到 {B.GH} 点棋盘最省事。"
    x, y = COLS.index(m.group(1).upper()), int(m.group(2)) - 1
    here = coord(x, y)
    if s["over"]:  # 上一局已经结束：这一手就是新一局的第一手
        keep = {k: s[k] for k in ("score", "players", "winners", "recent", "game")}
        s.clear()
        s.update(new_state())
        s.update(keep)
        s["game"] += 1
    if s["board"][y][x] != EMPTY:
        return f"{here} 已经有子了，换个空位吧 → [回到棋盘]({B.GH})"
    s["players"][player] = s["players"].get(player, 0) + 1
    place(s, x, y, HUMAN, player, issue)
    s["recent"].insert(0, dict(player=player, at=here, issue=issue, game=s["game"]))
    s["recent"] = s["recent"][:6]
    if s["over"]:
        if s["winner"] == "human":
            return f"**{here}，五子连珠 —— 你赢了！** 第 {s['game']} 局归人类，名字已经刻进名人堂。[回去看看]({B.GH})"
        return f"{here}，棋盘下满了，和棋。[再来一局]({B.GH})"
    ax, ay = ai_move(s["board"], seed=f"{s['game']}-{len(s['moves'])}")
    place(s, ax, ay, AI)
    if s["over"] and s["winner"] == "ai":
        return f"你下在 {here}，AI 回了 **{coord(ax, ay)}** —— 连成五子，这局 AI 赢了。[点任意格子再来一局]({B.GH})"
    return f"你下在 {here}，AI 回了 **{coord(ax, ay)}**。轮到你了 → [回到棋盘]({B.GH})"


# ═══════════════════════════════════════════════════════════════════
#  像素画
# ═══════════════════════════════════════════════════════════════════

def rect(x, y, w, h, c, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{P.get(c, c)}"{extra}/>'


def pixels(rows, x0, y0, u, colors):
    """用字符画一张像素图：rows 是字符串列表，colors 把字符映射成颜色，空格和 . 是透明。"""
    out = []
    for j, row in enumerate(rows):
        i = 0
        while i < len(row):
            ch = row[i]
            if ch in " .":
                i += 1
                continue
            k = i
            while k < len(row) and row[k] == ch:  # 同色连成一条，少画几个方块
                k += 1
            out.append(rect(x0 + i * u, y0 + j * u, (k - i) * u, u, colors[ch]))
            i = k
    return "".join(out)


GLYPH = {  # 3×5 的小点阵，只给棋盘坐标用 —— 为 18 个小图各嵌一份字体太浪费
    "A": ".#.|#.#|###|#.#|#.#", "B": "##.|#.#|##.|#.#|##.", "C": ".##|#..|#..|#..|.##",
    "D": "##.|#.#|#.#|#.#|##.", "E": "###|#..|##.|#..|###", "F": "###|#..|##.|#..|#..",
    "G": ".##|#..|#.#|#.#|.##", "H": "#.#|#.#|###|#.#|#.#", "I": "###|.#.|.#.|.#.|###",
    "1": ".#.|##.|.#.|.#.|###", "2": "##.|..#|.#.|#..|###", "3": "##.|..#|.#.|..#|##.",
    "4": "#.#|#.#|###|..#|..#", "5": "###|#..|##.|..#|##.", "6": ".##|#..|###|#.#|###",
    "7": "###|..#|.#.|.#.|.#.", "8": "###|#.#|###|#.#|###", "9": "###|#.#|###|..#|##.",
}

CELL = 40  # 含四周各 2px 的透明边：格子之间自然留出 4px 缝，像一排排街机按钮

# 9×9 的按钮，每格 4px。o 描边、c 按钮面、h 高光、s 下沿阴影
BUTTON = [
    ".ooooooo.",
    "ohhhhhhco",
    "ohcccccco",
    "occccccco",
    "occccccco",
    "occccccco",
    "occccccso",
    "ossssssso",
    ".ooooooo.",
]


def cell_svg(kind):
    """kind: empty / h / a，后缀 -last（刚落的那手，边框闪）、-win（连成五子的那几颗）"""
    base_kind, _, flag = kind.partition("-")
    if base_kind == "empty":
        colors = dict(o=P["black"], h=P["dgray"], c=P["navy"], s=P["black"])
        dot = rect(18, 18, 4, 4, "dgray")
    elif base_kind == "h":
        colors = dict(o=P["plum"], h=P["white"], c=P["pink"], s=P["red"])
        dot = ""
    else:
        colors = dict(o=P["navy"], h=P["white"], c=P["blue"], s=P["navy"])
        dot = ""
    if flag == "win":
        colors["c"] = P["yellow"]
        colors["s"] = P["orange"]
    body = pixels(BUTTON, 2, 2, 4, colors) + dot
    css = ""
    if flag == "last":  # 四个角各一个黄色像素，一闪一闪：刚落的就是这一手
        body += (
            '<g class="blink">' + rect(2, 2, 8, 4, "yellow") + rect(2, 2, 4, 8, "yellow")
            + rect(30, 2, 8, 4, "yellow") + rect(34, 2, 4, 8, "yellow")
            + rect(2, 34, 8, 4, "yellow") + rect(2, 30, 4, 8, "yellow")
            + rect(30, 34, 8, 4, "yellow") + rect(34, 30, 4, 8, "yellow") + "</g>"
        )
        css = ".blink{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
    if flag == "win":
        css = "g.w{animation:glow 1.2s steps(2) infinite}@keyframes glow{50%{opacity:.55}}"
        body = f'<g class="w">{body}</g>'
    title = {"empty": "空位", "h": "人类", "a": "AI"}[base_kind]
    return kit.svg(CELL, CELL, title, f'<g shape-rendering="crispEdges">{body}</g>', css)


def label_svg(ch):
    glyph = GLYPH[ch].split("|")
    # 薰衣草紫在白底和 GitHub 暗色底上对比度都够；浅灰在白底上几乎看不见
    body = pixels([row.replace("#", "g") for row in glyph], 14, 10, 4, dict(g=P["lav"]))
    return kit.svg(CELL, CELL, ch, f'<g shape-rendering="crispEdges">{body}</g>')


def fonts_css():
    return kit.font_face("PX", HERE / "fonts" / "pixel.woff2") + f"text{{font-family:{PX}}}"


def ptext(x, y, s, size=24, color="white", anchor="start", extra=""):
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{P.get(color, color)}" '
        f'text-anchor="{anchor}"{extra}>{B.e(s)}</text>'
    )


def scanlines(w, h, r=14):
    return (
        '<defs><pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="2" fill="#000" fill-opacity=".22"/></pattern>'
        '<radialGradient id="vig" cx=".5" cy=".5" r=".75"><stop offset=".6" stop-color="#000" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient></defs>'
        f'<rect width="{w}" height="{h}" rx="{r}" fill="url(#scan)"/>'
        f'<rect width="{w}" height="{h}" rx="{r}" fill="url(#vig)"/>'
    )


def title_svg(s):
    """标题画面：合成器浪潮式的像素落日 + 冲过来的网格地面 + 投币提示。"""
    W, H, HZ = 840, 440, 280  # HZ：地平线
    rng = random.Random(7)
    parts = ['<defs><clipPath id="scr"><rect width="840" height="440" rx="20"/></clipPath></defs>',
             '<g clip-path="url(#scr)" shape-rendering="crispEdges">']
    # 天空：三段色带，像素画不用渐变
    parts += [rect(0, 0, W, 120, "black"), rect(0, 120, W, 90, "#0b0f24"), rect(0, 210, W, HZ - 210, "navy")]
    # 星星
    stars = []
    for i in range(46):
        x, y = rng.randrange(0, W // 4) * 4, rng.randrange(2, 50) * 4
        c = rng.choice(["white", "lgray", "blue", "peach"])
        sz = 4 if i % 5 else 8
        stars.append(f'<g class="tw t{i % 4}">{rect(x, y, sz, sz, c)}</g>')
    parts += stars
    # 太阳：一行一行的像素条，下半截挖出横缝
    cx, R, u = W // 2, 104, 6
    for yy in range(HZ - R, HZ, u):
        dy = HZ - yy - u / 2
        half = int(((R * R - dy * dy) ** .5) // u) * u
        gap = HZ - yy
        if gap < 60 and (gap // u) % 3 == 0:
            continue
        c = "yellow" if yy < HZ - 70 else "orange" if yy < HZ - 40 else "pink" if yy < HZ - 18 else "red"
        parts.append(rect(cx - half, yy, half * 2, u, c))
    # 地面 + 透视网格
    parts.append(rect(0, HZ, W, H - HZ, "black"))
    for k in range(-9, 10):
        parts.append(f'<line x1="{cx}" y1="{HZ}" x2="{cx + k * 110}" y2="{H}" stroke="{P["plum"]}" stroke-width="2"/>')
    parts.append(f'<line x1="0" y1="{HZ}" x2="{W}" y2="{HZ}" stroke="{P["pink"]}" stroke-width="2"/>')
    for i in range(6):
        parts.append(f'<line class="fl" style="animation-delay:{-i * 0.6:.1f}s" x1="0" y1="{HZ}" x2="{W}" y2="{HZ}" '
                     f'stroke="{P["pink"]}" stroke-width="2"/>')
    parts.append("</g>")
    # 字：logo 三层错位投影，标准的街机标题
    for dx, c in ((8, "plum"), (4, "red")):
        parts.append(ptext(W / 2 + dx, 128 + dx, "DECLI", 96, c, "middle"))
    parts.append(ptext(W / 2, 128, "DECLI", 96, "yellow", "middle"))
    n, live = B.stats()
    parts.append(ptext(W / 2, 176, f"{B.cn(n)}个作品 · 一行代码没写", 24, "white", "middle"))
    parts.append(ptext(40, 44, f"第 {s['game']} 局", 24, "lgray"))
    parts.append(ptext(W - 40, 44, "SAN JOSE", 24, "lgray", "end"))
    sc = s["score"]
    parts.append(ptext(40, H - 40, f"1P 人类  {sc['human']}", 24, "pink"))
    parts.append(ptext(W - 40, H - 40, f"AI 2P  {sc['ai']}", 24, "blue", "end"))
    parts.append(f'<g class="blink">{ptext(W / 2, H - 40, "▶ 点下面的棋盘落子", 24, "yellow", "middle")}</g>')
    parts.append(scanlines(W, H, 20))
    css = fonts_css() + (
        ".blink{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        ".tw{animation:tw 2.4s steps(1) infinite}.t1{animation-delay:-.6s}.t2{animation-delay:-1.2s}.t3{animation-delay:-1.8s}"
        "@keyframes tw{50%{opacity:.25}}"
        f".fl{{animation:fl 3.6s cubic-bezier(.55,0,1,.45) infinite}}"
        f"@keyframes fl{{from{{transform:translateY(0)}}to{{transform:translateY({H - HZ}px)}}}}"
    )
    alt = f"DECLI —— {B.cn(n)}个作品，一行代码没写。人机五子棋第 {s['game']} 局，比分 人类 {sc['human']} : AI {sc['ai']}。"
    return kit.svg(W, H, alt, "\n".join(parts), css), alt


def status_svg(s):
    W, H = 840, 64
    last = s["moves"][-1] if s["moves"] else None
    if s["over"]:
        who = {"human": "人类胜！", "ai": "AI 胜", "draw": "和棋"}[s["winner"]]
        mid, mid_c = f"第 {s['game']} 局 {who}", "yellow"
        right = "点任意格子开新局"
    else:
        mid, mid_c = "轮到你了 ▶", "yellow"
        right = f"AI 上一手 {coord(last[0], last[1])}" if last and last[2] == AI else "你先手，下哪都行"
    body = (
        rect(0, 0, W, H, "black", ' rx="10"') + rect(4, 4, W - 8, H - 8, "navy", ' rx="7"')
        + ptext(28, 42, f"第 {len(s['moves'])} 手", 24, "lgray")
        + f'<g class="blink">{ptext(W / 2, 42, mid, 24, mid_c, "middle")}</g>'
        + ptext(W - 28, 42, right, 24, "pink" if not s["over"] else "lgray", "end")
    )
    css = fonts_css() + ".blink{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:.35}}"
    alt = f"第 {s['game']} 局，第 {len(s['moves'])} 手。{mid}。{right}。"
    return kit.svg(W, H, alt, body, css), alt


def cart_svg(w, idx):
    """作品是一盘一盘的卡带。"""
    W, H = 264, 190
    a, b = CART_ART[w["slug"]]
    shell = [  # 卡带外壳：浅灰机身、顶上几道防滑纹、底部插口
        rect(12, 8, W - 24, H - 16, "dgray"), rect(16, 12, W - 32, H - 24, "lgray"),
        rect(16, 12, W - 32, 4, "white"),
    ]
    for i in range(5):
        shell.append(rect(W / 2 - 60 + i * 26, 20, 16, 4, "dgray"))
    shell += [rect(40, H - 22, W - 80, 10, "dgray"), rect(52, H - 18, W - 104, 6, "black")]
    label = [rect(32, 34, W - 64, 120, "black"), rect(36, 38, W - 72, 112, a),
             rect(36, 38, W - 72, 28, b)]
    name = w["name"]
    # 像素字只在 12 的整数倍字号上清楚，所以长名字不缩字号，按空格断成两行
    lines = [name] if B.tw(name, 24) <= W - 96 else name.split(" ", 1)
    action = "▶ PLAY" if w.get("href") else "▼ 下载" if w.get("dl") else "◆ 源码"
    y0 = 102 if len(lines) == 1 else 94
    ink = "black" if a in LIGHT else "white"
    text = (
        ptext(48, 60, f"STAGE {idx:02d}", 12, "black")
        + "".join(ptext(48, y0 + i * 26, ln, 24, ink) for i, ln in enumerate(lines))
        + ptext(48, 142, action, 12, ink)
    )
    body = f'<g shape-rendering="crispEdges">{"".join(shell + label)}</g>{text}'
    return kit.svg(W, H, f"{name} —— {w['brief']}", body, fonts_css())


def continue_svg():
    """收尾：CONTINUE? 倒数 9→0，一直在转。"""
    W, H = 840, 150
    digits = "".join(
        f'<g class="d" style="animation-delay:{i}s">{ptext(W / 2, 96, str(9 - i), 48, "yellow", "middle")}</g>'
        for i in range(10)
    )
    body = (
        rect(0, 0, W, H, "black", ' rx="20"')
        + ptext(W / 2, 44, "CONTINUE?", 24, "pink", "middle") + digits
        + ptext(W / 2, 128, "全部作品 → decli.github.io", 24, "lgray", "middle")
        + scanlines(W, H, 20)
    )
    css = fonts_css() + ".d{opacity:0;animation:d 10s steps(1) infinite}@keyframes d{0%{opacity:1}10%,100%{opacity:0}}"
    return kit.svg(W, H, "CONTINUE? 全部作品在 decli.github.io", body, css)


# ═══════════════════════════════════════════════════════════════════
#  README
# ═══════════════════════════════════════════════════════════════════

def issue_link(c):
    q = urllib.parse.urlencode({"title": f"五子棋｜落子 {c}", "body": ISSUE_BODY})
    return f"{kit.REPO}/issues/new?{q}"


def board_html(s, pre):
    last = s["moves"][-1][:2] if s["moves"] else None
    win = {tuple(c) for c in s["win_cells"]}
    img = lambda src, alt: f'<img src="{pre}cells/{src}.svg" width="{CELL}" align="top" alt="{alt}">'  # noqa: E731
    rows = [img("corner", "") + "".join(img(f"col-{c}", c) for c in COLS)]
    for y in range(N):
        row = [img(f"row-{y + 1}", str(y + 1))]
        for x in range(N):
            v, c = s["board"][y][x], coord(x, y)
            kind = {EMPTY: "empty", HUMAN: "h", AI: "a"}[v]
            if (x, y) in win:
                kind += "-win"
            elif last and [x, y] == last and v != EMPTY:
                kind += "-last"
            alt = f"{c} " + {EMPTY: "空位，点击落子", HUMAN: "人类", AI: "AI"}[v]
            cell = img(kind, alt)
            # 空位点了就是落子；已经结束的局，点哪都是开新局；有子的格子不给链接
            if v == EMPTY or s["over"]:
                cell = f'<a href="{issue_link(c)}">{cell}</a>'
            row.append(cell)
        rows.append("".join(row))
    return '<p align="center">\n' + "<br>\n".join(rows) + "\n</p>"


def readme(s, pre, status_name, title_name, title_alt, status_alt):
    n, live = B.stats()
    md = [B.GENERATED.replace("build.py", "styles/arcade/game.py"), ""]
    md.append(f'<a href="{B.SITE}"><img src="{pre}{title_name}" width="100%" alt="{B.e(title_alt)}"></a>')
    md += ["", f"### ▶ 人机五子棋 · 第 {s['game']} 局", ""]
    md.append("你执**粉**，AI 执**蓝**，先连成五子的赢。点棋盘上任意空位 → GitHub 会打开一个预填好的 issue → "
              "直接点 **Submit** → 大约半分钟后 AI 回一手，刷新这一页就能看到。")
    md += ["", f'<p align="center"><img src="{pre}{status_name}" width="100%" alt="{B.e(status_alt)}"></p>', ""]
    md.append(board_html(s, pre))
    sc = s["score"]
    md += ["", f"<p align=\"center\"><sub>战绩 · 人类 <b>{sc['human']}</b> 胜 · AI <b>{sc['ai']}</b> 胜 · 和 {sc['draw']} · "
               f"已有 {len(s['players'])} 位访客下过棋</sub></p>", ""]
    md += ["### ▶ STAGE SELECT", "", "<p>"]
    for i, slug in enumerate(CARTS, 1):
        w = kit.work(slug)
        md.append(f'<a href="{B.link_of(w)}"><img src="{pre}cart-{slug}.svg" width="32%" alt="{B.e(w["name"])}"></a>')
    md += ["</p>", "", f"<details><summary><b>ROM LIST · 全部 {n} 个作品</b></summary>", "", B.works_table(), "", "</details>", ""]
    md += ["### ▶ HALL OF FAME", ""]
    if s["winners"]:
        md.append("赢过 AI 的人：" + " · ".join(f"[@{w['player']}](https://github.com/{w['player']})（第 {w['game']} 局）" for w in s["winners"]))
    else:
        md.append("还没有人赢过 AI。第一个名字会刻在这里。")
    if s["recent"]:
        md += ["", "最近落子：" + " · ".join(
            f"[@{r['player']}](https://github.com/{r['player']}) {r['at']}" for r in s["recent"])]
    md += ["", f'<a href="{B.SITE}"><img src="{pre}continue.svg" width="100%" alt="CONTINUE? 全部作品在 decli.github.io"></a>', ""]
    return "\n".join(md)


def render(s, home=False):
    assets = HERE / "assets"
    (assets / "cells").mkdir(parents=True, exist_ok=True)
    for kind in ("empty", "h", "a", "h-last", "a-last", "h-win", "a-win"):
        (assets / "cells" / f"{kind}.svg").write_text(cell_svg(kind))
    for ch in COLS:
        (assets / "cells" / f"col-{ch}.svg").write_text(label_svg(ch))
    for i in range(1, N + 1):
        (assets / "cells" / f"row-{i}.svg").write_text(label_svg(str(i)))
    (assets / "cells" / "corner.svg").write_text(kit.svg(CELL, CELL, "", ""))
    for i, slug in enumerate(CARTS, 1):
        (assets / f"cart-{slug}.svg").write_text(cart_svg(kit.work(slug), i))
    (assets / "continue.svg").write_text(continue_svg())
    t_svg, t_alt = title_svg(s)
    st_svg, st_alt = status_svg(s)
    t_name = kit.write_hashed(assets, "title", t_svg)
    st_name = kit.write_hashed(assets, "status", st_svg)
    pre = "styles/arcade/assets/" if home else "assets/"
    out = kit.ROOT / "README.md" if home else HERE / "README.md"
    out.write_text(readme(s, pre, st_name, t_name, t_alt, st_alt))


def chars():
    """这套风格里可能出现的所有字 —— tools/fonts.py 按它切像素字体的子集。"""
    fixed = (
        "DECLI STAGE PLAY CONTINUE? SAN JOSE ▶▼◆·→：！，。1P 2P AI 人类第局手轮到你了上一手先手下哪都行"
        "胜和棋点任意格子开新局个作品一行代码没写下面的盘落子全部 decli.github.io 下载源码"
        + "".join(B.cn(i) for i in range(1, 100))
    )
    names = "".join(kit.work(s)["name"] for s in CARTS)
    ascii_ = "".join(chr(c) for c in range(32, 127))
    return fixed + names + ascii_


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--home"]
    home = "--home" in sys.argv
    state = load()
    if args[:1] == ["play"]:
        _, title, player, issue = args[:4]
        reply = play(state, title, player, int(issue))
        save(state)
        render(state, home)
        print(reply)
    elif args[:1] == ["render"]:
        save(state)
        render(state, home)
    else:
        sys.exit(__doc__)
