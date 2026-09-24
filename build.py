#!/usr/bin/env python3
"""
decli 的 GitHub 个人主页 —— 生成器。

    python3 build.py              三套全部重新生成
    python3 build.py aurora       只生成其中一套（aurora / terminal / bento）

生成到哪：HOME_STYLE 指定的那一套生成到仓库根目录（README.md + assets/），
那就是个人主页上显示的；另外两套生成到 styles/<名字>/ 备用。
想换风格，改 HOME_STYLE 再跑一次就行。

加一个作品：只改下面的 WORKS。卡片、表格、首屏数字全跟着数据走。
只用标准库，不装任何东西。

── 为什么是生成出来的 SVG，而不是手写 HTML ──
GitHub 渲染 README 时会剥掉 <style>、class、style 属性和所有脚本，能留下来的
只有图片和少数几个标签。但 SVG 当图片用的时候，它内部的 CSS 动画照样跑 ——
所以「极光在飘、风线在走、在线的小绿点在呼吸」只能画进 SVG 里。
代价是图里的字读屏读不到、手机上会跟着整张图缩小：所以每张图都带 alt，
真正要读的东西（作品清单、链接）一律写成 Markdown 文本，不画进图里。

── 明暗两套 ──
GitHub 支持 <picture><source media="(prefers-color-scheme: dark)">，
跟着用户在 GitHub 上选的主题切换。每张图出 light / dark 两份，
配色直接取自作品集首页的 CSS 变量，两边是同一个人的东西，得一眼认得出来。

── 字体 ──
SVG 当图片加载时拿不到任何外部资源（包括 Google Fonts），只能用看的人
机器上有的字体。所以字宽只能估：中文按 1em，西文按常见无衬线字体的均值。
排版上凡是「接在一段字后面」的东西都留了余量，宁可松一点，不能压字。
"""

import base64
import html
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
HOME_STYLE = "aurora"  # 个人主页用哪一套：aurora / terminal / bento
SITE = "https://decli.github.io"
GH = "https://github.com/decli"

SANS = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', "
    "'Microsoft YaHei', 'Noto Sans SC', 'Noto Sans CJK SC', 'Source Han Sans SC', "
    "'WenQuanYi Zen Hei', Roboto, 'Helvetica Neue', Arial, sans-serif"
)
MONO = (
    "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, 'JetBrains Mono', "
    "'Liberation Mono', 'DejaVu Sans Mono', monospace"
)

# ═══════════════════════════════════════════════════════════════════
#  数据：跟 decli.github.io 的 sites.js 保持一致
# ═══════════════════════════════════════════════════════════════════

CATS = [
    ("web", "在线应用"),
    ("ext", "浏览器扩展"),
    ("script", "用户脚本"),
    ("desktop", "桌面应用"),
    ("app", "移动应用"),
]

# icon：以 @ 开头的借项目自己的图标（src/icons/ 下）；否则取 ICONS 里的线条图形，用 tint 上色。
# tint 同时决定卡片角上那团光晕的颜色。
# desc 给大卡片用（照抄作品集），brief 给小卡片和作品表用（控制在 30 字上下）。
WORKS = [
    dict(
        slug="codeless", cat="web", name="codeless", repo="codeless",
        icon="wand", tint=("#7c3aed", "#06b6d4"),
        desc="说一句话，它在容器里写代码、跑测试、改 bug，再由 CI 部署成一个能打开的网站。"
             "全程不用碰 IDE，做完接着说「换成卡片风格」就能改。",
        brief="说一句话，它写代码、跑测试、改 bug，再部署成能打开的网站。",
        tags=["AI Agent", "自托管", "Docker + CI"],
    ),
    dict(
        slug="ftms", cat="web", name="信风 Tradewind", repo="ftms", href=f"{SITE}/ftms/",
        icon="@ftms.svg", tint=("#3b5bd6", "#7f9bff"),
        desc="外贸业务全流程管理系统。询盘、报价、PI、采购生产、出运跟单、收汇、退税，一个 PI 号串到底。",
        brief="外贸全流程管理，从询盘到退税，一个 PI 号串到底。",
        tags=["外贸管理", "跟单", "出口退税", "33 个模块"],
    ),
    dict(
        slug="ems", cat="web", name="EMS 外贸营销系统", repo="ems", href=f"{SITE}/ems/",
        icon="@ems.svg", tint=("#3b82f6", "#4f46e5"),
        desc="AI Agent 驱动的外贸全链路增长系统 —— 从「找到买家」到「收到货款」跑在同一套数据上。",
        brief="AI Agent 驱动的外贸增长，从找到买家到收到货款。",
        tags=["获客", "AI Agent", "外贸营销"],
    ),
    dict(
        slug="logicc", cat="web", name="思维小画本", repo="logicc", href=f"{SITE}/logicc/",
        icon="@logicc.png", tint=("#f59e0b", "#3b82f6"), who="给幼儿园大班的孩子",
        desc="给幼儿园大班孩子的思维训练游戏。把做不下去的纸质练习册改成十二个平板游戏，全程语音读题，不识字也能自己玩。",
        brief="把做不下去的纸质练习册，改成十二个会读题的平板游戏。",
        tags=["幼儿", "思维训练", "12 个游戏", "语音读题"],
    ),
    dict(
        slug="wxformat3", cat="web", name="WxMark", repo="wxformat3", href=f"{SITE}/wxformat3/",
        icon="@wxformat3.svg", tint=("#667eea", "#764ba2"),
        desc="微信公众号 Markdown 排版工具。左边写、右边预览，一键复制成带内联样式的 HTML 直接粘进后台。",
        brief="公众号 Markdown 排版，一键复制成能直接粘贴的 HTML。",
        tags=["公众号", "Markdown", "6 套主题"],
    ),
    dict(
        slug="macpleco", cat="desktop", name="MacPleco", repo="MacPleco",
        dl=f"{GH}/MacPleco/releases/latest",
        icon="@macpleco.png", tint=("#2dd4bf", "#0f766e"),
        desc="Mac 清理工具。删什么都先进废纸篓，风险项一律不替你勾，每一条都写清它到底是什么、在哪个路径 —— 不靠制造焦虑卖清理。",
        brief="不制造焦虑的 Mac 清理工具，删什么都先进废纸篓。",
        tags=["macOS 15+", "Swift 6", "清理 / 监控"],
    ),
    dict(
        slug="ip-geo", cat="ext", name="IP 归属地监控", repo="IP_Geolocation_Extension_Chrome",
        icon="globe", tint=("#0ea5e9", "#2563eb"),
        desc="工具栏徽标直接显示出口国家代码，IPv4 / IPv6 与归属地一眼可见 —— 代理有没有真的生效，不用再开个测试网站去看。",
        brief="工具栏直接显示出口国家，代理有没有生效一眼可见。",
        tags=["Chrome 扩展", "IP", "代理排查"],
    ),
    dict(
        slug="jobornot", cat="ext", name="职得投 JobOrNot", repo="JobOrNot",
        icon="target", tint=("#f59e0b", "#ef4444"),
        desc="浏览 BOSS 直聘 / 猎聘时，把简历和岗位 JD 摆在一起比，诚实回答「值不值得投、怎么投得更好」。",
        brief="把简历和岗位 JD 摆在一起比，诚实回答值不值得投。",
        tags=["求职", "AI 匹配", "扩展"],
    ),
    dict(
        slug="wx-export", cat="ext", name="公众号数据导出", repo="weixin_public_export",
        icon="chat", tint=("#10b981", "#059669"),
        desc="在已登录的公众号后台本地导出近期发表的文章与阅读、点赞、分享数据，拿来做内容复盘和选题分析。",
        brief="在本地导出公众号文章的阅读、点赞、分享数据，拿来复盘选题。",
        tags=["公众号", "数据导出"],
    ),
    dict(
        slug="tabinfocopy", cat="ext", name="TabInfoCopy", repo="TabInfoCopy",
        icon="tab", tint=("#8b5cf6", "#6366f1"),
        desc="一键复制当前标签页的标题和网址，省掉「点地址栏、全选、复制、再回去抄标题」这四步。",
        brief="一键复制当前标签页的标题和网址。",
        tags=["Chrome 扩展", "效率"],
    ),
    dict(
        slug="ip-display", cat="ext", name="IP Display", repo="IPDisplayExtension",
        icon="globe", tint=("#64748b", "#475569"),
        desc="显示当前 IP 与国内外归属地。IP 归属地监控的前身，留着做个记录。",
        brief="显示当前 IP 与归属地。IP 归属地监控的前身，留着做个记录。",
        tags=["Chrome 扩展", "早期版本"],
    ),
    dict(
        slug="pagescroll", cat="script", name="PageScroll", repo="pagescroll",
        icon="scroll", tint=("#06b6d4", "#0891b2"),
        desc="任意网页上一个可拖动的悬浮胶囊，一点回顶或到底。用 Shadow DOM 隔离样式，SPA 重渲染后它会自己回来。",
        brief="任意网页上一个可拖动的悬浮胶囊，一点回顶或到底。",
        tags=["油猴脚本", "Shadow DOM"],
    ),
    dict(
        slug="bing-wallpaper", cat="script", name="Bing 壁纸批量下载", repo="BingWDByte4KBatchDownloader",
        icon="download", tint=("#ec4899", "#db2777"),
        desc="在壁纸列表页勾选多张，一次把 4K / UHD 原图批量下到指定目录，不用一张张点进去另存为。",
        brief="勾选多张壁纸，一次批量下载 4K 原图。",
        tags=["油猴脚本", "批量下载"],
    ),
    dict(
        slug="codehelper", cat="app", name="取件码助手", repo="CodeHelper",
        icon="package", tint=("#f97316", "#ea580c"), who="给家里老人",
        desc="给家里老人做的 Android 应用。自动从短信里挑出还没取的取件码，用取件小票的样子大字号摆出来，到驿站直接给人看。",
        brief="从短信里挑出还没取的取件码，像取件小票一样大字摆出来。",
        tags=["Android", "适老化", "短信解析"],
    ),
    dict(
        slug="chinesechess", cat="app", name="老爸下象棋", repo="chinesechess03",
        icon="chess", tint=("#a16207", "#854d0e"), who="给老爸",
        desc="Android 平板上的中国象棋，按 14 寸横屏放大过布局，三档 AI，落子有音效和语音播报。",
        brief="按 14 寸平板放大布局的中国象棋，三档 AI，落子有语音播报。",
        tags=["Android", "象棋", "大屏"],
    ),
]

