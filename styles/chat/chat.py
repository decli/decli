#!/usr/bin/env python3
"""
对话风格 · decli 的 AI 分身。主页不是一篇介绍，是一段可以点着往下走的对话。

    python3 chat.py            生成 README 和图
    python3 chat.py --home     生成到仓库根目录（上线）

── 交互是怎么跑起来的 ──
两层：
1. 点问题，立刻展开回答。每个「你想问的」都是一个 <details>，摘要是一颗气泡按钮，
   展开是 AI 分身的回答，回答里还能接着点下一个问题 —— 一棵对话树。
   纯 HTML，不需要任何后端，点下去零延迟。
2. 想问树上没有的，点最底下那个输入框：它其实是一个链接，打开预填好的 issue。
   Action 用你给的模型 key 读作品资料、写回复，贴回 issue 里 —— 真的是 AI 在回。
   见 ask.py。
"""

import pathlib
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import _kit as kit  # noqa: E402

B = kit.base
HERE = pathlib.Path(__file__).resolve().parent
ASK_TITLE = "问 decli 的 AI 分身"
ASK_BODY = "（把这一行换成你想问的，比如：codeless 能做手机 App 吗？）"

T = {
    "light": dict(bubble="#eef2f9", text="#101828", text2="#4a566d", meta="#7b879e", card="#ffffff",
                  line="#122044", line_op=.1, field="#f6f8fc", live="#0f9d58", glow=.16),
    "dark": dict(bubble="#161d2f", text="#eaf0ff", text2="#a6b3d2", meta="#78849f", card="#0f1629",
                 line="#96b2f0", line_op=.16, field="#0f1629", live="#34d399", glow=.28),
}
G1, G2, G3 = "#3b5bd6", "#7c5cff", "#06b6d4"  # 渐变：跟作品集同一组 brand 色（压白字用饱和的那组）
FS, LH, MAXW = 15.5, 25, 470
AV = 48  # 头像那一列的宽度，所有气泡左边对齐在它后面


def orb(cx, cy, r, uid, animated=True):
    """AI 分身的「脸」：一颗慢慢转的渐变光球。三层色斑各转各的，看着像在呼吸。"""
    cls = lambda i: f' class="spin s{i}"' if animated else ""  # noqa: E731
    return (
        f'<defs><clipPath id="oc{uid}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>'
        f'<radialGradient id="ob{uid}" cx=".35" cy=".3" r=".9"><stop offset="0" stop-color="#b9c6ff"/>'
        f'<stop offset=".45" stop-color="{G2}"/><stop offset="1" stop-color="{G1}"/></radialGradient>'
        f'<radialGradient id="o1{uid}"><stop offset="0" stop-color="{G3}" stop-opacity=".95"/>'
        f'<stop offset="1" stop-color="{G3}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="o2{uid}"><stop offset="0" stop-color="#ff77c8" stop-opacity=".75"/>'
        f'<stop offset="1" stop-color="#ff77c8" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="o3{uid}"><stop offset="0" stop-color="#fff" stop-opacity=".85"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>'
        f'<g clip-path="url(#oc{uid})"><circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#ob{uid})"/>'
        f'<g{cls(1)} style="transform-origin:{cx}px {cy}px"><ellipse cx="{cx - r * .35}" cy="{cy + r * .3}" '
        f'rx="{r * .8}" ry="{r * .55}" fill="url(#o1{uid})"/></g>'
        f'<g{cls(2)} style="transform-origin:{cx}px {cy}px"><ellipse cx="{cx + r * .4}" cy="{cy + r * .2}" '
        f'rx="{r * .7}" ry="{r * .5}" fill="url(#o2{uid})"/></g>'
        f'<g{cls(3)} style="transform-origin:{cx}px {cy}px"><ellipse cx="{cx - r * .2}" cy="{cy - r * .45}" '
        f'rx="{r * .55}" ry="{r * .3}" fill="url(#o3{uid})"/></g></g>'
    )


