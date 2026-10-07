"""
studio/content.py —— 两套新主页共用的内容。

作品数据只有一份：直接从 build.py 里 import（WORKS / POC / PRINCIPLES …），
这里只补两套新风格额外要用的几样：
  - for_     「为谁做」—— 页面上唯一用橙色（我的判断）标出来的东西之一
  - en       英文名，跟作品集 sites.js 一致
  - shot     作品集里的真截图（decli.github.io/shots/），没有一张是画的
  - code     首屏那片「AI 写的代码」：一律取自 codeless 仓库里真实的源码
"""

from __future__ import annotations

import importlib.util
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("legacy_build", ROOT / "build.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

SITE, GH, EMAIL = B.SITE, B.GH, B.EMAIL
CATS = dict(B.CATS)
POC = B.POC
PRINCIPLES = [(h, b.replace(" —— ", "——")) for h, b in B.PRINCIPLES]
LEDE = [x.replace(" —— ", "——") for x in B.LEDE]
STEPS = B.STEPS
AI_DOES = B.AI_DOES
CAREER, CAREER_PAST, CAREER_NOW, BIO = B.CAREER, B.CAREER_PAST, B.CAREER_NOW, B.BIO
ICONS = B.ICONS
ROLE = "AI Architect"
# 旧主页写的「San Jose」跟作品集对不上（作品集里没有这个地名，倒是 IP 插件截图里的代理出口是 San Jose），
# 新版先不写地点 —— 要写的话在这里加，两套都会跟着变。
CITY = None

EN = {
    "codeless": "codeless", "ftms": "Tradewind", "ems": "EMS", "logicc": "Logicc", "wxformat3": "WxMark",
    "macpleco": "MacPleco", "ip-geo": "IP Geolocation", "jobornot": "JobOrNot", "wx-export": "WeChat MP Exporter",
    "tabinfocopy": "TabInfoCopy", "ip-display": "IP Display", "pagescroll": "PageScroll",
    "bing-wallpaper": "Bing Wallpaper Batch", "codehelper": "Pickup Code Helper", "chinesechess": "Chinese Chess",
}
CAT_EN = {"web": "Web app", "ext": "Extension", "script": "Userscript", "desktop": "macOS app", "app": "Android"}

# 「为谁做」—— 跟旧主页的分组同一套说法：替外贸生意干活 / 顺手的小工具 / 给身边的人做的
FOR = {
    "codeless": "正在做",
    "ftms": "替外贸生意", "ems": "替外贸生意",
    "logicc": "给孩子", "codehelper": "给家里老人", "chinesechess": "给老人",
}
FOR_DEFAULT = "顺手的小工具"

# 作品集里的真截图。一律裁成 1.6:1（跟版面里的图框同比例，不再二次裁切），
# 并且只取界面的一块：放大到界面上的字看得清，边缘落在界面自己的空隙上，不从字中间切开。
# mcrop 是手机版用的更小的一块。
SHOT = {
    "codeless": dict(rel="codeless/cafe"),
    # 裁切线都落在界面本身的空隙上（gaps：逐行 / 逐列找底色一致的带），不切字、不切卡片。都是 1.6 : 1。
    # 信风：侧栏 + 待办 + 经营大盘整排指标卡（左边补一点侧栏底色，好让上下都落在空隙里）；手机只要「还没睡，理查德」那块待办
    "ftms": dict(rel="ftms/dashboard", crop=(-0.0119, 0.0621, 0.4535, 0.5275), mcrop=(0.174, 0.0, 0.4578, 0.2838)),
    # EMS：顶上那条「数据全部虚构」的横幅留着，跳过面包屑，到第一条待办为止；手机只要第一张指标卡
    "ems": dict(rel="ems/dashboard", crop=(0.165, 0, 0.58, 0.415), stack=[(0, 0.0312), (0.1, 0.4838)],
                mcrop=(0.168, 0, 0.3775, 0.2095), mstack=[(0.1, 0.1391), (0.17, 0.3405)]),
    # 思维小画本：标题在原图里贴着左边，左边补一点底色；下边停在第二排卡片和第三排之间
    "logicc": dict(rel="logicc/home", crop=(-0.0221, 0, 0.4995, 0.703)),
    # WxMark：只要预览栏的正文，左右边距对称；下边停在第二条和第三条特点之间
    "wxformat3": dict(rel="wxformat3/editor", crop=(0.522, 0.1125, 0.98, 0.5705)),
    # MacPleco：停在「日志」那一行下面的空隙，不露下一行的边；比 1.6 扁出来的那点，底下补窗口底色
    "macpleco": dict(rel="macpleco/clean", crop=(0.215, 0.06, 0.93, 0.843)),
    # 插件：工具栏上的国家代码徽标 + 弹窗里「国家 / 大洲」两行，两块真截图摆在一起；IP、城市、时区那几行不露
    "ip-geo": dict(rel="ip-geo/popup", exhibit=[
        dict(crop=(0.6, 0.0, 1.018, 0.066), label="工具栏徽标"),   # 徽标在原图里贴着右边，补一点底色
        dict(crop=(0, 0, 0.62, 1), stack=[(0.068, 0.17), (0.43, 0.615)], label="弹窗"),
    ]),
}

# 显示用的分类：codeless 是自托管的服务，不是点开就能用的网页
CAT_SHOW = {"codeless": "自托管服务"}

# 精选：上大图的六个 —— 全是有真截图、点开就能用 / 能下载的
FEATURED = ["ftms", "ems", "logicc", "wxformat3", "macpleco", "ip-geo"]


def zh(s):
    """中文排版小修：破折号前后不留空格。"""
    return s.replace(" —— ", "——").replace(" ——", "——").replace("—— ", "——")


def works():
    out = []
    for i, w in enumerate(B.WORKS, 1):
        w = dict(w)
        w["desc"], w["brief"] = zh(w["desc"]), zh(w["brief"])
        w["no"] = i
        w["en"] = EN.get(w["slug"], w["name"])
        w["for_"] = FOR.get(w["slug"], FOR_DEFAULT)
        w["cat_zh"] = CAT_SHOW.get(w["slug"], CATS[w["cat"]])
        w["cat_en"] = CAT_EN[w["cat"]]
        w["link"] = w.get("href") or w.get("dl") or f"{GH}/{w['repo']}"
        w["src"] = f"{GH}/{w['repo']}"
        w["shot"] = SHOT.get(w["slug"])
        icon = w["icon"]
        w["icon_file"] = ROOT / "src" / "icons" / icon[1:] if icon.startswith("@") else None
        out.append(w)
    return out


WORKS = works()
BY = {w["slug"]: w for w in WORKS}
N = len(WORKS)
LIVE = sum(1 for w in WORKS if w.get("href"))


def cn(n):
    return B.cn(n)


# 首屏标题：跟作品集 decli.github.io 首屏一字不差
HEAD_A = "代码已不稀缺，"
HEAD_B = "判断才是。"


def code_lines(limit=200):
    """首屏背景那片代码：codeless 仓库里 AI 写的真代码，只留纯 ASCII 的行（嵌进去的等宽字体只切西文）。"""
    src = pathlib.Path("/home/claude/src-codeless/poc/agent")
    cache = ROOT / "studio" / "code.txt"
    if src.exists():
        lines = []
        for f in ["loop.py", "tools.py", "sandbox.py", "llm.py", "task.py", "publish.py"]:
            p = src / f
            if not p.exists():
                continue
            for ln in p.read_text().splitlines():
                ln = ln.rstrip().replace("\t", "    ")
                if not ln.strip() or not all(32 <= ord(c) < 127 for c in ln):
                    continue
                if ln.strip().startswith(("#", '"""')):
                    continue
                lines.append(ln)
        cache.write_text("\n".join(lines[:limit]) + "\n")
    return cache.read_text().splitlines()[:limit]


def alt_work(w):
    bits = [f"{w['name']}（{w['cat_zh']}）", w["brief"]]
    if w.get("href"):
        bits.append(f"在线体验：{w['href']}")
    if w.get("dl"):
        bits.append(f"下载：{w['dl']}")
    bits.append(f"源码：{w['src']}")
    return " — ".join(bits)