# 首页上几句话 —— 跟作品集首屏同一套说法，别各说各的
HEADLINE = ("{n}个作品，", "一行代码没写")
LEDE = [
    "从 UI 交互设计到每一行代码编写，全部由 AI 完成。",
    "我只做三件事：提出问题、选择方案、验收结果 —— 人出判断，AI 出产能。",
    "不是尝鲜，这是 AI Native 时代工作新范式。",
]
STEPS = [  # 「我只做三件事」
    ("提出问题", "想清楚它替谁解决什么", "ask"),
    ("选择方案", "在 AI 给的几条路里拍板", "fork"),
    ("验收结果", "测过、用过，才算做完", "check"),
]
AI_DOES = ["UI 交互设计", "写代码", "跑测试", "修 bug", "部署上线"]

# codeless 的流水线 —— 数字全部来自 codeless 仓库 docs/06-poc-findings.md 的实测，不是示意
# https://github.com/decli/codeless/blob/main/docs/06-poc-findings.md
POC = dict(
    task="做一个咖啡店单页官网",
    steps=[
        ("需求", "做一个咖啡店单页官网"),
        ("写代码", "断网沙箱 · 13 次模型调用"),
        ("跑测试", "验收测试一轮全绿"),
        ("CI 部署", "推送即构建"),
        ("上线", "点开链接就能访问"),
    ],
    cost="$0.0127",
    runs=[  # 终端风格里 tail 出来的那三行
        ("咖啡店单页官网", "static-site", "13 次调用", "$0.0127", "全绿 → CI → 已上线"),
        ("个人博客", "static-site", "17 次调用", "$0.0208", "全绿"),
        ("CSV 转 JSON", "python-cli", " 8 次调用", "$0.0034", "全绿 → CI → 制品已发布"),
    ],
)

# 「我相信的几件事」—— 从作品集 README 里的原话提炼，口吻保持一致
PRINCIPLES = [
    ("人出判断，AI 出产能。",
     "我只做三件事：提出问题、选择方案、验收结果。剩下的，从 UI 交互设计到每一行代码，全部交给 AI。"),
    ("不摆示意图。",
     "作品集里的每一张截图都来自项目本身。拿不出真图的，宁可不放预览，也不摆一张摆拍出来的示意图。"),
    ("一页只做一件事。",
     "作品集首页曾经加过戳泡泡和连连看，后来都拿掉了 —— 入口页多一个玩意儿，主线就模糊一分。"),
]

# 线条图形：跟作品集首页同一套（24×24，白色描边，底色用 tint）。
# 不用 emoji —— emoji 在 Windows / Mac / Android 上长得完全不一样，一排摆开必然花。
ICONS = {
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18a15 15 0 0 1 0-18"/>',
    "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    "chat": '<path d="M21 12a8 8 0 0 1-8 8H7l-4 3v-6.5A8 8 0 0 1 13 4a8 8 0 0 1 8 8Z"/><path d="M9 11h.01M13 11h.01M17 11h.01"/>',
    "tab": '<rect x="3" y="5" width="18" height="15" rx="2.5"/><path d="M3 9.5h7l1.6-2.4H21"/>',
    "scroll": '<path d="M12 4v16"/><path d="m7 9 5-5 5 5"/><path d="m7 15 5 5 5-5"/>',
    "download": '<path d="M12 3v12"/><path d="m7.5 11 4.5 4.5 4.5-4.5"/><path d="M4 20h16"/>',
    "package": '<path d="m12 3 8 4.2v9.6L12 21l-8-4.2V7.2Z"/><path d="M4.3 7.3 12 11.4l7.7-4.1M12 11.4V21"/>',
    "chess": '<path d="M9 4h6v2.6l2 2.4H7l2-2.4Z"/><path d="M8.4 9h7.2l-.9 6H9.3Z"/><path d="M6.5 20h11l-.8-2.6H7.3Z"/>',
    "wand": '<path d="m4 20 8.4-8.4"/><path d="m16 3.4 1.5 3.5 3.5 1.5-3.5 1.5L16 13.4l-1.5-3.5L11 8.4l3.5-1.5Z"/><path d="M6.4 5.2v3.2M4.8 6.8h3.2"/>',
    # 下面三个只给「我只做三件事」用
    "ask": '<path d="M21 12a8 8 0 0 1-8 8H7l-4 3v-6.5A8 8 0 0 1 13 4a8 8 0 0 1 8 8Z"/><path d="M10.6 9.6a2.4 2.4 0 1 1 3.4 2.2c-.7.3-1 .8-1 1.5M13 16h.01"/>',
    "fork": '<circle cx="6" cy="5" r="2"/><circle cx="18" cy="5" r="2"/><circle cx="12" cy="19" r="2"/><path d="M6 7v2a3 3 0 0 0 3 3h6a3 3 0 0 0 3-3V7M12 12v5"/>',
    "check": '<path d="M12 3 4.5 6v5.5c0 4.6 3.2 8.2 7.5 9.5 4.3-1.3 7.5-4.9 7.5-9.5V6Z"/><path d="m8.6 12 2.4 2.4 4.4-4.6"/>',
}

# 配色：直接取自作品集首页 index.html 的 CSS 变量（亮 / 暗两套）
THEMES = {
    "light": dict(
        bg="#f5f7fc", panel="#ffffff", line="#122044", line_op=0.10, line2_op=0.18,
        text="#101828", text2="#4a566d", text3="#7b879e",
        brand="#3b5bd6", brand2="#7c5cff", brand3="#06b6d4", live="#0f9d58",
        aurora=(0.20, 0.15, 0.15), wind="#3b5bd6", wind_op=0.11,
        chip="#122044", chip_op=0.055, glow_op=0.13, shadow_op=0.10,
    ),
    "dark": dict(
        bg="#060a18", panel="#0c1328", line="#96b2f0", line_op=0.14, line2_op=0.26,
        text="#eaf0ff", text2="#a6b3d2", text3="#78849f",
        brand="#7c9bff", brand2="#a78bfa", brand3="#22d3ee", live="#34d399",
        aurora=(0.32, 0.20, 0.26), wind="#8fa9ff", wind_op=0.14,
        chip="#96b2f0", chip_op=0.09, glow_op=0.22, shadow_op=0.5,
    ),
}
AURORA_COLORS = ("#7c5cff", "#06b6d4", "#3b5bd6")
# 上面压白字的实心色块（按钮、头像、AI 标签、作品集入口）两套主题都用亮色主题那组饱和色：
# 暗色主题的 brand 偏浅，白字压上去对比度不到 3:1
SOLID = (THEMES["light"]["brand"], THEMES["light"]["brand2"], THEMES["light"]["brand3"])
CAT_COLORS = {"web": "brand", "ext": "brand2", "script": "brand3", "desktop": "#f59e0b", "app": "#ec4899"}


# ═══════════════════════════════════════════════════════════════════
#  小工具
# ═══════════════════════════════════════════════════════════════════

def e(s):
    return html.escape(str(s), quote=True)