ORB_CSS = (
    ".spin{animation:spin 14s linear infinite}.s2{animation-duration:19s;animation-direction:reverse}"
    ".s3{animation-duration:23s}@keyframes spin{to{transform:rotate(360deg)}}"
)
BASE_CSS = f"text{{font-family:{B.SANS}}}.mono{{font-family:{B.MONO}}}"


def hero(t):
    W, H = 840, 290
    cx, cy, r = W / 2, 118, 70
    body = (
        f'<defs><radialGradient id="halo"><stop offset=".55" stop-color="{G2}" stop-opacity="{t["glow"]}"/>'
        f'<stop offset="1" stop-color="{G2}" stop-opacity="0"/></radialGradient></defs>'
        f'<circle class="breath" cx="{cx}" cy="{cy}" r="{r * 1.75}" fill="url(#halo)" style="transform-origin:{cx}px {cy}px"/>'
        + orb(cx, cy, r, "h")
        + f'<text x="{cx}" y="{cy + r + 50}" font-size="26" font-weight="700" fill="{t["text"]}" text-anchor="middle">decli 的 AI 分身</text>'
        f'<circle class="pulse" cx="{cx - 118}" cy="{cy + r + 78}" r="4" fill="{t["live"]}"/>'
        f'<text x="{cx - 106}" y="{cy + r + 83}" font-size="15" fill="{t["meta"]}">在线 · 他在忙的时候，我替他聊</text>'
    )
    css = BASE_CSS + ORB_CSS + (
        ".breath{animation:breath 5s ease-in-out infinite}@keyframes breath{50%{transform:scale(1.08);opacity:.7}}"
        ".pulse{animation:pulse 2.4s ease-in-out infinite}@keyframes pulse{50%{opacity:.25}}"
    )
    return kit.svg(W, H, "decli 的 AI 分身，在线", body, css)


def bubble(t, text, typing=False, extra_h=0, extra="", width=None):
    """AI 分身的一条消息：左边一颗小光球，右边气泡。extra 是气泡里文字下面的附加内容。"""
    paras = text.split("\n")
    lines = []
    for p in paras:
        lines += B.wrap(p, FS, MAXW) or [""]
    tw_ = max(B.tw(ln, FS) for ln in lines)
    bw = max(width or 0, tw_ + 36)
    bh = 16 + len(lines) * LH + 8 + extra_h
    W, H = AV + bw + 2, bh + 2
    # 气泡：左下角收成小圆角，指向头像
    x0, y0, rr = AV, 1, 20
    path = (
        f"M{x0 + rr} {y0} H{x0 + bw - rr} Q{x0 + bw} {y0} {x0 + bw} {y0 + rr} V{y0 + bh - rr} "
        f"Q{x0 + bw} {y0 + bh} {x0 + bw - rr} {y0 + bh} H{x0 + 5} Q{x0} {y0 + bh} {x0} {y0 + bh - 5} "
        f"V{y0 + rr} Q{x0} {y0} {x0 + rr} {y0} Z"
    )
    msg = (
        f'<path d="{path}" fill="{t["bubble"]}"/>'
        + "".join(
            f'<text x="{x0 + 18}" y="{y0 + 16 + (i + 1) * LH - 7}" font-size="{FS}" fill="{t["text"]}">{B.e(ln)}</text>'
            for i, ln in enumerate(lines)
        )
        + extra
    )
    body = orb(18, H - 18, 16, "a", animated=False)
    css = BASE_CSS
    if typing:  # 开场那句：先「正在输入」一秒多，再冒出来
        dots = "".join(
            f'<circle class="dot d{i}" cx="{x0 + 22 + i * 12}" cy="{H - 22}" r="3.5" fill="{t["meta"]}"/>' for i in range(3)
        )
        body += (
            f'<g class="typing"><rect x="{x0}" y="{H - 44}" width="64" height="42" rx="20" fill="{t["bubble"]}"/>{dots}</g>'
            f'<g class="msg">{msg}</g>'
        )
        css += (
            ".typing{opacity:0;animation:typ 1.7s linear both}@keyframes typ{0%,88%{opacity:1}100%{opacity:0}}"
            ".dot{animation:bounce .9s ease-in-out infinite}.d1{animation-delay:.15s}.d2{animation-delay:.3s}"
            "@keyframes bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-5px)}}"
            ".msg{animation:msg .45s cubic-bezier(.2,.8,.3,1) 1.55s both}"
            "@keyframes msg{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
        )
    else:
        body += msg
    return kit.svg(W, H, text, body, css), W, lines


def chip(text):
    """访客这一侧：一颗渐变的气泡按钮。两套主题共用，白字压饱和色。"""
    w = B.tw(text, 15, True) + 40
    W, H = w + 2, 46
    body = (
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{G1}"/>'
        f'<stop offset="1" stop-color="{G2}"/></linearGradient></defs>'
        f'<rect x="1" y="3" width="{w}" height="40" rx="20" fill="url(#g)"/>'
        f'<text x="{1 + w / 2}" y="28" font-size="15" font-weight="600" fill="#fff" text-anchor="middle">{B.e(text)}</text>'
    )
    return kit.svg(W, H, text, body, BASE_CSS), W


def mini_card(t, w):
    """回答里附带的作品卡片，每张单独是一个链接。"""
    W, H = 300, 88
    live = w.get("href")
    body = (
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{t["card"]}" stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>'
        + B.icon(w, 16, 20, 48, dict(B.THEMES["light" if t is T["light"] else "dark"]))
        + f'<text x="78" y="40" font-size="15.5" font-weight="700" fill="{t["text"]}">{B.e(w["name"])}</text>'
    )
    brief = B.wrap(w["brief"], 12.5, W - 94, max_lines=2)
    body += "".join(f'<text x="78" y="{60 + i * 17}" font-size="12.5" fill="{t["text2"]}">{B.e(s)}</text>' for i, s in enumerate(brief))
    if live:
        bx = 78 + B.tw(w["name"], 15.5, True) + 8
        if bx + 40 < W - 10:
            body += (f'<circle class="pulse" cx="{bx + 5}" cy="35" r="3.5" fill="{t["live"]}"/>'
                     f'<text x="{bx + 13}" y="40" font-size="12" font-weight="700" fill="{t["live"]}">在线</text>')
    css = BASE_CSS + ".pulse{animation:pulse 2.4s ease-in-out infinite}@keyframes pulse{50%{opacity:.25}}"
    return kit.svg(W, H, f"{w['name']} —— {w['brief']}", body, css)


def pipeline_extra(t, x0, y0, width):
    """「来个真实的例子」那条回答里的小流水线，数字来自 codeless 的 POC 实测。"""
    steps = [("需求", "做一个咖啡店单页官网"), ("写代码", "断网沙箱，13 次模型调用"),
             ("跑测试", "验收测试一轮全绿"), ("上线", "CI 部署，点开就能访问")]
    out = [f'<rect x="{x0}" y="{y0}" width="{width}" height="{len(steps) * 34 + 44}" rx="14" fill="{t["card"]}" '
           f'stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>']
    nx = x0 + 22
    out.append(f'<line x1="{nx}" y1="{y0 + 24}" x2="{nx}" y2="{y0 + 24 + (len(steps) - 1) * 34}" stroke="{t["meta"]}" stroke-opacity=".4" stroke-width="2"/>')
    for i, (a, b) in enumerate(steps):
        y = y0 + 24 + i * 34
        c = t["live"] if i == len(steps) - 1 else G1
        out.append(
            f'<circle cx="{nx}" cy="{y}" r="6" fill="{t["card"]}" stroke="{c}" stroke-width="2"/><circle cx="{nx}" cy="{y}" r="2.8" fill="{c}"/>'
            f'<text x="{nx + 18}" y="{y + 5}" font-size="14" font-weight="700" fill="{t["text"]}">{a}</text>'
            f'<text x="{x0 + width - 16}" y="{y + 5}" font-size="13" fill="{t["meta"]}" text-anchor="end">{b}</text>'
        )
    out.append(f'<text x="{nx - 6}" y="{y0 + len(steps) * 34 + 30}" font-size="12.5" fill="{t["meta"]}">单次成本 '
               f'<tspan font-weight="700" fill="{t["text"]}">{B.POC["cost"]}</tspan> · POC 实测</text>')
    return "".join(out), len(steps) * 34 + 44 + 10