def cn(n):
    """15 → 十五。首屏那句「十五个作品」跟着作品数走，加一个就自动变十六。"""
    d = "零一二三四五六七八九"
    if n < 10:
        return d[n]
    if n < 100:
        return (d[n // 10] if n >= 20 else "") + "十" + (d[n % 10] if n % 10 else "")
    return str(n)


WIDE = set("，。、；：！？「」『』（）《》【】—…“”‘’")
NARROW = set("iljI.,:;|!'`·")
SEMI = set("frt()[]{}-/\\")
SYMBOL = set("↗→←↑↓✓●❯")


def tw(s, size, bold=False, mono=False):
    """估字宽。中文 1em；西文按常见无衬线字体的均值；等宽按 0.6em。"""
    em = 0.0
    for ch in s:
        if ord(ch) >= 0x2E80 or ch in WIDE:
            em += 1.0
        elif mono:
            em += 0.6
        elif ch in SYMBOL:
            em += 0.9
        elif ch == " " or ch in NARROW:
            em += 0.28
        elif ch in SEMI:
            em += 0.36
        elif ch in "mwMW@%":
            em += 0.86
        elif ch.isupper():
            em += 0.66
        elif ch.isdigit():
            em += 0.58
        else:
            em += 0.54
    return em * size * (1.05 if bold else 1.0)


TOKEN = re.compile(r"[A-Za-z0-9$%+#@&/_.'’-]+|\s+|.")
NO_LINE_START = set("，。、；：！？）」』》”’,.;:!?)%")
NO_LINE_END = set("「『（《“‘(")


def wrap(text, size, width, bold=False, max_lines=None):
    """中文逐字可断、西文按词断；句读不许落到行首（挂在上一行末尾，宁可略出界），
    开引号不许留在行尾（跟着下一个字一起换行）。"""
    lines, cur = [], ""
    for tok in TOKEN.findall(text):
        if cur and not tok.isspace() and tok not in NO_LINE_START and tw(cur + tok, size, bold) > width:
            carry = ""
            while cur and cur[-1] in NO_LINE_END:
                carry, cur = cur[-1] + carry, cur[:-1]
            lines.append(cur.rstrip())
            cur = carry + tok
        elif cur or not tok.isspace():
            cur += tok
    if cur.strip():
        lines.append(cur.rstrip())
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and tw(last + "…", size, bold) > width:
            last = last[:-1]
        lines[-1] = last.rstrip("，、；：。 ") + "…"
    return lines


def data_uri(path):
    mime = "image/svg+xml" if path.suffix == ".svg" else "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def color(t, c):
    """CAT_COLORS 里既有主题色的名字，也有写死的色值。"""
    return t[c] if c in t else c


BASE_CSS = (
    "text{font-family:%s}.mono{font-family:%s}"
    ".pulse{animation:pulse 2.4s ease-in-out infinite}"
    "@keyframes pulse{50%%{opacity:.25}}"
) % (SANS, MONO)
REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def svg_doc(w, h, title, body, css=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="title">\n'
        f"<title id=\"title\">{e(title)}</title>\n"
        f"<style>{BASE_CSS}{css}{REDUCED}</style>\n"
        f"{body}\n</svg>\n"
    )


def icon(w, x, y, size, t, uid=""):
    """作品图标：有自己 favicon 的借它的，没有的用线条图形 + tint。"""
    rx = round(size * 0.29, 1)
    ic = w["icon"]
    if ic.startswith("@"):
        f = ROOT / "src" / "icons" / ic[1:]
        img = f'<image x="{x}" y="{y}" width="{size}" height="{size}" href="{data_uri(f)}"'
        if f.suffix == ".svg":  # favicon 自带圆角底色，原样摆上
            return img + "/>"
        cid = f"ic-{w['slug']}{uid}"
        return (
            f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{rx}"/></clipPath>'
            f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{rx}" fill="{t["panel"]}"/>'
            f'{img} clip-path="url(#{cid})"/>'
            f'<rect x="{x + .5}" y="{y + .5}" width="{size - 1}" height="{size - 1}" rx="{rx}" fill="none" '
            f'stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>'
        )
    gid = f"tint-{w['slug']}{uid}"
    a, b = w["tint"]
    k = size * 0.54 / 24
    off = size * 0.23
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>'
        f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{rx}" fill="url(#{gid})"/>'
        f'<g transform="translate({x + off:.1f} {y + off:.1f}) scale({k:.3f})" fill="none" stroke="#fff" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[ic]}</g>'
    )


def line_icon(name, x, y, size, stroke, width=1.8):
    k = size / 24
    return (
        f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.3f})" fill="none" stroke="{stroke}" '
        f'stroke-width="{width / k:.2f}" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>'
    )


def live_badge(x, cy, t, fs=11):
    """跟作品集卡片上那个「● 在线」同一个样子，小绿点会呼吸。"""
    w = 17 + tw("在线", fs, True) + 8
    return (
        f'<rect x="{x:.1f}" y="{cy - 10}" width="{w:.1f}" height="20" rx="10" fill="none" '
        f'stroke="{t["live"]}" stroke-opacity=".45"/>'
        f'<circle class="pulse" cx="{x + 9.5:.1f}" cy="{cy}" r="2.6" fill="{t["live"]}"/>'
        f'<text x="{x + 16:.1f}" y="{cy + fs * 0.36:.1f}" font-size="{fs}" font-weight="700" '
        f'fill="{t["live"]}">在线</text>'
    ), w


def chips(tags, x, y, t, fs=11.5, h=22, gap=6, maxw=None):
    out, cx = [], x
    for tag in tags:
        w = tw(tag, fs) + 16
        if maxw and cx + w - x > maxw:
            break
        out.append(
            f'<rect x="{cx:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="6" fill="{t["chip"]}" '
            f'fill-opacity="{t["chip_op"]}"/>'
            f'<text x="{cx + 8:.1f}" y="{y + h / 2 + fs * 0.36:.1f}" font-size="{fs}" fill="{t["text2"]}">{e(tag)}</text>'
        )
        cx += w + gap
    return "".join(out)


def text_lines(lines, x, y, lh, fs, fill, extra=""):
    return "".join(
        f'<text x="{x}" y="{y + i * lh:.1f}" font-size="{fs}" fill="{fill}"{extra}>{e(s)}</text>'
        for i, s in enumerate(lines)
    )


def radial(gid, c, op):
    return (
        f'<radialGradient id="{gid}"><stop offset="0" stop-color="{c}" stop-opacity="{op}"/>'
        f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
    )


def brand_gradient(gid, t, x1, x2, y=0):
    """标题那道渐变：brand → brand-2 → brand-3，跟作品集 h1 .g 同一个"""
    return (
        f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1:.1f}" y1="{y}" x2="{x2:.1f}" y2="{y}">'
        f'<stop offset="0" stop-color="{t["brand"]}"/><stop offset=".55" stop-color="{t["brand2"]}"/>'
        f'<stop offset="1" stop-color="{t["brand3"]}"/></linearGradient>'
    )


# ── 极光背景：三团色斑慢慢漂 + 几条常年不改向的风线 ──
# 跟作品集首页同一个手法。透明度比网页上高一点：网页上它铺满整屏，
# 放进一张横幅里面积小得多，压到网页那么淡就等于没有。
AURORA_CSS = (
    ".b1{animation:f1 40s ease-in-out infinite}"
    ".b2{animation:f2 52s ease-in-out -14s infinite}"
    ".b3{animation:f3 46s ease-in-out -26s infinite}"
    "@keyframes f1{33%{transform:translate(48px,-36px)}66%{transform:translate(-60px,30px)}}"
    "@keyframes f2{33%{transform:translate(-40px,34px)}66%{transform:translate(56px,-20px)}}"
    "@keyframes f3{33%{transform:translate(36px,28px)}66%{transform:translate(-52px,-34px)}}"
    ".wind path{fill:none;stroke-linecap:round;stroke-dasharray:180 1400;animation:drift 26s linear infinite}"
    ".wind path:nth-child(2){animation-duration:34s;animation-delay:-6s}"
    ".wind path:nth-child(3){animation-duration:29s;animation-delay:-14s}"
    ".wind path:nth-child(4){animation-duration:38s;animation-delay:-3s}"
    ".wind path:nth-child(5){animation-duration:31s;animation-delay:-19s}"
    "@keyframes drift{to{stroke-dashoffset:-1580}}"
)


def wind(W, H, t, rows=(0.16, 0.36, 0.55, 0.73, 0.9), op=None):
    widths = (1.5, 1, 1.8, 1.1, 1.4)
    op = t["wind_op"] if op is None else op
    paths = []
    for i, f in enumerate(rows):
        y = f * H
        paths.append(
            f'<path d="M-40 {y:.0f} C {W * .27:.0f} {y - H * .1:.0f}, {W * .55:.0f} {y + H * .08:.0f}, '
            f'{W + 40} {y - H * .07:.0f}" stroke-width="{widths[i % 5]}"/>'
        )
    return f'<g class="wind" stroke="{t["wind"]}" stroke-opacity="{op}">{"".join(paths)}</g>'


def aurora_panel(W, H, t, rx=28, blobs=None, with_wind=True, fill=None):
    """带极光的底板：圆角、裁切、描边。blobs = [(cx, cy, rx, ry, color, opacity), ...]"""
    a = t["aurora"]
    blobs = blobs or [
        (W * .78, H * .02, W * .42, H * .9, AURORA_COLORS[0], a[0]),
        (W * .06, H * .74, W * .38, H * .8, AURORA_COLORS[1], a[1]),
        (W * .9, H * 1.02, W * .4, H * .72, AURORA_COLORS[2], a[2]),
    ]
    defs = [f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="{rx}"/></clipPath>']
    body = [f'<rect width="{W}" height="{H}" fill="{fill or t["bg"]}"/>']
    for i, (cx, cy, bx, by, c, op) in enumerate(blobs):
        defs.append(radial(f"au{i}", c, op))
        body.append(
            f'<g class="b{i % 3 + 1}"><ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{bx:.0f}" ry="{by:.0f}" '
            f'fill="url(#au{i})"/></g>'
        )
    if with_wind:
        body.append(wind(W, H, t))
    return (
        "<defs>" + "".join(defs) + "</defs>"
        + '<g clip-path="url(#frame)">' + "".join(body) + "</g>"
        + f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{rx - .5}" fill="none" '
          f'stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>'
    )


def stats():
    n = len(WORKS)
    live = sum(1 for w in WORKS if w.get("href"))
    return n, live


# ═══════════════════════════════════════════════════════════════════
#  风格一：极光 Aurora —— 跟作品集首页同源
# ═══════════════════════════════════════════════════════════════════

def aurora_hero(t):
    W, H = 1200, 468
    n, live = stats()
    a, b = HEADLINE[0].format(n=cn(n)), HEADLINE[1]
    fs = 74
    x0 = 72
    wa, wb = tw(a, fs, True), tw(b, fs, True)
    parts = [aurora_panel(W, H, t)]

    # 页眉：头像 + 名字 + 作品集地址，跟网页页眉一样
    parts.append(
        '<defs><linearGradient id="av" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{SOLID[0]}"/><stop offset="1" stop-color="{SOLID[1]}"/></linearGradient>'
        f'<filter id="avs" x="-50%" y="-50%" width="200%" height="200%"><feDropShadow dx="0" dy="6" stdDeviation="7" '
        f'flood-color="{t["brand"]}" flood-opacity=".45"/></filter>'
        + brand_gradient("hl", t, x0 + wa, x0 + wa + wb) + "</defs>"
    )
    parts.append(
        f'<rect x="{x0}" y="56" width="52" height="52" rx="16" fill="url(#av)" filter="url(#avs)"/>'
        f'<text x="{x0 + 26}" y="91" font-size="26" font-weight="700" fill="#fff" text-anchor="middle">d</text>'
        f'<text x="{x0 + 68}" y="90" font-size="22" font-weight="700" fill="{t["text"]}">decli</text>'
        f'<text x="{x0 + 68 + tw("decli", 22, True) + 16:.0f}" y="90" font-size="15" fill="{t["text3"]}">'
        f"AI Architect · San Jose</text>"
    )
    pill = "decli.github.io ↗"
    pw = tw(pill, 15, True) + 32
    px = W - x0 - pw
    parts.append(
        f'<rect x="{px:.0f}" y="63" width="{pw:.0f}" height="38" rx="12" fill="{t["panel"]}" fill-opacity=".55" '
        f'stroke="{t["line"]}" stroke-opacity="{t["line2_op"]}"/>'
        f'<text x="{px + 16:.0f}" y="87" font-size="15" font-weight="600" fill="{t["text2"]}">{e(pill)}</text>'
    )

    # 主标题：前半句正文色，后半句渐变 —— 跟网页 h1 一样
    parts.append(
        f'<text x="{x0}" y="212" font-size="{fs}" font-weight="800" letter-spacing="-1" fill="{t["text"]}">'
        f'{e(a)}<tspan fill="url(#hl)">{e(b)}</tspan></text>'
    )
    parts.append(text_lines(LEDE, x0, 268, 36, 21, t["text2"]))

    # 数字：15 个作品 · 4 个可在线体验 · 0 行手写代码
    parts.append(
        f'<text x="{x0}" y="408" fill="{t["text3"]}" font-size="16">'
        f'<tspan font-size="34" font-weight="700" fill="{t["text"]}">{n}</tspan><tspan dx="8">个作品</tspan>'
        f'<tspan dx="34" font-size="34" font-weight="700" fill="{t["text"]}">{live}</tspan><tspan dx="8">个可在线体验</tspan>'
        f'<tspan dx="34" font-size="34" font-weight="700" fill="{t["brand2"]}">0</tspan><tspan dx="8">行手写代码</tspan>'
        "</text>"
    )
    title = f"decli — {a}{b}。" + "".join(LEDE)
    return svg_doc(W, H, title, "\n".join(parts), AURORA_CSS)


def aurora_card_layout(w, size):
    """算一张卡片需要多高。同一排的卡片取最高那张，排出来才齐。"""
    W = 420 if size == "half" else 276
    fs = 14 if size == "half" else 13.5
    text = w["desc"] if size == "half" else w["brief"]
    lines = wrap(text, fs, W - 40, max_lines=4 if size == "half" else 3)
    y_desc = 100
    y_tags = y_desc + (len(lines) - 1) * 22 + 16
    h = y_tags + 22 + 18 + 30 + 20
    return W, fs, lines, y_desc, y_tags, h


def aurora_card(w, t, size, H):
    W, fs, lines, y_desc, y_tags, _ = aurora_card_layout(w, size)
    a, _b = w["tint"]
    isz = 44 if size == "half" else 40
    parts = [
        '<defs><clipPath id="frame">'
        f'<rect width="{W}" height="{H}" rx="18"/></clipPath>'
        + radial("glow", a, t["glow_op"] * 1.6) + "</defs>",
        '<g clip-path="url(#frame)">'
        f'<rect width="{W}" height="{H}" fill="{t["panel"]}"/>'
        f'<ellipse cx="{W * .1:.0f}" cy="0" rx="{W * .85:.0f}" ry="{H * .9:.0f}" fill="url(#glow)"/></g>',
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" fill="none" '
        f'stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>',
        icon(w, 20, 20, isz, t),
    ]
    nx = 20 + isz + 13
    nfs = 17.5 if size == "half" else 16.5
    parts.append(f'<text x="{nx}" y="{20 + isz * .42:.0f}" font-size="{nfs}" font-weight="700" fill="{t["text"]}">{e(w["name"])}</text>')
    if w.get("href"):
        badge, _ = live_badge(nx + tw(w["name"], nfs, True) + 10, 20 + isz * .42 - nfs * .36, t)
        parts.append(badge)
    kind = w.get("who") if size == "third" and w.get("who") else dict(CATS)[w["cat"]]
    parts.append(f'<text x="{nx}" y="{20 + isz * .42 + 21:.0f}" font-size="12.5" fill="{t["text3"]}">{e(kind)}</text>')
    parts.append(text_lines(lines, 20, y_desc, 22, fs, t["text2"]))
    parts.append(chips(w["tags"], 20, y_tags, t, maxw=W - 40))

    # 底部：主动作 + 地址。整张卡片本身就是链接，这里只是告诉人点下去会去哪
    by = H - 20 - 30
    if w.get("href"):
        label, url = "打开 ↗", w["href"].replace("https://", "").rstrip("/")
    elif w.get("dl"):
        label, url = "下载 ↗", "GitHub Releases"
    else:
        label, url = "源码 ↗", f"github.com/decli/{w['repo']}"
    bw = tw(label, 13, True) + 28
    if w.get("href") or w.get("dl"):
        parts.append(
            f'<defs><linearGradient id="btn" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{SOLID[0]}"/>'
            f'<stop offset="1" stop-color="{SOLID[1]}"/></linearGradient></defs>'
            f'<rect x="20" y="{by}" width="{bw:.0f}" height="30" rx="9" fill="url(#btn)"/>'
            f'<text x="34" y="{by + 19.5}" font-size="13" font-weight="700" fill="#fff">{e(label)}</text>'
        )
    else:
        parts.append(
            f'<rect x="20.5" y="{by + .5}" width="{bw - 1:.0f}" height="29" rx="9" fill="none" '
            f'stroke="{t["line"]}" stroke-opacity="{t["line2_op"]}"/>'
            f'<text x="34" y="{by + 19.5}" font-size="13" font-weight="700" fill="{t["text2"]}">{e(label)}</text>'
        )
    ux = 20 + bw + 12
    if ux + tw(url, 12, mono=True) <= W - 20:
        parts.append(f'<text class="mono" x="{ux:.0f}" y="{by + 19}" font-size="12" fill="{t["text3"]}">{e(url)}</text>')
    title = f"{w['name']} — {w['desc']}"
    return svg_doc(W, H, title, "\n".join(parts))


def aurora_codeless(t):
    """旗舰横幅：左边说它是什么，右边是一次真实跑出来的流水线。"""
    W, H = 1200, 400
    w = next(x for x in WORKS if x["slug"] == "codeless")
    blobs = [
        (W * .95, H * -.05, W * .36, H * .9, w["tint"][0], t["aurora"][0]),
        (W * .08, H * 1.05, W * .36, H * .8, w["tint"][1], t["aurora"][1]),
        (W * .5, H * .3, W * .3, H * .6, AURORA_COLORS[2], t["aurora"][2] * .6),
    ]
    parts = [aurora_panel(W, H, t, blobs=blobs, with_wind=False)]
    parts.append(
        f'<text x="64" y="78" font-size="13" font-weight="700" letter-spacing="2.5" fill="{t["brand"]}">'
        "AI 编码流水线 · 自托管</text>"
    )
    parts.append(icon(w, 64, 102, 60, t, uid="-big"))
    parts.append(f'<text x="144" y="147" font-size="44" font-weight="800" letter-spacing="-.5" fill="{t["text"]}">codeless</text>')
    parts.append(text_lines(wrap(w["desc"], 19, 500), 64, 212, 31, 19, t["text2"]))
    parts.append(chips(w["tags"], 64, 316, t, fs=13, h=28, gap=8))
    parts.append(f'<text class="mono" x="64" y="370" font-size="13" fill="{t["text3"]}">github.com/decli/codeless</text>')

    # 右：流水线面板
    px, py, pw, ph = 640, 48, 512, 304
    parts.append(
        f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="20" fill="{t["panel"]}" fill-opacity=".62" '
        f'stroke="{t["line"]}" stroke-opacity="{t["line2_op"]}"/>'
        f'<text x="{px + 28}" y="{py + 40}" font-size="15" font-weight="700" fill="{t["text"]}">一句话 → 能打开的网站</text>'
        f'<text x="{px + pw - 28}" y="{py + 40}" font-size="12.5" fill="{t["text3"]}" text-anchor="end">POC 实测一次</text>'
    )
    steps = POC["steps"]
    nx = px + 38
    y0, dy = py + 86, 38
    y1 = y0 + dy * (len(steps) - 1)
    # 竖线 + 一颗顺着往下走的光点；每走到一个节点，节点亮起来
    cyc = 8.0
    travel = 62.5  # 光点在前 62.5% 的时间里走完全程
    css = [
        f".dot{{animation:run {cyc}s cubic-bezier(.45,0,.55,1) infinite}}"
        f"@keyframes run{{0%{{transform:translateY(0);opacity:0}}4%{{opacity:1}}"
        f"{travel}%{{transform:translateY({y1 - y0}px);opacity:1}}88%{{transform:translateY({y1 - y0}px);opacity:1}}"
        f"96%,100%{{transform:translateY({y1 - y0}px);opacity:0}}}}"
    ]
    parts.append(
        f'<line x1="{nx}" y1="{y0 - 5}" x2="{nx}" y2="{y1 - 5}" stroke="{t["line"]}" stroke-opacity="{t["line2_op"]}" stroke-width="2"/>'
        f'<defs>{radial("dotg", t["brand3"], .9)}</defs>'
    )
    for i, (label, detail) in enumerate(steps):
        y = y0 + i * dy
        last = i == len(steps) - 1
        c = t["live"] if last else t["brand"]
        p = travel * i / (len(steps) - 1)
        css.append(
            f".n{i}{{animation:on{i} {cyc}s linear infinite}}"
            f"@keyframes on{i}{{0%,{max(p - .1, 0):.1f}%{{fill-opacity:0}}{p:.1f}%,88%{{fill-opacity:1}}96%,100%{{fill-opacity:0}}}}"
        )
        parts.append(
            f'<circle cx="{nx}" cy="{y - 5}" r="7.5" fill="{t["panel"]}" stroke="{c}" stroke-width="2"/>'
            f'<circle class="n{i}" cx="{nx}" cy="{y - 5}" r="4" fill="{c}"/>'
            f'<text x="{nx + 24}" y="{y}" font-size="15.5" font-weight="700" fill="{t["text"] if not last else t["live"]}">{e(label)}</text>'
            f'<text x="{px + pw - 28}" y="{y}" font-size="13.5" fill="{t["text3"]}" text-anchor="end">{e(detail)}</text>'
        )
    parts.append(f'<circle class="dot" cx="{nx}" cy="{y0 - 5}" r="10" fill="url(#dotg)"/>')
    parts.append(
        f'<text x="{px + 28}" y="{py + ph - 24}" font-size="12.5" fill="{t["text3"]}">'
        f'单次成本 <tspan fill="{t["text"]}" font-weight="700">{POC["cost"]}</tspan>'
        f' · 模型 DeepSeek · 模板 static-site</text>'
    )
    title = f"codeless — {w['desc']}"
    return svg_doc(W, H, title, "\n".join(parts), "".join(css))


def aurora_workflow(t):
    W, H = 1200, 344
    parts = [aurora_panel(W, H, t, blobs=[
        (W * .5, H * 1.1, W * .5, H * .8, AURORA_COLORS[0], t["aurora"][0] * .8),
        (W * .02, H * -.1, W * .3, H * .9, AURORA_COLORS[1], t["aurora"][1] * .8),
        (W * 1.0, H * .0, W * .3, H * .9, AURORA_COLORS[2], t["aurora"][2] * .8),
    ], with_wind=False)]
    tag = "人出判断，AI 出产能"
    tag_w = tw(tag, 20, True)
    parts.append("<defs>" + brand_gradient("tg", t, W - 64 - tag_w, W - 64) + brand_gradient("band", t, 64, W - 64) + "</defs>")
    parts.append(
        f'<text x="64" y="80" font-size="28" font-weight="800" fill="{t["text"]}">我只做三件事</text>'
        f'<text x="{W - 64}" y="80" font-size="20" font-weight="800" fill="url(#tg)" text-anchor="end">{e(tag)}</text>'
    )
    gap = 28
    cw = (W - 128 - 2 * gap) / 3
    y, ch = 108, 128
    for i, (head, sub, ic) in enumerate(STEPS):
        x = 64 + i * (cw + gap)
        parts.append(
            f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{ch}" rx="18" fill="{t["panel"]}" fill-opacity=".7" '
            f'stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>'
            f'<text class="mono" x="{x + 24:.1f}" y="{y + 38}" font-size="13" font-weight="700" fill="{t["brand"]}">0{i + 1}</text>'
            + line_icon(ic, x + cw - 24 - 30, y + 18, 30, t["brand2"])
            + f'<text x="{x + 24:.1f}" y="{y + 80}" font-size="23" font-weight="800" fill="{t["text"]}">{e(head)}</text>'
            f'<text x="{x + 24:.1f}" y="{y + 107}" font-size="14.5" fill="{t["text2"]}">{e(sub)}</text>'
        )
        if i < 2:  # 两张卡之间的小箭头
            ax = x + cw + gap / 2
            parts.append(
                f'<path d="M{ax - 4:.1f} {y + ch / 2 - 6} l6 6 -6 6" fill="none" stroke="{t["text3"]}" '
                'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            )
    # AI 那一条：一整道带子，光从左往右扫
    by, bh = 262, 46
    parts.append(
        f'<defs><clipPath id="bandc"><rect x="64" y="{by}" width="{W - 128}" height="{bh}" rx="{bh / 2}"/></clipPath>'
        f'<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity="{.5 if t is THEMES["light"] else .12}"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
        f'<rect x="64" y="{by}" width="{W - 128}" height="{bh}" rx="{bh / 2}" fill="url(#band)" fill-opacity=".1"/>'
        f'<g clip-path="url(#bandc)"><rect class="sheen" x="-260" y="{by}" width="260" height="{bh}" fill="url(#sheen)"/></g>'
        f'<rect x="64.5" y="{by + .5}" width="{W - 129}" height="{bh - 1}" rx="{bh / 2 - .5}" fill="none" '
        f'stroke="url(#band)" stroke-opacity=".55"/>'
        f'<linearGradient id="pill" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{SOLID[0]}"/>'
        f'<stop offset="1" stop-color="{SOLID[1]}"/></linearGradient>'
        f'<rect x="72" y="{by + 7}" width="52" height="32" rx="16" fill="url(#pill)"/>'
        f'<text x="98" y="{by + 28}" font-size="15" font-weight="800" fill="#fff" text-anchor="middle">AI</text>'
    )
    x = 146
    for j, item in enumerate(AI_DOES):
        parts.append(f'<text x="{x:.0f}" y="{by + 29}" font-size="15.5" font-weight="600" fill="{t["text2"]}">{e(item)}</text>')
        x += tw(item, 15.5, True)
        if j < len(AI_DOES) - 1:
            parts.append(f'<text x="{x + 14:.0f}" y="{by + 29}" font-size="15" fill="{t["text3"]}">→</text>')
            x += 44
    parts.append(f'<text x="{W - 90}" y="{by + 29}" font-size="14" fill="{t["text3"]}" text-anchor="end">全部交给 AI</text>')
    css = ".sheen{animation:sheen 7s ease-in-out infinite}@keyframes sheen{0%,20%{transform:translateX(0)}80%,100%{transform:translateX(1400px)}}"
    title = "我只做三件事：提出问题、选择方案、验收结果。人出判断，AI 出产能。"
    return svg_doc(W, H, title, "\n".join(parts), css)


def aurora_footer(t):
    """收尾：透明底，几条风线从页面里吹过去。"""
    W, H = 1200, 150
    parts = [
        wind(W, H, t, rows=(0.2, 0.42, 0.62, 0.8, 0.98), op=t["wind_op"] * 1.6),
        f'<text x="{W / 2}" y="78" font-size="15" fill="{t["text2"]}" text-anchor="middle">'
        f'decli <tspan fill="{t["text3"]}">·</tspan> AI Architect <tspan fill="{t["text3"]}">·</tspan> San Jose</text>',
        f'<text class="mono" x="{W / 2}" y="104" font-size="13" fill="{t["brand"]}" text-anchor="middle">decli.github.io</text>',
    ]
    return svg_doc(W, H, "decli · AI Architect · San Jose · decli.github.io", "\n".join(parts), AURORA_CSS)


# ═══════════════════════════════════════════════════════════════════
#  风格二：终端 Terminal —— 一个会自己敲字的 zsh 窗口
# ═══════════════════════════════════════════════════════════════════

TERM = dict(
    bg="#0a0f1f", bar="#0e1529", line="#96b2f0", text="#eaf0ff", text2="#a6b3d2", text3="#6f7b96",
    cyan="#22d3ee", purple="#a78bfa", blue="#7c9bff", green="#34d399",
)


def terminal_svg():
    T = TERM
    n, live = stats()
    W = 1000
    fs, lh = 15.5, 27
    x0, cx = 32, 72  # 提示符、命令各自一列：等宽字体在不同系统上宽度不一，分开放才不会互相压
    CPS = 0.045  # 每个字敲多久

    L = []  # (kind, payload)
    L.append(("cmd", "whoami"))
    L.append(("out", [(x0, [("decli", T["text"], 700), ("  AI Architect · San Jose", T["text2"], 400)])]))
    L.append(("gap", None))
    L.append(("cmd", "cat manifesto.md"))
    L.append(("out", [(x0, [("# " + HEADLINE[0].format(n=cn(n)) + HEADLINE[1], T["purple"], 700)])]))
    for s in LEDE:
        L.append(("out", [(x0, [(s, T["text2"], 400)])]))
    L.append(("gap", None))
    L.append(("cmd", "ls works/ --live"))
    for w in WORKS:
        if w.get("href"):
            L.append(("out", [
                (x0, [("●", T["green"], 400)]),
                (x0 + 24, [(w["name"], T["text"], 700)]),
                (x0 + 220, [(w["brief"], T["text2"], 400)]),
            ]))
    L.append(("out", [(x0, [(f"… 另有 {n - live} 个扩展、脚本、桌面和手机 App → decli.github.io", T["text3"], 400)])]))
    L.append(("gap", None))
    L.append(("cmd", "tail -3 codeless/poc.log"))
    for task, tpl, calls, cost, result in POC["runs"]:
        L.append(("out", [
            (x0, [(task, T["text"], 400)]),
            (x0 + 180, [(tpl, T["text3"], 400)]),
            (x0 + 320, [(calls, T["text2"], 400)]),
            (x0 + 440, [(cost, T["cyan"], 400)]),
            (x0 + 540, [(result, T["green"], 400)]),
        ]))
    L.append(("gap", None))
    L.append(("cmd", "wc -l handwritten/*"))
    L.append(("out", [(x0, [("       ", T["text2"], 400), ("0", T["purple"], 700), (" total", T["text2"], 400)])]))
    L.append(("end", None))

    top = 40
    H = top + 34 + len(L) * lh + 8
    parts = [
        f'<defs><clipPath id="win"><rect width="{W}" height="{H}" rx="14"/></clipPath>'
        + radial("tg1", T["purple"], .16) + radial("tg2", T["cyan"], .10) + "</defs>",
        f'<rect width="{W}" height="{H}" rx="14" fill="{T["bg"]}"/>',
    ]
    # 窗口里那两团光晕要画在文字「上面」：打字用的遮挡块是纯底色，
    # 光晕要是垫在下面，遮挡块在光晕里就会露出一个个深色方块
    chrome = [
        '<g clip-path="url(#win)">'
        f'<ellipse cx="{W * .92:.0f}" cy="{top}" rx="{W * .4:.0f}" ry="{H * .45:.0f}" fill="url(#tg1)"/>'
        f'<ellipse cx="{W * .05:.0f}" cy="{H:.0f}" rx="{W * .35:.0f}" ry="{H * .4:.0f}" fill="url(#tg2)"/>'
        f'<rect width="{W}" height="{top}" fill="{T["bar"]}"/>'
        f'<rect y="{top - 1}" width="{W}" height="1" fill="{T["line"]}" fill-opacity=".12"/></g>',
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="13.5" fill="none" stroke="{T["line"]}" stroke-opacity=".2"/>',
        '<circle cx="22" cy="20" r="6" fill="#ff5f57"/><circle cx="42" cy="20" r="6" fill="#febc2e"/>'
        '<circle cx="62" cy="20" r="6" fill="#28c840"/>',
        f'<text x="{W / 2}" y="25" font-size="13" fill="{T["text3"]}" text-anchor="middle">decli — zsh — {W // 10}×{len(L)}</text>',
    ]
    # 时间轴：命令一个字一个字敲出来，输出一行一行冒出来。只播一遍，停在最后那个闪烁的光标上。
    # 不播动画时（系统开了「减少动态效果」），所有行直接显示 —— 默认状态就是全显示，动画只负责「晚一点出现」。
    t = 0.6
    y = top + 34
    for kind, payload in L:
        if kind == "cmd":
            dur = max(len(payload), 1) * CPS
            cw = tw(payload, fs, mono=True) + 24
            parts.append(
                f'<text class="mono ap" x="{x0}" y="{y}" font-size="{fs}" style="animation-delay:{t:.2f}s">'
                f'<tspan fill="{T["cyan"]}">~</tspan><tspan fill="{T["purple"]}"> ❯</tspan></text>'
                f'<text class="mono ap" x="{cx}" y="{y}" font-size="{fs}" fill="{T["text"]}" '
                f'style="animation-delay:{t:.2f}s">{e(payload)}</text>'
                f'<rect class="cv" x="{cx - 2}" y="{y - fs}" width="{cw:.0f}" height="{lh}" fill="{T["bg"]}" '
                f'style="animation:type {dur:.2f}s steps({len(payload)}) {t:.2f}s"/>'
            )
            t += dur + 0.3
        elif kind == "out":
            segs = []
            for x, spans in payload:
                inner = "".join(
                    f'<tspan fill="{c}"' + (f' font-weight="{wt}"' if wt != 400 else "") + f">{e(s)}</tspan>"
                    for s, c, wt in spans
                )
                segs.append(f'<text class="mono" x="{x}" y="{y}" font-size="{fs}" xml:space="preserve">{inner}</text>')
            parts.append(f'<g class="ap" style="animation-delay:{t:.2f}s">{"".join(segs)}</g>')
            t += 0.07
        elif kind == "gap":
            t += 0.45
        elif kind == "end":
            parts.append(
                f'<text class="mono ap" x="{x0}" y="{y}" font-size="{fs}" style="animation-delay:{t:.2f}s">'
                f'<tspan fill="{T["cyan"]}">~</tspan><tspan fill="{T["purple"]}"> ❯</tspan></text>'
                f'<rect x="{cx}" y="{y - fs + 1}" width="9" height="{fs + 3}" fill="{T["text2"]}" '
                f'style="animation:ap .1s linear {t:.2f}s both, blink 1.1s step-end {t:.2f}s infinite"/>'
            )
        y += lh
    parts += chrome
    css = (
        ".ap{animation:ap .12s linear both}@keyframes ap{from{opacity:0}to{opacity:1}}"
        # 遮挡块从右往左缩：左边先露出来，看着就像一个字一个字在敲
        ".cv{transform:scaleX(0);transform-box:fill-box;transform-origin:100% 50%}"
        "@keyframes type{from{transform:scaleX(1)}to{transform:scaleX(0)}}"
        "@keyframes blink{50%{opacity:0}}"
    )
    title = (
        f"decli 的终端：whoami → decli, AI Architect, San Jose。"
        f"{HEADLINE[0].format(n=cn(n))}{HEADLINE[1]}。" + "".join(LEDE)
        + f" 在线作品：" + "、".join(w["name"] for w in WORKS if w.get("href")) + "。"
    )
    return svg_doc(W, H, title, "\n".join(parts), css)


# ═══════════════════════════════════════════════════════════════════
#  风格三：便当格 Bento —— 一张名片，一屏看完
# ═══════════════════════════════════════════════════════════════════

def bento_svg(t):
    M, G, CW, RH = 24, 16, 276, 196
    W = M * 2 + CW * 4 + G * 3
    H = M * 2 + RH * 4 + G * 3
    n, live = stats()

    def cell(c, r, cs=1, rs=1):
        return M + c * (CW + G), M + r * (RH + G), cs * CW + (cs - 1) * G, rs * RH + (rs - 1) * G

    defs = [
        f'<clipPath id="page"><rect width="{W}" height="{H}" rx="32"/></clipPath>',
        radial("pg1", AURORA_COLORS[0], t["aurora"][0] * .8),
        radial("pg2", AURORA_COLORS[1], t["aurora"][1] * .8),
        f'<linearGradient id="av" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{SOLID[0]}"/>'
        f'<stop offset="1" stop-color="{SOLID[1]}"/></linearGradient>',
        f'<linearGradient id="cta" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{SOLID[0]}"/>'
        f'<stop offset=".55" stop-color="{SOLID[1]}"/><stop offset="1" stop-color="{SOLID[2]}"/></linearGradient>',
        '<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff" stop-opacity=".28"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>',
    ]
    parts = [
        '<g clip-path="url(#page)">'
        f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>'
        f'<g class="b1"><ellipse cx="{W * .85:.0f}" cy="0" rx="{W * .45:.0f}" ry="{H * .5:.0f}" fill="url(#pg1)"/></g>'
        f'<g class="b2"><ellipse cx="0" cy="{H * .8:.0f}" rx="{W * .4:.0f}" ry="{H * .5:.0f}" fill="url(#pg2)"/></g></g>',
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="31.5" fill="none" stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>',
    ]

    def tile(x, y, w, h, fill=None):
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="{fill or t["panel"]}" '
            f'fill-opacity="{1 if fill else .78}" stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>'
        )

    def eyebrow(x, y, s):
        return f'<text x="{x}" y="{y}" font-size="13.5" font-weight="600" fill="{t["text3"]}">{e(s)}</text>'

    # A · 我是谁
    x, y, w, h = cell(0, 0, 2)
    a, b = HEADLINE[0].format(n=cn(n)), HEADLINE[1]
    defs.append(brand_gradient("hl", t, x + 28 + tw(a, 40, True), x + 28 + tw(a + b, 40, True)))
    parts.append(tile(x, y, w, h))
    parts.append(
        f'<rect x="{x + 28}" y="{y + 28}" width="52" height="52" rx="16" fill="url(#av)"/>'
        f'<text x="{x + 54}" y="{y + 63}" font-size="26" font-weight="700" fill="#fff" text-anchor="middle">d</text>'
        f'<text x="{x + 96}" y="{y + 51}" font-size="23" font-weight="700" fill="{t["text"]}">decli</text>'
        f'<text x="{x + 96}" y="{y + 74}" font-size="14" fill="{t["text3"]}">AI Architect · San Jose</text>'
        f'<text x="{x + 28}" y="{y + 142}" font-size="40" font-weight="800" letter-spacing="-.5" fill="{t["text"]}">'
        f'{e(a)}<tspan fill="url(#hl)">{e(b)}</tspan></text>'
        f'<text x="{x + 28}" y="{y + 174}" font-size="14.5" fill="{t["text2"]}">{e(LEDE[0])}</text>'
    )

    # B · 作品数   C · 手写代码
    x, y, w, h = cell(2, 0)
    parts.append(tile(x, y, w, h) + eyebrow(x + 24, y + 40, "全部作品"))
    parts.append(
        f'<text x="{x + 20}" y="{y + 132}" font-size="88" font-weight="800" letter-spacing="-3" fill="{t["text"]}">{n}</text>'
        f'<text x="{x + 24}" y="{y + 170}" font-size="13.5" fill="{t["text2"]}">网页、扩展、脚本、桌面、手机</text>'
    )
    x, y, w, h = cell(3, 0)
    defs.append(brand_gradient("zero", t, x + 20, x + 90))
    parts.append(tile(x, y, w, h) + eyebrow(x + 24, y + 40, "手写代码"))
    parts.append(
        f'<text x="{x + 20}" y="{y + 132}" font-size="88" font-weight="800" fill="url(#zero)">0'
        f'<tspan dx="6" font-size="22" font-weight="600" fill="{t["text2"]}">行</tspan></text>'
        f'<text x="{x + 24}" y="{y + 170}" font-size="13.5" fill="{t["text2"]}">UI 与代码全部由 AI 完成</text>'
    )

    # D · codeless（两格宽、两格高）
    x, y, w, h = cell(0, 1, 2, 2)
    cl = next(v for v in WORKS if v["slug"] == "codeless")
    defs.append(radial("clg", cl["tint"][0], t["glow_op"] * 1.5))
    defs.append(f'<clipPath id="clc"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22"/></clipPath>')
    parts.append(tile(x, y, w, h))
    parts.append(f'<g clip-path="url(#clc)"><ellipse cx="{x + w}" cy="{y}" rx="{w * .8:.0f}" ry="{h * .7:.0f}" fill="url(#clg)"/></g>')
    parts.append(icon(cl, x + 28, y + 28, 52, t))
    parts.append(
        f'<text x="{x + 96}" y="{y + 52}" font-size="26" font-weight="800" fill="{t["text"]}">codeless</text>'
        f'<text x="{x + 96}" y="{y + 75}" font-size="14" fill="{t["text3"]}">正在做 · 说一句话，得到一个能打开的网站</text>'
    )
    steps = POC["steps"]
    nx, y0, dy = x + 48, y + 138, 46
    y1 = y0 + dy * (len(steps) - 1)
    parts.append(f'<line x1="{nx}" y1="{y0 - 5}" x2="{nx}" y2="{y1 - 5}" stroke="{t["line"]}" stroke-opacity="{t["line2_op"]}" stroke-width="2"/>')
    for i, (label, detail) in enumerate(steps):
        yy = y0 + i * dy
        c = t["live"] if i == len(steps) - 1 else t["brand"]
        parts.append(
            f'<circle cx="{nx}" cy="{yy - 5}" r="7.5" fill="{t["panel"]}" stroke="{c}" stroke-width="2"/>'
            f'<circle cx="{nx}" cy="{yy - 5}" r="3.6" fill="{c}"/>'
            f'<text x="{nx + 24}" y="{yy}" font-size="16" font-weight="700" fill="{t["text"]}">{e(label)}</text>'
            f'<text x="{x + w - 28}" y="{yy}" font-size="13.5" fill="{t["text3"]}" text-anchor="end">{e(detail)}</text>'
        )
    defs.append(radial("dotg", t["brand3"], .9))
    parts.append(f'<circle class="dot" cx="{nx}" cy="{y0 - 5}" r="10" fill="url(#dotg)"/>')
    parts.append(
        f'<text x="{x + 28}" y="{y + h - 28}" font-size="13" fill="{t["text3"]}">POC 实测 · 单次成本 '
        f'<tspan font-weight="700" fill="{t["text"]}">{POC["cost"]}</tspan> · github.com/decli/codeless</text>'
    )

    # E–H · 四个在线就能玩的
    lives = [v for v in WORKS if v.get("href")][:4]
    for k, v in enumerate(lives):
        x, y, w, h = cell(2 + k % 2, 1 + k // 2)
        parts.append(tile(x, y, w, h))
        parts.append(icon(v, x + 24, y + 24, 48, t, uid=f"-{k}"))
        badge, bw = live_badge(0, 0, t)
        parts.append(f'<g transform="translate({x + w - 24 - bw:.1f} {y + 36})">{badge}</g>')
        parts.append(f'<text x="{x + 24}" y="{y + 106}" font-size="18" font-weight="700" fill="{t["text"]}">{e(v["name"])}</text>')
        parts.append(text_lines(wrap(v["brief"], 13.5, w - 48, max_lines=2), x + 24, y + 132, 20, 13.5, t["text2"]))
        url = v["href"].replace("https://", "").rstrip("/")
        parts.append(f'<text class="mono" x="{x + 24}" y="{y + h - 18}" font-size="12" fill="{t["text3"]}">{e(url)}</text>')

    # I · 我只做三件事
    x, y, w, h = cell(0, 3, 2)
    parts.append(tile(x, y, w, h) + eyebrow(x + 28, y + 40, "我只做三件事"))
    colw = (w - 56) / 3
    for i, (head, sub, ic) in enumerate(STEPS):
        cx = x + 28 + i * colw
        parts.append(
            f'<text class="mono" x="{cx:.1f}" y="{y + 76}" font-size="12" font-weight="700" fill="{t["brand"]}">0{i + 1}</text>'
            f'<text x="{cx:.1f}" y="{y + 106}" font-size="21" font-weight="800" fill="{t["text"]}">{e(head)}</text>'
            f'<text x="{cx:.1f}" y="{y + 130}" font-size="12.5" fill="{t["text3"]}">{e(sub)}</text>'
        )
    tag = "人出判断，AI 出产能。"
    defs.append(brand_gradient("tg", t, x + 28, x + 28 + tw(tag, 18, True)))
    parts.append(f'<text x="{x + 28}" y="{y + 172}" font-size="18" font-weight="800" fill="url(#tg)">{e(tag)}</text>')

    # J · 作品分布
    x, y, w, h = cell(2, 3)
    parts.append(tile(x, y, w, h) + eyebrow(x + 24, y + 40, "作品分布"))
    counts = [(k, label, sum(1 for v in WORKS if v["cat"] == k)) for k, label in CATS]
    bx, bwid = x + 24, w - 48
    for k, label, c in counts:
        seg = bwid * c / n
        parts.append(f'<rect x="{bx:.1f}" y="{y + 54}" width="{max(seg - 3, 2):.1f}" height="8" rx="4" fill="{color(t, CAT_COLORS[k])}"/>')
        bx += seg
    for i, (k, label, c) in enumerate(counts):
        yy = y + 92 + i * 20
        parts.append(
            f'<circle cx="{x + 28}" cy="{yy - 4.5}" r="4" fill="{color(t, CAT_COLORS[k])}"/>'
            f'<text x="{x + 40}" y="{yy}" font-size="13" fill="{t["text2"]}">{e(label)}</text>'
            f'<text x="{x + w - 24}" y="{yy}" font-size="13" font-weight="700" fill="{t["text"]}" text-anchor="end">{c}</text>'
        )

    # K · 去作品集
    x, y, w, h = cell(3, 3)
    defs.append(f'<clipPath id="ctac"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22"/></clipPath>')
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="url(#cta)"/>'
        f'<g clip-path="url(#ctac)"><rect class="sheen" x="{x - 200}" y="{y}" width="200" height="{h}" fill="url(#sheen)" '
        f'transform="skewX(-12)"/></g>'
        f'<circle cx="{x + w - 44}" cy="{y + 44}" r="20" fill="#fff" fill-opacity=".2"/>'
        f'<path d="M{x + w - 50} {y + 50} l12 -12 M{x + w - 48} {y + 38} h10 v10" fill="none" stroke="#fff" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<text x="{x + 24}" y="{y + 40}" font-size="13.5" font-weight="600" fill="#fff" fill-opacity=".82">看全部作品</text>'
        f'<text x="{x + 24}" y="{y + 132}" font-size="32" font-weight="800" fill="#fff">作品集</text>'
        f'<text class="mono" x="{x + 24}" y="{y + 164}" font-size="14" fill="#fff" fill-opacity=".9">decli.github.io</text>'
    )

    cyc = 8.0
    css = AURORA_CSS + (
        f".dot{{animation:run {cyc}s cubic-bezier(.45,0,.55,1) infinite}}"
        f"@keyframes run{{0%{{transform:translateY(0);opacity:0}}4%{{opacity:1}}"
        f"62%,88%{{transform:translateY({y1 - y0}px);opacity:1}}96%,100%{{transform:translateY({y1 - y0}px);opacity:0}}}}"
        ".sheen{animation:sheen 6s ease-in-out infinite}"
        "@keyframes sheen{0%,55%{transform:skewX(-12deg) translateX(0)}100%{transform:skewX(-12deg) translateX(620px)}}"
    )
    title = (
        f"decli · AI Architect · San Jose。{a}{b}。{LEDE[0]} "
        f"{n} 个作品，{live} 个可在线体验，0 行手写代码。正在做 codeless。"
    )
    return svg_doc(W, H, title, "<defs>" + "".join(defs) + "</defs>\n" + "\n".join(parts), css)


# ═══════════════════════════════════════════════════════════════════
#  README
# ═══════════════════════════════════════════════════════════════════

GENERATED = "<!-- 这个文件由 build.py 生成。改内容请改 build.py 里的数据，再跑 python3 build.py -->"


def out_dir(style):
    """主页那套放根目录（GitHub 只认根目录的 README），其余放 styles/ 下备用。
    assets/ 里的 SVG 全是生成的，每次先清空再写：删掉一个作品，它的卡片图也跟着消失。"""
    out = ROOT if style == HOME_STYLE else ROOT / "styles" / style
    if out == ROOT:  # 刚从备选换成主页的，styles/ 下那份旧的就不要了
        shutil.rmtree(ROOT / "styles" / style, ignore_errors=True)
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for f in assets.glob("*.svg"):
        f.unlink()
    return out


def picture(name, alt, width=None, href=None, themed=True):
    """一张跟着 GitHub 明暗主题切换的图。"""
    wattr = f' width="{width}"' if width else ""
    if themed:
        img = (
            f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
            f'<img alt="{e(alt)}" src="assets/{name}-light.svg"{wattr}></picture>'
        )
    else:
        img = f'<img alt="{e(alt)}" src="assets/{name}.svg"{wattr}>'
    return f'<a href="{href}">{img}</a>' if href else img


def link_of(w):
    return w.get("href") or w.get("dl") or f"{GH}/{w['repo']}"


def works_table():
    rows = ["| 作品 | 它替谁解决什么 | 入口 |", "| --- | --- | --- |"]
    for key, label in CATS:
        for w in (v for v in WORKS if v["cat"] == key):
            links = []
            if w.get("href"):
                links.append(f"[在线]({w['href']})")
            if w.get("dl"):
                links.append(f"[下载]({w['dl']})")
            links.append(f"[源码]({GH}/{w['repo']})")
            rows.append(f"| **{w['name']}**<br><sub>{label}</sub> | {w['brief']} | {' · '.join(links)} |")
    return "\n".join(rows)


def principles_md():
    return "\n\n".join(f"**{head}** {body}" for head, body in PRINCIPLES)


AURORA_SECTIONS = [
    ("替外贸生意干活", ["ftms", "ems"], "half"),
    ("顺手的小工具", ["wxformat3", "macpleco", "ip-geo", "jobornot"], "half"),
    ("给身边的人做的", ["logicc", "codehelper", "chinesechess"], "third"),
]


def build_aurora():
    out = out_dir("aurora")
    assets = out / "assets"
    by_slug = {w["slug"]: w for w in WORKS}
    for mode, t in THEMES.items():
        (assets / f"hero-{mode}.svg").write_text(aurora_hero(t))
        (assets / f"codeless-{mode}.svg").write_text(aurora_codeless(t))
        (assets / f"workflow-{mode}.svg").write_text(aurora_workflow(t))
        (assets / f"footer-{mode}.svg").write_text(aurora_footer(t))
        for _, slugs, size in AURORA_SECTIONS:
            H = max(aurora_card_layout(by_slug[s], size)[-1] for s in slugs)
            for s in slugs:
                (assets / f"card-{s}-{mode}.svg").write_text(aurora_card(by_slug[s], t, size, H))

    n, live = stats()
    a, b = HEADLINE[0].format(n=cn(n)), HEADLINE[1]
    md = [GENERATED, ""]
    md.append(picture("hero", f"decli — {a}{b}。" + "".join(LEDE), "100%", SITE))
    md.append("")
    md.append("### 正在做")
    md.append("")
    cl = by_slug["codeless"]
    md.append(picture("codeless", f"codeless — {cl['desc']}", "100%", link_of(cl)))
    for head, slugs, size in AURORA_SECTIONS:
        width = "49%" if size == "half" else "32%"
        md += ["", f"### {head}", "", "<p>"]
        for s in slugs:
            w = by_slug[s]
            md.append(picture(f"card-{s}", f"{w['name']} — {w['brief']}", width, link_of(w)))
        md.append("</p>")
    md += [""]
    md.append(picture("workflow", "我只做三件事：提出问题、选择方案、验收结果。人出判断，AI 出产能。", "100%"))
    md += ["", f"### 全部 {n} 个作品", "", works_table()]
    md += ["", "### 我相信的几件事", "", principles_md()]
    md += ["", picture("footer", "decli · AI Architect · San Jose · decli.github.io", "100%", SITE), ""]
    (out / "README.md").write_text("\n".join(md))


def build_terminal():
    out = out_dir("terminal")
    (out / "assets" / "terminal.svg").write_text(terminal_svg())
    n, live = stats()
    a, b = HEADLINE[0].format(n=cn(n)), HEADLINE[1]
    md = [GENERATED, ""]
    md.append(picture("terminal", f"decli — AI Architect · San Jose。{a}{b}。" + "".join(LEDE), "100%", SITE, themed=False))
    md += ["", "### `ls works/`", "", works_table()]
    md += ["", "### `cat ~/.principles`", "", principles_md()]
    md += [
        "", "### `open decli`", "",
        f"作品集 [decli.github.io]({SITE}) · 正在做 [codeless]({GH}/codeless) · San Jose", "",
    ]
    (out / "README.md").write_text("\n".join(md))


def build_bento():
    out = out_dir("bento")
    for mode, t in THEMES.items():
        (out / "assets" / f"bento-{mode}.svg").write_text(bento_svg(t))
    n, live = stats()
    a, b = HEADLINE[0].format(n=cn(n)), HEADLINE[1]
    alt = (
        f"decli · AI Architect · San Jose。{a}{b}。{n} 个作品，{live} 个可在线体验，0 行手写代码。"
        "正在做 codeless。我只做三件事：提出问题、选择方案、验收结果。"
    )
    links = [f'<a href="{SITE}"><b>作品集</b></a>', f'<a href="{GH}/codeless">codeless</a>']
    links += [f'<a href="{w["href"]}">{e(w["name"])}</a>' for w in WORKS if w.get("href")]
    md = [GENERATED, "", picture("bento", alt, "100%", SITE), ""]
    md += ['<p align="center">', " · ".join(links), "</p>", ""]
    md += [f"<details><summary>全部 {n} 个作品</summary>", "", works_table(), "", "</details>", ""]
    (out / "README.md").write_text("\n".join(md))


BUILDERS = {"aurora": build_aurora, "terminal": build_terminal, "bento": build_bento}

if __name__ == "__main__":
    names = sys.argv[1:] or list(BUILDERS)
    for name in names:
        if name not in BUILDERS:
            sys.exit(f"不认识的风格：{name}（可选：{' / '.join(BUILDERS)}）")
        BUILDERS[name]()
        print(f"✓ {name}")