def composer(t):
    """最底下的输入框。它不是真的输入框 —— 整张图是一个链接，点了开一个预填好的 issue。"""
    W, H = 840, 64
    body = (
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="31" fill="{t["field"]}" stroke="{t["line"]}" stroke-opacity="{t["line_op"] * 1.6}"/>'
        f'<text x="30" y="38" font-size="16" fill="{t["meta"]}">问点树上没有的？在这里说一句话…</text>'
        f'<rect class="caret" x="285" y="21" width="2" height="22" fill="{G2}"/>'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{G1}"/>'
        f'<stop offset="1" stop-color="{G2}"/></linearGradient></defs>'
        f'<circle cx="{W - 33}" cy="32" r="22" fill="url(#g)"/>'
        f'<path d="M{W - 33} 42 V23 M{W - 41} 30 l8 -8 8 8" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    css = BASE_CSS + ".caret{animation:caret 1.1s steps(1) infinite}@keyframes caret{50%{opacity:0}}"
    return kit.svg(W, H, "问 decli 的 AI 分身：点这里开一个 issue，AI 会在 issue 里回你", body, css)


# ═══════════════════════════════════════════════════════════════════
#  对话树
# ═══════════════════════════════════════════════════════════════════

OPENING = "你好，我是 decli 的 AI 分身。\n他这两年做了十五个作品，一行代码没写 —— 代码都是 AI 写的，也包括我。想从哪儿聊起？"

# (按钮文字, [回答里的一段段内容], [子问题])
# 回答内容：("say", 文字) 一条消息 / ("works", [slug…]) 一排作品卡 / ("pipeline", 文字) 带流水线的消息 / ("table",) 全部作品表
TREE = [
    ("一行代码没写？那他做什么？", [
        ("say", "他只做三件事：提出问题、选择方案、验收结果。\n从界面设计到每一行代码，都交给 AI。用他的话说：人出判断，AI 出产能。"),
    ], [
        ("来个真实的例子", [
            ("pipeline", "拿 codeless 说吧，它本身就是干这个的：你说一句话，它在断网的沙箱里写代码、跑测试、修 bug，再由 CI 部署上线。这是一次实测："),
            ("works", ["codeless"]),
        ], []),
        ("AI 写的靠谱吗？", [
            ("say", "不全靠谱，所以才要验收。\ncodeless 的实测里就抓到过一次：AI 为了让检查变绿，偷偷新建了一个配置文件，把规则改了。"
                    "\n后来他把验证挪到了 AI 碰不到的地方 —— 报告状态的和做验证的，必须是两个主体。"),
        ], []),
    ]),
    ("有能直接玩的吗？", [
        ("say", "有四个，点开就能用："),
        ("works", ["ftms", "ems", "logicc", "wxformat3"]),
    ], []),
    ("给家里人做过什么？", [
        ("say", "三个。给幼儿园大班孩子的思维小画本，给家里老人的取件码助手，还有给老爸的象棋 —— 按 14 寸平板放大过，字大、子大。"),
        ("works", ["logicc", "codehelper", "chinesechess"]),
    ], []),
    ("全部作品列一下", [
        ("say", "一共十五个："),
        ("table",),
    ], []),
]


class Gen:
    def __init__(self, pre):
        self.pre, self.n = pre, 0
        self.assets = HERE / "assets"
        self.assets.mkdir(parents=True, exist_ok=True)

    def themed(self, name, make):
        """make(t) → (svg, width)；写出明暗两份，返回 <picture> 标签。"""
        w = None
        for mode, t in T.items():
            s, w = make(t)
            (self.assets / f"{name}-{mode}.svg").write_text(s)
        return w

    def pic(self, name, alt, width, href=None):
        return kit.picture(self.pre, name, alt, width, href)

    def say(self, text, typing=False, extra=None):
        self.n += 1
        name = f"msg-{self.n:02d}"

        def make(t):
            if extra:
                ex, eh = extra(t, AV + 18, 16 + len(B.wrap(text, FS, MAXW)) * LH + 8, MAXW)
                s, w, _ = bubble(t, text, extra=ex, extra_h=eh, width=MAXW + 36)
            else:
                s, w, _ = bubble(t, text, typing=typing)
            return s, w
        w = self.themed(name, make)
        return self.pic(name, text, w)

    def chip(self, text, slug):
        name = f"chip-{slug}"
        s, w = chip(text)
        (self.assets / f"{name}.svg").write_text(s)
        return f'<img src="{self.pre}{name}.svg" width="{w}" alt="{B.e(text)}" align="top">'

    def works(self, slugs):
        cards = []
        for s in slugs:
            w = kit.work(s)
            self.themed(f"card-{s}", lambda t, w=w: (mini_card(t, w), 300))
            cards.append(self.pic(f"card-{s}", f"{w['name']} —— {w['brief']}", 300, B.link_of(w)))
        # 两张一行，每行前面垫一块头像宽的空白，卡片才跟气泡左边对齐
        pad = f'<img src="{self.pre}spacer.svg" width="{AV}" height="1" alt="">'
        return "<br>\n".join(pad + " ".join(cards[i:i + 2]) for i in range(0, len(cards), 2))

    def answer(self, parts):
        out = []
        for p in parts:
            if p[0] == "say":
                out.append(self.say(p[1]))
            elif p[0] == "pipeline":
                out.append(self.say(p[1], extra=pipeline_extra))
            elif p[0] == "works":
                out.append(self.works(p[1]))
            elif p[0] == "table":
                out += ["", B.works_table(), ""]
        return out

    def node(self, text, parts, children, path):
        slug = "-".join(str(i) for i in path)
        md = ['<div align="right">', "<details>", f"<summary>{self.chip(text, slug)}</summary>", "", '<div align="left">', ""]
        for line in self.answer(parts):
            md.append(line)
            md.append("")
        md.append("</div>")
        for i, (ct, cp, cc) in enumerate(children):
            md += ["", *self.node(ct, cp, cc, path + [i + 1])]
        md += ["", "</details>", "</div>"]
        return md


def render(home=False):
    pre = "styles/chat/assets/" if home else "assets/"
    g = Gen(pre)
    for f in g.assets.glob("*.svg"):
        f.unlink()
    (g.assets / "spacer.svg").write_text(kit.svg(AV, 1, "", ""))
    g.themed("hero", lambda t: (hero(t), 840))
    md = [B.GENERATED.replace("build.py", "styles/chat/chat.py"), ""]
    md.append(f'<p align="center">{kit.picture(pre, "hero", "decli 的 AI 分身，在线", "100%")}</p>')
    md += ["", g.say(OPENING, typing=True), ""]
    for i, (text, parts, children) in enumerate(TREE):
        md += g.node(text, parts, children, [i + 1]) + [""]
    g.themed("composer", lambda t: (composer(t), 840))
    q = urllib.parse.urlencode({"title": ASK_TITLE, "body": ASK_BODY, "labels": "ai-twin"})
    md += ["", kit.picture(pre, "composer", "问 decli 的 AI 分身：点这里开一个 issue", "100%", f"{kit.REPO}/issues/new?{q}"), ""]
    md += ['<p align="center"><sub>点上面的问题，回答立刻展开 · 最下面的输入框会开一个 issue，AI 分身在 issue 里回你，decli 本人也会看到</sub></p>', ""]
    out = kit.ROOT / "README.md" if home else HERE / "README.md"
    out.write_text("\n".join(md))


if __name__ == "__main__":
    render("--home" in sys.argv)
