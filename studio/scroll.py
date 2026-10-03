"""
studio/scroll.py —— 方向 C「长卷」。

一卷山水，从右往左看。山是 AI 写下的代码；卷上的朱印，是我盖的。

    近山就是代码本身：画出那张截图的源文件，竖排着一列一列灌进山形里，凑近了能读。
    远山的轮廓是那个仓库**全部**代码的行长，一行不少（studio/skyline.json，八万零八十四行）。
    山有多高，跟这个项目写了多少行走 —— 信风那座最高，TabInfoCopy 只是一块石头。
    朱印一件作品一方：古画上，画是画师的，印是鉴藏的人的 —— 盖印就是「我看过、我认」。
    AI 出产能、人出判断，换成这个媒介，正好是一卷画和画上的印。
    每件作品那句话旁边的朱笔圈点，是审稿的人留下的记号：圈的是我认为最要紧的那几个字。

── README 是竖着读的，长卷是横着看的 ──
所以把卷子裁成一段一段，从上往下摞：引首（右头带着卷轴和题签）、一整幅「八万行」的江山、
六段作品、十五张签条，最后是题跋（左头是另一根轴）。每一段自己从右往左读：题字在右，画在左。
段与段之间是两道锦边，装裱里叫「隔水」。

── 拼缝 ──
GitHub 把图片当行内元素排，图和图之间会露出一条几像素的行距缝。
这里所有图放在同一个 <p> 里、每张 <img align="top">：顶对齐的行内图不再给字的下伸部留位置，
整卷从上到下严丝合缝，看起来就是一张纸。（align="left/right" 会被 GitHub 加 20px 内边距，不能用。）

── 网格 ──
跟「零」同一套换算：桌面画布 1692 = README 栏 846px 的两倍，手机 648 = 324px 的两倍。
"""

from __future__ import annotations

import base64
import datetime
import json
import math
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import content as C  # noqa: E402
import kit  # noqa: E402
from kit import Doc, Stack, num  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
DW, MW = 1692, 648
SILK = 18          # 每段上下各一条锦边；两段摞起来就是一道 36 的隔水

STACKS = {
    "brush": Stack(["brush", "serif-sc-b"], kit.SYS_SERIF),
    "brush-lat": Stack(["instr-it"], kit.SYS_SERIF),
    "song": Stack(["serif-sc-r"], kit.SYS_SERIF),
    "song-sb": Stack(["serif-sc-sb"], kit.SYS_SERIF),
    "song-b": Stack(["serif-sc-b"], kit.SYS_SERIF),
    "lat": Stack(["instr", "serif-sc-r"], kit.SYS_SERIF),
    "seal": Stack(["serif-sc-k"], kit.SYS_SERIF),
    "code": Stack(["mono"], kit.SYS_MONO),
}

# 纸是一张实物：亮暗两套只差在纸的亮度 —— 暗色模式下纸压暗、偏旧，像放久了的绢，在 GitHub 的黑底上不刺眼。
# 小字（ink3）和朱红的字（red_t）在两种纸上都过 4.5:1
T = {
    "light": dict(paper="#ECE3CE", mat="#F4EEDF", ink="#1F1B17", ink2="#463F36", ink3="#6A6152",
                  red="#B2342A", red_t="#9E2A22", silk="#2A3650", silk_hi="#C7B98F", wash="#3E4A52",
                  stain="#7A5C32", tone=("#2a241d", "#f1e9d7"), roll=("#8d7f63", "#f5eedc", "#6f6249")),
    "dark": dict(paper="#C9BC9F", mat="#D3C7AC", ink="#1C1814", ink2="#3A332B", ink3="#4F473B",
                 red="#A93127", red_t="#7E1F16", silk="#1E2638", silk_hi="#AE9F76", wash="#36414A",
                 stain="#5E4524", tone=("#231e18", "#cdbfa2"), roll=("#6c614b", "#cfc4ac", "#544a37")),
}

EASE = "cubic-bezier(.22,.7,.12,1)"
BASE_CSS = (
    f".stamp{{animation:stamp .7s {EASE} both;transform-box:fill-box;transform-origin:50% 50%}}"
    "@keyframes stamp{0%{opacity:0;transform:scale(1.35) rotate(-6deg)}55%{opacity:1;transform:scale(.96)}100%{opacity:1;transform:none}}"
    f".rise{{animation:rise 1.6s {EASE} both;transform-box:fill-box;transform-origin:50% 100%}}"
    "@keyframes rise{from{transform:scaleY(0)}to{transform:none}}"
    f".fade{{animation:fade 1.1s {EASE} both}}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    f".unroll{{animation:unroll 1.8s {EASE} both;transform-box:fill-box;transform-origin:100% 50%}}"
    "@keyframes unroll{from{transform:scaleX(0)}to{transform:none}}"
)

# 印文：作品名里的汉字取二到四个；全是西文的就刻西文。不是篆书，是宋体最粗那一档 —— 诚实一点
SEAL_TEXT = {
    "codeless": "CODE LESS", "ftms": "信风", "ems": "营销", "logicc": "思维画本", "wxformat3": "WX MARK",
    "macpleco": "MAC PLECO", "ip-geo": "归属地", "jobornot": "职得投", "wx-export": "数据导出", "tabinfocopy": "TAB COPY",
    "ip-display": "IP", "pagescroll": "PAGE SCROLL", "bing-wallpaper": "壁纸", "codehelper": "取件码", "chinesechess": "象棋",
}
# 江山图上的地名签：短名
PLACE = {
    "codeless": "codeless", "ftms": "信风", "ems": "EMS", "logicc": "思维小画本", "wxformat3": "WxMark",
    "macpleco": "MacPleco", "ip-geo": "IP归属地", "jobornot": "职得投", "wx-export": "公众号导出", "tabinfocopy": "TabInfoCopy",
    "ip-display": "IP Display", "pagescroll": "PageScroll", "bing-wallpaper": "Bing壁纸", "codehelper": "取件码", "chinesechess": "中国象棋",
}

def seal_text(slug):
    """印文：SEAL_TEXT 里没写的新作品，取名字里的前两个汉字；没有汉字就取第一个西文词"""
    if slug in SEAL_TEXT:
        return SEAL_TEXT[slug]
    name = C.BY[slug]["name"]
    han = re.findall(r"[\u4e00-\u9fff]", name)
    return "".join(han[:2]) if len(han) >= 2 else re.findall(r"[A-Za-z]+", name)[0][:5].upper()


def place(slug):
    return PLACE.get(slug) or C.BY[slug]["name"]


# 上版面的六件：跟作品集首页一样 —— 能直接打开 / 下载的五件，加上 codeless（一句话变成网站，本身就是这卷画的主题）
FEATURED = ["codeless", "ftms", "ems", "logicc", "wxformat3", "macpleco"]

# 每件作品挂哪张截图：作品集里的真截图，裁到界面上的字看得清（复用「零」那套裁切参数，codeless 换成对话那一屏）
SHOT = dict(C.SHOT)
SHOT["codeless"] = dict(rel="codeless/chat", crop=(0.0, 0.0, 0.62, 0.62))
SHOT["macpleco"] = dict(rel="macpleco/clean", crop=(0.215, 0.06, 0.62, 0.525))   # 裁到「所有内容会先放进废纸篓」那一句看得清
SHOT_CAP = {"codeless": "一句话下去，测试、CI、上线地址都在这一屏", "ftms": "数据看板", "ems": "工作台",
            "logicc": "十二个游戏", "wxformat3": "左写右看", "macpleco": "清理 · 删的都先进废纸篓"}
# 朱笔圈点：每件作品那句话里，我圈出来的几个字
# 那句话在哪里换列
BRIEF_COLS = {"codeless": ["说一句话，它写代码、跑测试、改 bug，", "再部署成能打开的网站。"],
              "ftms": ["外贸全流程管理，从询盘到退税，", "一个 PI 号串到底。"],
              "ems": ["AI Agent 驱动的外贸增长，", "从找到买家到收到货款。"],
              "logicc": ["把做不下去的纸质练习册，", "改成十二个会读题的平板游戏。"],
              "wxformat3": ["公众号 Markdown 排版，", "一键复制成能直接粘贴的 HTML。"],
              "macpleco": ["不制造焦虑的 Mac 清理工具，", "删什么都先进废纸篓。"]}
EMPH = {"codeless": "能打开的网站", "ftms": "一个 PI 号串到底", "ems": "从找到买家到收到货款", "logicc": "会读题",
        "wxformat3": "一键复制", "macpleco": "先进废纸篓"}


# ═══════════════════════════════════════════════════════════════════
#  数据：行数、行长、代码摘录 —— 都跟作品集首页的透视层同一份
# ═══════════════════════════════════════════════════════════════════

def _sibling(rel):
    """作品集仓库里的文件（两个仓库并排 clone 着的话），拿来刷新本地缓存；没有就用缓存"""
    for base in (kit.ROOT.parent / "decli.github.io", pathlib.Path(os.environ.get("PORTFOLIO", "/nonexistent"))):
        p = base / rel
        if p.exists():
            return p
    return None


def _loc():
    cache = HERE / "loc.json"
    src = _sibling("code/index.json")
    if src:
        data = json.loads(src.read_text())
        slim = {"total": data["total"], "projects": {k: {"loc": v["loc"], "files": v["files"]} for k, v in data["projects"].items()}}
        cache.write_text(json.dumps(slim, ensure_ascii=False, indent=1) + "\n")
    return json.loads(cache.read_text())


LOC = _loc()
TOTAL = LOC["total"]
MAXLOC = max(v["loc"] for v in LOC["projects"].values())
_SKY = json.loads((HERE / "skyline.json").read_text())


def skyline(slug):
    b = _SKY.get(slug)
    return list(base64.b64decode(b)) if b else []


def code_of(slug):
    """画出那张截图的源文件：(行, 'repo/path', 起始行号)。
    来源是作品集仓库 code/<slug>.json 里那张截图的摘录（透视层用的同一份），缓存到 studio/code/<slug>.txt。
    只留纯 ASCII 的行：嵌进图里的等宽字体只切了西文。"""
    cache = HERE / "code" / f"{slug}.txt"
    key = SHOT[slug]["rel"].split("/")[1]
    src = _sibling(f"code/{slug}.json")
    if src:
        h = json.loads(src.read_text())
        s = h.get("shots", {}).get(key)
        if s:
            lines = [ln.rstrip() for ln in s["text"].split("\n") if ln.strip() and ln.isascii()]
            cache.parent.mkdir(exist_ok=True)
            cache.write_text(f"# {h['repo']}/{s['path']}  (从第 {s['start']} 行起，只留纯 ASCII 的行)\n" + "\n".join(lines) + "\n")
    if not cache.exists():
        return [], "", 1
    ls = cache.read_text().split("\n")
    m = re.match(r"# (\S+)\s+\(从第 (\d+) 行起", ls[0])
    path, start = (m.group(1), int(m.group(2))) if m else ("", 1)
    return [x for x in ls[1:] if x.strip()], path, start


def loc(slug):
    return LOC["projects"].get(slug, {}).get("loc", 0)


def cn(n):
    """37031 → 三万七千零三十一。带位数的读法写「零」，〇只用在逐位写的数里（GB/T 15835）"""
    D, U = "〇一二三四五六七八九", ["", "十", "百", "千"]

    def four(x):
        s, zero = "", False
        for i in range(3, -1, -1):
            d = (x // 10 ** i) % 10
            if d == 0:
                zero = s != ""
                continue
            if zero:
                s += "零"
                zero = False
            s += ("" if (d == 1 and i == 1 and s == "") else D[d]) + U[i]
        return s

    if not n:
        return "零"
    w, r = divmod(n, 10000)
    if not w:
        return four(r)
    return four(w) + "万" + (("零" if r < 1000 else "") + four(r) if r else "")


def kuan():
    """落款的年月：干支纪年 + 季节。每次重画，落款就是那一季（SOURCE_DATE_EPOCH 可以钉住）"""
    ts = os.environ.get("SOURCE_DATE_EPOCH")
    d = datetime.datetime.fromtimestamp(int(ts), datetime.timezone.utc) if ts else datetime.datetime.now()
    gz = "甲乙丙丁戊己庚辛壬癸"[(d.year - 4) % 10] + "子丑寅卯辰巳午未申酉戌亥"[(d.year - 4) % 12]
    season = "冬春春春夏夏夏秋秋秋冬冬"[d.month - 1]
    return gz + season


# ═══════════════════════════════════════════════════════════════════
#  画纸、锦边、卷轴、印
# ═══════════════════════════════════════════════════════════════════

def doc(w, h, title):
    d = Doc(w, h, title, STACKS)
    d.style(BASE_CSS)
    return d


def delay(s):
    return f'style="animation-delay:{s:.2f}s"'


def paper(d, t, x, y, w, h, seed=4, vignette=True, oy=0.0):
    """熟宣：底色 + 一层纤维 + 一圈很淡的茶渍（签条一张接一张，不要茶渍，不然一条一条的边会显出来）"""
    fid, gid, sid = d.uid("fib"), d.uid("vig"), d.uid("stn")
    d.deff(f'<filter id="{fid}" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".55 .08" '
           f'numOctaves="3" seed="{seed}"/><feColorMatrix values="0 0 0 0 .45  0 0 0 0 .36  0 0 0 0 .22  0 0 0 .14 0"/></filter>')
    d.deff(f'<filter id="{sid}" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".004" '
           f'numOctaves="3" seed="{seed + 5}"/><feColorMatrix values="0 0 0 0 .5  0 0 0 0 .38  0 0 0 0 .18  0 0 0 .2 -.05"/></filter>')
    d.deff(f'<radialGradient id="{gid}" cx="50%" cy="45%" r="75%"><stop offset=".55" stop-color="{t["stain"]}" stop-opacity="0"/>'
           f'<stop offset="1" stop-color="{t["stain"]}" stop-opacity=".14"/></radialGradient>')
    r = f'x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"'
    # oy：这张纸在整卷里往下数第几个单位。噪点按自己的坐标取样，平移过去，几张图拼起来纹理是接着的
    ro = f'x="{num(x)}" y="{num(y + oy)}" width="{num(w)}" height="{num(h)}"'
    g0, g1 = (f'<g transform="translate(0 {num(-oy)})">', "</g>") if oy else ("", "")
    d.add(f'<rect {r} fill="{t["paper"]}"/>{g0}<rect {ro} filter="url(#{sid})"/><rect {ro} filter="url(#{fid})"/>{g1}' +
          (f'<rect {r} fill="url(#{gid})"/>' if vignette else ""))


def silk(d, t, x, y, w, h):
    """锦边（隔水）：靛蓝底，两向斜纹的金线"""
    pid = d.uid("silk")
    d.deff(f'<pattern id="{pid}" width="9" height="9" patternUnits="userSpaceOnUse">'
           f'<path d="M0 9L9 0M-2 2L2-2M7 11L11 7" stroke="{t["silk_hi"]}" stroke-opacity=".22" stroke-width="1.6"/>'
           f'<path d="M0 0L9 9" stroke="{t["silk_hi"]}" stroke-opacity=".12" stroke-width="1.2"/></pattern>')
    r = f'x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"'
    d.add(f'<rect {r} fill="{t["silk"]}"/><rect {r} fill="url(#{pid})"/>')


def frame(d, t, W, H, top=True, bottom=True, x=0):
    """一段画心：上下锦边，中间纸。锦边和纸交界处压一道细细的暗线，像裱的时候折进去的边"""
    y0 = SILK if top else 0
    y1 = H - SILK if bottom else H
    paper(d, t, x, y0, W - x, y1 - y0)
    if top:
        silk(d, t, x, 0, W - x, SILK)
        d.add(f'<path d="M{num(x)} {SILK + 0.75}H{num(W)}" stroke="#2a1d10" stroke-opacity=".28" stroke-width="1.5"/>')
    if bottom:
        silk(d, t, x, H - SILK, W - x, SILK)
        d.add(f'<path d="M{num(x)} {num(H - SILK - 0.75)}H{num(W)}" stroke="#2a1d10" stroke-opacity=".28" stroke-width="1.5"/>')


def roller(d, t, x, y, h, w=34, side="r"):
    """卷着的纸：圆柱的明暗 + 两头的轴头 + 纸卷进去之前那一段阴影"""
    gid = d.uid("rl")
    a, b, c = t["roll"]
    d.deff(f'<linearGradient id="{gid}" x1="0" x2="1"><stop offset="0" stop-color="{a}"/><stop offset=".38" stop-color="{b}"/>'
           f'<stop offset=".55" stop-color="{b}"/><stop offset="1" stop-color="{c}"/></linearGradient>')
    d.add(f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="url(#{gid})"/>')
    sid = d.uid("rs")
    d.deff(f'<linearGradient id="{sid}" x1="{0 if side == "r" else 1}" x2="{1 if side == "r" else 0}">'
           f'<stop offset="0" stop-color="#3c2d19" stop-opacity="0"/><stop offset="1" stop-color="#3c2d19" stop-opacity=".2"/></linearGradient>')
    sx = x - 60 if side == "r" else x + w
    d.add(f'<rect x="{num(sx)}" y="{num(y)}" width="60" height="{num(h)}" fill="url(#{sid})"/>')


def rough(d):
    """印章的质感：边缘毛一点、印泥不匀一点。每张图定义一次"""
    if getattr(d, "_rough", None):
        return d._rough
    rid = d.uid("rough")
    d.deff(f'<filter id="{rid}" x="-10%" y="-10%" width="120%" height="120%">'
           f'<feTurbulence type="fractalNoise" baseFrequency=".7" numOctaves="2" seed="3" result="n"/>'
           f'<feDisplacementMap in="SourceGraphic" in2="n" scale="2.4" xChannelSelector="R" yChannelSelector="G" result="d"/>'
           f'<feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="3" seed="11" result="m"/>'
           f'<feColorMatrix in="m" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -4 3.5" result="blot"/>'
           f'<feTurbulence type="fractalNoise" baseFrequency="1.6" numOctaves="1" seed="5" result="g"/>'
           f'<feColorMatrix in="g" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -12 8.9" result="grain"/>'
           f'<feComposite in="blot" in2="grain" operator="in" result="mask"/>'
           f'<feComposite in="d" in2="mask" operator="in"/></filter>')
    d._rough = rid
    return rid


def seal_box(text):
    """印面的比例 (W, H)：两个字是竖长条，三四个字是方印，西文按词分行"""
    if re.fullmatch(r"[A-Za-z ]+", text):
        parts = text.split(" ")
        return min(100.0, max(64.0, 30.0 + 14.0 * max(map(len, parts)))), 34.0 + len(parts) * 30.0
    return (62.0 if len(text) == 2 else 100.0), 100.0


def seal_size(text, area):
    """同样的面积，不同印文的宽高：两个字的长条印不会比方印显得大一号"""
    W, H = seal_box(text)
    w = math.sqrt(area * W / H)
    return w, w * H / W


def seal(d, t, x, y, text, w=None, h=None, rot=-1.5, cls="", extra=""):
    """一方朱文印（白字红底）。(x, y) 是左上角；给 w 或 h 定大小。返回 (宽, 高)。
    竖排、从右往左：第一个字在右上；三个字是右列两字、左列一个长字"""
    rid = rough(d)
    W, H = seal_box(text)
    s = (w / W) if w else (h / H)
    g = []
    if re.fullmatch(r"[A-Za-z ]+", text):
        parts = text.split(" ")
        for i, wd in enumerate(parts):
            fs = 19 if len(wd) > 4 else 23
            g.append((W / 2, 17 + (i + 0.78) * ((H - 26) / len(parts)), wd, fs, 1.0))
        sp = ' letter-spacing="1.5"'
    else:
        n = len(text)
        lay = {1: [(0, 0, 1, 1)], 2: [(0, 0, 1, 2), (0, 1, 1, 2)],
               3: [(1, 0, 2, 2), (1, 1, 2, 2), (0, 0, 2, 1)], 4: [(1, 0, 2, 2), (1, 1, 2, 2), (0, 0, 2, 2), (0, 1, 2, 2)]}[min(n, 4)]
        for i, ch in enumerate(text[:4]):
            cx_, cy_, nc, nr = lay[i]
            cw, chh = (W - 18) / nc, (H - 18) / nr
            tall = n == 3 and i == 2
            fs = min(cw, chh) * (0.95 if tall else 0.9)
            g.append((9 + cw * cx_ + cw / 2, 9 + chh * cy_ + chh / 2 + fs * 0.36, ch, fs, 1.9 if tall else 1.0))
        sp = ""
    cx, cy = x + W * s / 2, y + H * s / 2
    d.add(f'<g transform="rotate({num(rot)} {num(cx)} {num(cy)})"><g class="{cls}" {extra}>'
          f'<g filter="url(#{rid})" transform="translate({num(x)} {num(y)}) scale({num(s)})">'
          f'<rect x="1.5" y="1.5" width="{num(W - 3)}" height="{num(H - 3)}" rx="4" fill="{t["red"]}"/>')
    for gx, gy, ch, fs, sy in g:
        tr = ""
        if sy != 1:
            oy = gy - fs * 0.36
            tr = f' transform="translate({num(gx)} {num(oy)}) scale(1 {num(sy)}) translate({num(-gx)} {num(-oy)})"'
        d.text(gx, gy, ch, "seal", fs, "#F4ECDC", anchor="middle", extra=tr + sp)
    d.add("</g></g></g>")
    return W * s, H * s


# ═══════════════════════════════════════════════════════════════════
#  竖排
# ═══════════════════════════════════════════════════════════════════

# 竖排标点：直接用 Unicode 的竖排形式（思源宋体都有），位置是字体设计师摆好的
VFORM = {"，": "︐", "。": "︒", "、": "︑", "：": "︓", "；": "︔", "！": "︕", "？": "︖", "（": "︵", "）": "︶",
         "「": "﹁", "」": "﹂", "『": "﹃", "』": "﹄", "《": "︽", "》": "︾", "…": "︙", "·": "・"}
NO_START = set("︐︒︑︓︔︕︖︶﹂﹄︾︙")
LAT = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+#/&'’\-]*(?: [A-Za-z][A-Za-z0-9.+#/&'’\-]*)*")  # 空格连着的西文词组整体转


def vtokens(text):
    """→ [(kind, s, idx)]：cjk 一个字一格；tcy 两个以内的西文/数字横着挤进一格（纵中横）；lat 转九十度；dash 一条线"""
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        m = LAT.match(text, i)
        if m:
            g = m.group()
            out.append(("tcy" if len(g) <= 2 else "lat", g, i))
            i = m.end()
            continue
        if ch.isspace():
            out.append(("sp", " ", i))
        elif text[i:i + 2] == "——":
            out.append(("dash", "——", i))
            i += 2
            continue
        else:
            out.append(("cjk", VFORM.get(ch, ch), i))
        i += 1
    return out


def vcolumns(d, text, size, max_h, track=0.08, lat_stack="song", balance=True):
    """把一段字切成竖排的列：[[(kind, s, adv, idx), ...], ...]。
    折成几列就把字平均分到几列里（balance）：不会剩一两个字孤零零占一列"""
    cell = size * (1 + track)
    if balance and max_h < 1e8:
        total = sum(a for col in vcolumns(d, text, size, 1e9, track, lat_stack, False) for _, _, a, _ in col)
        if total > max_h:
            n = math.ceil(total / max_h)
            for k in range(n, n + 3):       # 平均下来某一列装不下（西文词不能拆），就多分一列
                cols = vcolumns(d, text, size, total / k + cell * 0.95, track, lat_stack, False)
                if len(cols) <= k and all(sum(a for _, _, a, _ in c) <= max_h + 0.1 for c in cols):
                    return cols
    cols, cur, h = [], [], 0.0
    toks = vtokens(text)
    for k, (kind, s, idx) in enumerate(toks):
        if kind == "sp":
            prev = toks[k - 1][0] if k else ""
            nxt = toks[k + 1][0] if k + 1 < len(toks) else ""
            if prev in ("lat", "tcy") and nxt in ("lat", "tcy"):
                adv = size * 0.3
            else:
                continue
        elif kind == "lat":
            adv = d.width(s, lat_stack, size * 0.9) + size * 0.3
        elif kind == "dash":
            adv = cell * 2
        else:
            adv = cell
        if cur and h + adv > max_h + 0.1 and not (kind == "cjk" and s in NO_START):
            cols.append(cur)
            cur, h = [], 0.0
        cur.append((kind, s, adv, idx))
        h += adv
    if cur:
        cols.append(cur)
    return cols


def vdraw(d, col, xc, y_top, stack, size, color, lat_stack="song", emph=None, cls=None, extra=""):
    """画一列：列中线 xc，从 y_top 往下。emph=(起, 止, 颜色) 给这一段字加朱笔圈点。返回这一列的高度"""
    y = y_top

    def dot(cy):
        d.add(f'<circle cx="{num(xc + size * 0.6)}" cy="{num(cy)}" r="{num(size * 0.1)}" fill="none" '
              f'stroke="{emph[2]}" stroke-width="{num(size * 0.06)}"/>')

    for kind, s, adv, idx in col:
        on = emph and emph[0] <= idx < emph[1] and kind != "sp"
        if on and kind == "cjk":
            dot(y + size * 0.5)
        elif on and kind in ("tcy", "lat"):
            k_ = max(1, round(adv / (size * 1.1)))
            for j in range(k_):
                dot(y + adv * (j + 0.5) / k_)
        if kind == "cjk":
            d.text(xc, y + size * 0.88, s, stack, size, color, anchor="middle", cls=cls, extra=extra)
        elif kind == "dash":
            d.add(f'<path d="M{num(xc)} {num(y + size * 0.2)}V{num(y + adv - size * 0.2)}" stroke="{color}" stroke-width="{num(size * 0.06)}"/>')
        elif kind == "tcy":
            # 纵中横：两个字母挤进一格。尽量大 —— 西文的大写只有汉字的七成高，按汉字的字号排就显得小
            fs = size * (1.0 if len(s) == 1 else 0.92)
            fs = min(fs, size * 1.02 / max(0.01, d.width(s, lat_stack, 1)))
            d.text(xc, y + size * 0.5 + fs * 0.35, s, lat_stack, fs, color, anchor="middle", cls=cls, extra=extra)
        elif kind == "lat":
            cy = y + adv / 2
            d.text(xc, cy + size * 0.31, s, lat_stack, size * 0.9, color, anchor="middle", cls=cls,
                   extra=f'transform="rotate(90 {num(xc)} {num(cy)})" {extra}')
        y += adv
    return y - y_top


def vtext(d, x_right, y_top, text, stack, size, color, max_h, col_step=None, track=0.08, emph=None, lat_stack="song",
          cls=None, start=None, step=0.04, outline=""):
    """竖排一段字：第一列的右边在 x_right，列从右往左排。emph=(要圈的那几个字, 颜色)。
    返回 (列数, 占的宽度, 最长一列的高度)"""
    cols = vcolumns(d, text, size, max_h, track, lat_stack)
    col_step = col_step or size * 1.75
    rng = None
    if emph and emph[0] in text:
        a = text.index(emph[0])
        rng = (a, a + len(emph[0]), emph[1])
    tallest = 0.0
    for c, col in enumerate(cols):
        ex_ = (delay(start + c * step) if start is not None else "") + (" " + outline if outline else "")
        tallest = max(tallest, vdraw(d, col, x_right - size / 2 - c * col_step, y_top, stack, size, color, lat_stack, rng, cls, ex_))
    return len(cols), (len(cols) - 1) * col_step + size, tallest


def vblock(d, x_right, y_top, lines, stack, size, color, max_h, col_step=None, track=0.08, emph=None, lat_stack="song",
           cls=None, start=None, step=0.04, outline=""):
    """几句话竖排，每句另起一列（断在哪里由写的人定，太长才自动折）。参数和返回值同 vtext"""
    col_step = col_step or size * 1.75
    n, tallest = 0, 0.0
    for ln in lines:
        rng = None
        if emph and emph[0] and emph[0] in ln:
            a = ln.index(emph[0])
            rng = (a, a + len(emph[0]), emph[1])
        for col in vcolumns(d, ln, size, max_h, track, lat_stack):
            ex_ = (delay(start + n * step) if start is not None else "") + (" " + outline if outline else "")
            tallest = max(tallest, vdraw(d, col, x_right - size / 2 - n * col_step, y_top, stack, size, color, lat_stack, rng, cls, ex_))
            n += 1
    return n, (n - 1) * col_step + size, tallest


def vlen(d, text, size, track=0.08, lat_stack="song"):
    """一段字排成一整列有多长"""
    return sum(a for col in vcolumns(d, text, size, 1e9, track, lat_stack) for _, _, a, _ in col)


def ruled(d, t, x_right, top, lines, size, step, max_h, color, track=0.12, cls=None, start=0.0, emph=None):
    """朱丝栏：信笺上一道道朱红的竖格。一句一起头，一列一格。返回占的宽度"""
    cols = []
    for ln in lines:
        rng = None
        if emph and emph[0] in ln:
            a = ln.index(emph[0])
            rng = (a, a + len(emph[0]), emph[1])
        cols += [(c, rng) for c in vcolumns(d, ln, size, max_h, track)]
    pad = size * 0.7
    tallest = max(sum(a for _, _, a, _ in col) for col, _ in cols)
    for i, (col, rng) in enumerate(cols):
        vdraw(d, col, x_right - (i + 0.5) * step, top, "song", size, color, emph=rng, cls=cls,
              extra=delay(start + i * 0.06) if cls else "")
    n = len(cols)
    y0, y1 = top - pad, top + tallest + pad * 0.75
    rs = "".join(f"M{num(x_right - i * step)} {num(y0)}V{num(y1)}" for i in range(1, n))
    d.add(f'<path d="{rs}" stroke="{t["red"]}" stroke-opacity=".38" stroke-width="1.2" fill="none"/>')
    d.add(f'<rect x="{num(x_right - n * step)}" y="{num(y0)}" width="{num(n * step)}" height="{num(y1 - y0)}" fill="none" '
          f'stroke="{t["red"]}" stroke-opacity=".55" stroke-width="2.2"/>')
    return n * step


# ═══════════════════════════════════════════════════════════════════
#  山
# ═══════════════════════════════════════════════════════════════════

def ridge(lines, cols, win):
    """每一格取那一段代码行长的均值和最大值，再用一个窗口抹平"""
    n = len(lines)
    if not n:
        return [0.0] * cols
    raw = []
    for c in range(cols):
        a = int(c / cols * n)
        b = max(a + 1, int((c + 1) / cols * n))
        seg = lines[a:min(b, n)] or [0]
        raw.append(sum(seg) / len(seg) * 0.6 + max(seg) * 0.4)
    sm = []
    for c in range(cols):
        lo, hi = max(0, c - win), min(cols, c + win + 1)
        sm.append(sum(raw[lo:hi]) / (hi - lo))
    return sm


def _norm(v):
    lo, hi = min(v), max(v)
    return [(x - lo) / (hi - lo) if hi > lo else 0.5 for x in v]


def profile(lines, cols, taper=0.12, sharp=1.5, coarse_div=7, fine_div=40):
    """一道山脊，0～1。粗抹平定山势（哪一段代码写得满，哪里就是主峰），细抹平定山石；两头收成山脚。
    代码的行长本身起伏不大，直接画是一块平台 —— 所以按这一卷自己的最高和最低拉开"""
    if not lines:
        return [0.0] * cols
    coarse = _norm(ridge(lines, cols, max(2, cols // coarse_div)))
    fine = _norm(ridge(lines, cols, max(1, cols // fine_div)))
    out = []
    for c in range(cols):
        u = c / max(1, cols - 1)
        foot = math.sin(min(1.0, min(u, 1 - u) / taper) * math.pi / 2)
        out.append((0.16 + 0.6 * coarse[c] ** sharp + 0.24 * fine[c]) * foot)
    m = max(out) or 1
    return [h / m for h in out]


def wash(d, t, a, b=0.0, col=None):
    """淡墨：上浓下淡的竖向渐变，山脚化进雾里"""
    key = (a, b, col)
    cache = d.__dict__.setdefault("_wash", {})
    if key not in cache:
        gid = d.uid("wash")
        d.deff(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{col or t["wash"]}" stop-opacity="{a}"/>'
               f'<stop offset="1" stop-color="{col or t["wash"]}" stop-opacity="{b}"/></linearGradient>')
        cache[key] = gid
    return cache[key]


def far(d, t, slug, x, base, w, hmax, op=1.0, res=5):
    """远山：这个仓库每一行代码的长度。后面一层淡而高，前面一层浓而矮、错开一点。res 是几个单位取一个点"""
    lines = skyline(slug)
    if not lines or w < 4:
        return None
    cols = max(12, int(w / res))
    peak = None
    for li, (sharp, cdiv, fdiv, amp, dx, a, so) in enumerate(((1.6, 6, 30, 1.0, 0.0, .30, .30), (1.1, 12, 60, .58, .07, .40, .45))):
        p = profile(lines[::-1] if li else lines, cols, sharp=sharp, coarse_div=cdiv, fine_div=fdiv)
        xs = x + dx * w * (1 if li else 0)
        ww = w * (1 - dx) if li else w
        pts = [(xs + c / (cols - 1) * ww, base - p[c] * hmax * amp) for c in range(cols)]
        if li == 0:
            k = max(range(cols), key=lambda c: p[c])
            peak = pts[k]
        poly = " L".join(f"{num(px)},{num(py)}" for px, py in pts)
        d.add(f'<path d="M{num(xs)},{num(base)} L{poly} L{num(xs + ww)},{num(base)} Z" fill="url(#{wash(d, t, round(a * op, 3), 0.02)})"/>'
              f'<path d="M{poly}" fill="none" stroke="{t["wash"]}" stroke-opacity="{num(so * op)}" stroke-width="{1.5 if li else 1.2}" '
              f'stroke-linejoin="round"/>')
    return peak


def near(d, t, slug, x_right, base, width, hmax, size=20, t0=0.3):
    """近山：代码本身。把源文件去掉缩进，一行接一行，竖排着从右往左一列一列灌进山形里 ——
    山形是这个文件自己的行长；字从山脊往下读，凑近了就是那几行代码"""
    lines, _, _ = code_of(slug)
    if not lines:
        return
    pitch = size * 1.16
    cols = int(width / pitch)
    adv = size * 0.6          # Geist Mono 的字宽
    prof = profile([len(ln.strip()) for ln in lines], cols, taper=0.16, sharp=1.25, coarse_div=5, fine_div=24)
    stream = "  ".join(ln.strip() for ln in lines)
    gid, mid = d.uid("nf"), d.uid("nm")
    y0 = base - hmax
    d.deff(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{num(y0)}" x2="0" y2="{num(base)}">'
           f'<stop offset="0" stop-color="#fff"/><stop offset=".55" stop-color="#fff" stop-opacity=".78"/>'
           f'<stop offset="1" stop-color="#fff" stop-opacity=".12"/></linearGradient>')
    d.deff(f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="{num(x_right - width - 20)}" y="{num(y0 - 20)}" width="{num(width + 40)}" '
           f'height="{num(hmax + 40)}"><rect x="{num(x_right - width - 20)}" y="{num(y0 - 20)}" width="{num(width + 40)}" '
           f'height="{num(hmax + 40)}" fill="url(#{gid})"/></mask>')
    d.add(f'<g mask="url(#{mid})"><g class="rise" {delay(t0)}>')
    pos = 0
    for c in range(cols):
        n = max(2, int(hmax * (0.1 + 0.9 * prof[c]) / adv))
        while pos < len(stream) and stream[pos] == " ":     # 列首不留空格：山脊就是山形本身
            pos += 1
        if pos >= len(stream):
            pos = 0
        s = stream[pos:pos + n].rstrip()
        pos += n
        if not s:
            continue
        top = base - len(s) * adv
        bx = x_right - (c + 0.5) * pitch - size * 0.36
        d.text(bx, top, s, "code", size, t["ink"], extra=f'transform="rotate(90 {num(bx)} {num(top)})"')
    d.add("</g></g>")


def mist(d, t, x, y, w, h, op=0.85):
    gid = d.uid("fog")
    d.deff(f'<linearGradient id="{gid}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{t["paper"]}" stop-opacity="{op}"/>'
           f'<stop offset="1" stop-color="{t["paper"]}" stop-opacity="0"/></linearGradient>')
    d.add(f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="url(#{gid})"/>')


def hscale(slug):
    """山的高度跟代码量走。开平方：不然最小的那几件看不见"""
    return 0.18 + 0.82 * math.sqrt(loc(slug) / MAXLOC)


def ranges_strip(d, t, x0, base, width, hmax, op=1.0, res=5):
    """整卷的山：十五个仓库一字排开，从右往左（第一件在最右）。宽度按行数开方分，高度按行数开方定。
    返回每座山的 (slug, 山顶 x, 山顶 y)"""
    slugs = [w["slug"] for w in C.WORKS]
    ws = [math.sqrt(max(1, loc(s))) for s in slugs]
    tot = sum(ws)
    x = x0 + width
    peaks = []
    for s, wv in zip(slugs, ws):
        w = width * wv / tot
        x -= w
        pk = far(d, t, s, x - w * 0.08, base, w * 1.16, hmax * hscale(s), op=op, res=res)
        peaks.append((s,) + (pk or (x + w / 2, base - 8)))
    return peaks


def places(d, t, peaks, size, lo, hi, top_min, zone=1e9, gap=16):
    """地名签：旧舆图上山头旁边那种小纸签，竖写山名。签子之间挤不下就往两边让，拉一根细线指回山顶"""
    items = []
    for s, px, py in peaks:
        txt = place(s)
        h = vlen(d, txt, size, 0.06) + size * 0.7
        items.append(dict(s=s, px=px, py=py, x=px, h=h, w=size + size * 0.62))
    items.sort(key=lambda it: it["px"])
    sp = max(it["w"] for it in items) + size * 0.3
    for _ in range(200):
        moved = False
        for a, b in zip(items, items[1:]):
            if b["x"] - a["x"] < sp:
                push = (sp - (b["x"] - a["x"])) / 2 + 0.01
                a["x"] -= push
                b["x"] += push
                moved = True
        for it in items:
            it["x"] = min(hi - it["w"] / 2, max(lo + it["w"] / 2, it["x"]))
        if not moved:
            break
    # 题字那一块（x < zone）不让签子往上顶
    for it in items:
        it["yb"] = max((top_min if it["x"] < zone else SILK + 24) + it["h"], it["py"] - gap)
    # 先画所有的线，再画签子：线不会压在别人的签子上。线先直着往下，快到山顶再斜过去
    for it in items:
        x, yb, px, py = it["x"], it["yb"], it["px"], it["py"]
        knee = max(yb, py - 3 - min(18, abs(px - x)))
        d.add(f'<path d="M{num(x)} {num(yb)}V{num(knee)}L{num(px)} {num(py - 3)}" fill="none" stroke="{t["ink"]}" stroke-opacity=".4" stroke-width="1.2"/>')
    for it in items:
        x, w, h, yb = it["x"], it["w"], it["h"], it["yb"]
        d.add(f'<rect x="{num(x - w / 2)}" y="{num(yb - h)}" width="{num(w)}" height="{num(h)}" fill="{t["mat"]}" '
              f'stroke="{t["red"]}" stroke-opacity=".7" stroke-width="1.4"/>')
        vtext(d, x + size / 2, yb - h + size * 0.32, place(it["s"]), "song", size, t["ink"], 1e9, track=0.06)
    return items


# ═══════════════════════════════════════════════════════════════════
#  截图：当画挂在天上 —— 调成墨色，印在纸上
# ═══════════════════════════════════════════════════════════════════

def hang(d, t, slug, x, y, w, mobile=False, t0=0.2):
    s = SHOT[slug]
    crop = s.get("mcrop") if mobile and s.get("mcrop") else s.get("crop")
    stack = s.get("mstack") if mobile and s.get("mstack") else s.get("stack")
    uri, iw, ih = kit.shot_uri(s["rel"], int(w), crop=crop, stack=stack, tone=t["tone"], aspect=1.6)
    h = w / 1.6
    pad = 12 if not mobile else 9
    d.add(f'<g class="fade" {delay(t0)}>')
    d.add(f'<rect x="{num(x - pad)}" y="{num(y - pad)}" width="{num(w + 2 * pad)}" height="{num(h + 2 * pad)}" fill="{t["mat"]}" '
          f'stroke="{t["ink"]}" stroke-opacity=".16" stroke-width="1.5"/>')
    d.add(f'<image href="{uri}" x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" preserveAspectRatio="xMidYMin slice" '
          f'style="mix-blend-mode:multiply"/>')
    d.add(f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="none" stroke="{t["ink"]}" stroke-opacity=".22" stroke-width="1.2"/>')
    d.add("</g>")
    return h + pad


def halo(t, w=7):
    """压在山上的字：描一圈纸色的边，字不会被山吃掉"""
    return f'stroke="{t["paper"]}" stroke-width="{w}" stroke-linejoin="round" paint-order="stroke"'


# ═══════════════════════════════════════════════════════════════════
#  引首
# ═══════════════════════════════════════════════════════════════════

# 引言一列一句，断在哪里是排的人定的
LEDE = ["十五个作品，从 UI 交互设计", "到每一行代码编写，", "全部由 AI 完成。", "我只做三件事：",
        "提出问题、选择方案、验收结果。", "人出判断，AI 出产能。", "不是尝鲜，", "这是 AI Native 时代工作新范式。"]


def ledger(d, t, x_right, top, size, big, step, cls=True):
    """一笔账：右列「我写的代码 〇 行」，左列「AI 写的代码 八万〇八十四 行」。两列顶对齐，长短就是差别"""
    xa = x_right - step / 2
    h1 = vlen(d, "我写的代码", size, 0.2)
    vtext(d, xa + size / 2, top, "我写的代码", "song", size, t["ink3"], 1e9, track=0.2, cls="fade", start=1.5)
    zy = top + h1 + size * 0.5
    d.text(xa, zy + big * 1.05 * 0.86, "〇", "song-sb", big * 1.05, t["red"], anchor="middle", cls="stamp", extra=delay(2.2))
    vtext(d, xa + size / 2, zy + big * 1.05 + size * 0.4, "行", "song", size, t["ink3"], 1e9, cls="fade", start=1.6)
    xb = xa - step
    h2 = vlen(d, "AI 写的代码", size, 0.2)
    vtext(d, xb + size / 2, top, "AI 写的代码", "song", size, t["ink3"], 1e9, track=0.2, cls="fade", start=1.6)
    ny = top + h2 + size * 0.5
    bs = big * 0.56
    _, _, nh = vtext(d, xb + bs / 2, ny, cn(TOTAL), "song-sb", bs, t["ink"], 1e9, track=0.1, cls="fade", start=1.8, step=0.0)
    vtext(d, xb + size / 2, ny + nh + size * 0.4, "行", "song", size, t["ink3"], 1e9, cls="fade", start=1.9)
    return ny + nh + size * 1.5


def hero(t, mobile=False):
    title = (f"decli 作品长卷 · 引首：一行代码没写。{C.HEAD_A}从 UI 交互设计到每一行代码编写，全部由 AI 完成。"
             f"我只做三件事：提出问题、选择方案、验收结果——人出判断，AI 出产能。我写的代码〇行，AI 写的 {TOTAL:,} 行。")
    if not mobile:
        W, H = DW, 1080
        PW = W - 64                     # 纸的右边；再往右是包首的锦和卷轴
        d = doc(W, H, title)
        cid = d.uid("un")
        d.deff(f'<clipPath id="{cid}"><rect class="unroll" x="0" y="0" width="{PW}" height="{H}"/></clipPath>')
        d.add(f'<g clip-path="url(#{cid})">')
        frame(d, t, PW, H)
        ranges_strip(d, t, 40, H - SILK - 6, PW - 80, 190, op=0.85, res=9)
        mist(d, t, 0, H - SILK - 200, PW, 200, 0.55)
        # 题字：两列，右列「一行代码」，左列「没写」往下错半格多
        fs = 200
        xr = PW - 120
        vtext(d, xr, 112, "一行代码", "brush", fs, t["ink"], 1e9, track=0.03, cls="fade", start=0.9, step=0)
        x2 = xr - fs * 1.4
        _, _, h2 = vtext(d, x2, 112 + fs * 1.55, "没写", "brush", fs, t["ink"], 1e9, track=0.03, cls="fade", start=1.15)
        # 名章：盖在「写」字左下
        seal(d, t, x2 - fs - 30, 112 + fs * 1.55 + h2 - 4, "decli", w=124, rot=-3, cls="stamp", extra=delay(2.0))
        # 引言：朱丝栏里竖写，一句一起头
        lx = x2 - fs - 120
        lw = ruled(d, t, lx, 150, LEDE, 32, 60, 560, t["ink2"], cls="fade", start=1.25, emph=("人出判断", t["red"]))
        # 账：最左
        ledger(d, t, lx - lw - 96, 150, 28, 132, 150)
        d.add("</g>")
        # 右头：包首的锦、题签、卷轴
        silk(d, t, PW, 0, 30, H)
        slip(d, t, PW + 2, 120, 26, 340)
        roller(d, t, W - 34, 0, H, 34, "r")
        return d
    W, H = MW, 1360
    PW = W - 34
    d = doc(W, H, title)
    cid = d.uid("un")
    d.deff(f'<clipPath id="{cid}"><rect class="unroll" x="0" y="0" width="{PW}" height="{H}"/></clipPath>')
    d.add(f'<g clip-path="url(#{cid})">')
    frame(d, t, PW, H)
    ranges_strip(d, t, 20, H - SILK - 4, PW - 40, 130, op=0.85, res=7)
    mist(d, t, 0, H - SILK - 140, PW, 140, 0.55)
    fs = 116
    xr = PW - 44
    vtext(d, xr, 70, "一行代码", "brush", fs, t["ink"], 1e9, track=0.03, cls="fade", start=0.9, step=0)
    x2 = xr - fs * 1.4
    _, _, h2 = vtext(d, x2, 70 + fs * 1.55, "没写", "brush", fs, t["ink"], 1e9, track=0.03, cls="fade", start=1.15)
    seal(d, t, x2 - fs - 18, 70 + fs * 1.55 + h2 - 2, "decli", w=78, rot=-3, cls="stamp", extra=delay(2.0))
    ledger(d, t, x2 - fs - 40, 84, 22, 92, 104)
    ruled(d, t, PW - 44, 712, LEDE, 26, 52, 440, t["ink2"], cls="fade", start=1.25, emph=("人出判断", t["red"]))
    d.add("</g>")
    silk(d, t, PW, 0, 14, H)
    roller(d, t, W - 22, 0, H, 22, "r")
    return d


def slip(d, t, x, y, w, h):
    """题签：包首锦面上贴的一条签，写着卷名"""
    d.add(f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="{t["mat"]}"/>'
          f'<rect x="{num(x + 2.5)}" y="{num(y + 2.5)}" width="{num(w - 5)}" height="{num(h - 5)}" fill="none" stroke="{t["ink"]}" stroke-opacity=".35"/>')
    vtext(d, x + w / 2 + 10, y + 18, "作品长卷", "brush", 20, t["ink"], h - 30, track=0.3)


# ═══════════════════════════════════════════════════════════════════
#  千里江山：八万行，一卷看完
# ═══════════════════════════════════════════════════════════════════

def range_panel(t, mobile=False):
    title = (f"八万行代码的山水：十五个仓库的全部代码一字排开，山的轮廓是每一行代码的长度，山的高低是代码量。"
             f"共 {TOTAL:,} 行，最高的是信风 Tradewind（{loc('ftms'):,} 行），最小的是 TabInfoCopy（{loc('tabinfocopy')} 行）。")
    W = DW if not mobile else MW
    H = 760 if not mobile else 700
    d = doc(W, H, title)
    frame(d, t, W, H)
    if not mobile:
        base, hmax, x0, width, ps = H - SILK - 70, 400, 50, W - 100, 24
    else:
        base, hmax, x0, width, ps = H - SILK - 64, 300, 16, W - 32, 19
    peaks = ranges_strip(d, t, x0, base, width, hmax)
    mist(d, t, 0, base - 70, W, 80, 0.6)
    d.add(f'<rect x="0" y="{num(base + 10)}" width="{W}" height="{num(H - SILK - base - 10)}" fill="{t["paper"]}" opacity=".6"/>')
    if not mobile:
        # 题字：左上 —— 卷子的这一段最后读到的地方，题在这里像落款
        vtext(d, 236, 66, "八万行代码", "brush", 64, t["ink"], 1e9, track=0.04)
        vblock(d, 154, 76, ["十五个仓库，", f"共{cn(TOTAL)}行"], "song", 24, t["ink2"], 400, col_step=38, track=0.16)
        places(d, t, peaks, ps, x0, x0 + width, 330, zone=290)
        d.text(50, H - SILK - 26, "山的轮廓是每一行代码的长度，一行不少；山的高低跟代码量走（开平方）。从右往左依次是十五件作品。",
               "song", 24, t["ink3"])
        d.text(W - 50, H - SILK - 26, "凑近看下面六段：近处的山就是代码", "song", 24, t["red_t"], anchor="end")
    else:
        vtext(d, 116, 48, "八万行代码", "brush", 50, t["ink"], 1e9, track=0.04)
        _, _, bh = vblock(d, 52, 54, ["十五个仓库，", f"共{cn(TOTAL)}行"], "song", 18, t["ink2"], 400, col_step=26, track=0.14)
        places(d, t, peaks, ps, x0, x0 + width, 330, zone=140)
        d.text(20, H - SILK - 24, "山的轮廓是每一行代码的长度，一行不少。", "song", 21, t["ink3"])
    return d


# ═══════════════════════════════════════════════════════════════════
#  作品：一件一段画心
# ═══════════════════════════════════════════════════════════════════

def link_word(w):
    if w.get("href"):
        return "打开", "↗"
    if w.get("dl"):
        return "下载", "↓"
    return "源码", "↗"


def kind_box(d, t, x, y, w, h, kind, arrow, size):
    """去处：一个竖着的朱红小框，能打开的是实心"""
    solid = kind != "源码"
    d.add(f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="{t["red"] if solid else "none"}" '
          f'stroke="{t["red"] if solid else t["ink"]}" stroke-opacity="{1 if solid else .45}" stroke-width="1.6"/>')
    c = t["paper"] if solid else t["ink"]
    vtext(d, x + w / 2 + size / 2, y + size * 0.55, kind, "song", size, c, 1e9, track=0.3)
    d.text(x + w / 2, y + h - size * 0.5, arrow, "song", size, c, anchor="middle")


def caption(d, t, x_left, x_right, y, slug, size, code_size, mobile=False):
    """图注：左边说这一屏是什么，右边说底下那座山是哪个文件。挤不下就分两行"""
    _, path, start = code_of(slug)
    fname = path.rsplit("/", 1)[-1]
    cap = f"图 · {SHOT_CAP.get(slug, '')}"
    lab = "山 · 画出这一屏的"
    w1 = d.width(cap, "song", size)
    gapw = size * 0.3                     # SVG 会吞掉字串末尾的空格，中西文之间的空隙自己留
    w2 = d.width(lab, "song", size) + gapw + d.width(fname, "code", code_size)
    two = w1 + w2 + size * 3 > x_right - x_left
    d.text(x_left, y, cap, "song", size, t["ink2"], extra=halo(t))
    y2 = y + size * 1.5 if two else y
    d.text(x_right, y2, fname, "code", code_size, t["red_t"], anchor="end", extra=halo(t))
    d.text(x_right - d.width(fname, "code", code_size) - gapw, y2, lab, "song", size, t["ink2"], anchor="end", extra=halo(t))
    return y2


def inscription(d, t, w, i, xr, top, bottom, mobile=False):
    """题字区：作品名（行楷）→ 一句话（宋体，朱笔圈点）→ 印 → 小字的类别和行数 → 去处。从右往左"""
    slug = w["slug"]
    kind, arrow = link_word(w)
    avail = bottom - top
    s = dict(name=118, brief=34, bstep=62, gap=46, seal=92, meta=24, box=(48, 132, 24)) if not mobile else \
        dict(name=80, brief=27, bstep=48, gap=28, seal=66, meta=20, box=(40, 108, 20))
    nfs = min(s["name"], (avail - 10) / vlen(d, w["name"], 1, 0.03, "brush-lat"))
    _, nw, _ = vtext(d, xr, top, w["name"], "brush", nfs, t["ink"], 1e9, track=0.03, lat_stack="brush-lat", cls="fade", start=0.4,
                     outline=halo(t, 6))
    bx = xr - nw - s["gap"]
    cols = BRIEF_COLS.get(slug)
    if not cols or "".join(cols) != w["brief"]:      # 文案改了、换列表没跟上：退回自动折
        cols = [w["brief"]]
    _, bw, _ = vblock(d, bx, top + 8, cols, "song", s["brief"], t["ink"], avail - 10, col_step=s["bstep"], track=0.12,
                      emph=(EMPH.get(slug, ""), t["red"]), cls="fade", start=0.6, outline=halo(t, 6))
    sx = bx - bw - s["gap"] * 1.1
    st = seal_text(slug)
    sw0, _ = seal_size(st, s["seal"] ** 2)
    sw, sh = seal(d, t, sx - (s["seal"] + sw0) / 2, top, st, w=sw0, rot=-1.2 - (i % 3) * 0.8, cls="stamp", extra=delay(1.0))
    sx = sx - (s["seal"] - sw0) / 2
    bw_, bh_, bfs = s["box"]
    by = bottom - bh_
    m, my = s["meta"], top + sh + s["meta"] * 1.5
    cx = sx - sw / 2
    vtext(d, cx + m * 1.35, my, w["cat_zh"], "song", m, t["ink3"], 1e9, track=0.18, outline=halo(t, 5))
    vtext(d, cx - m * 0.35, my, f"代码{cn(loc(slug))}行", "song", m, t["ink3"], (by if not mobile else bottom) - my - m * 0.8,
          col_step=m * 1.5, track=0.12, outline=halo(t, 5))
    # 去处：桌面版压在印下面；手机版题字区左边是空的，放到最左下角，让小字一列写完
    kind_box(d, t, (cx - bw_ / 2) if not mobile else 40, by, bw_, bh_, kind, arrow, bfs)
    return sx - sw


def work(w, t, i, mobile=False):
    slug = w["slug"]
    title = C.alt_work(w) + f" — AI 写了 {loc(slug):,} 行。图下面那座山，是画出这一屏的源代码。"
    if not mobile:
        W, H = DW, 940
        d = doc(W, H, title)
        frame(d, t, W, H)
        base = H - SILK
        far(d, t, slug, -20, base, W + 40, (H - 2 * SILK) * 0.6 * hscale(slug), op=0.75)
        fx, fw = 104, 800
        fy = 70 + (i % 3) * 14
        fh = fw / 1.6 + 12
        cy = caption(d, t, fx - 12, fx + fw + 12, fy + fh + 40, slug, 23, 21)
        near(d, t, slug, fx + fw + 96, base - 2, fw + 180, base - 2 - (cy + 30))
        hang(d, t, slug, fx, fy, fw, t0=0.25)
        caption(d, t, fx - 12, fx + fw + 12, fy + fh + 40, slug, 23, 21)
        mist(d, t, 0, base - 60, W, 60, 0.8)
        inscription(d, t, w, i, W - 92, 86, H - SILK - 84)
        return d
    W = MW
    top, bottom = 58, 58 + 470
    fy = bottom + 56
    fw = W - 2 * 40
    fh = fw / 1.6 + 9
    cap_y = fy + fh + 34
    d = doc(W, 10, title)
    cy = caption(d, t, 31, W - 31, cap_y, slug, 20, 18, mobile=True)
    d.body = []
    H = int(cy + 24 + 230 + SILK)
    d.h = H
    frame(d, t, W, H)
    base = H - SILK
    far(d, t, slug, -10, base, W + 20, 300 * hscale(slug), op=0.75)
    near(d, t, slug, W - 6, base - 2, W - 12, base - 2 - (cy + 24), size=17)
    hang(d, t, slug, 40, fy, fw, mobile=True, t0=0.25)
    caption(d, t, 31, W - 31, cap_y, slug, 20, 18, mobile=True)
    mist(d, t, 0, base - 44, W, 44, 0.8)
    inscription(d, t, w, i, W - 40, top, bottom, mobile=True)
    return d


# ═══════════════════════════════════════════════════════════════════
#  签条：全部十五件，一件一条，每条都是一个链接
# ═══════════════════════════════════════════════════════════════════

def slip_geom(w, k, mobile):
    """一张签条的高度和几条线：(H, 纸顶, 表头高, 纸底, 折好的那句话)"""
    first, last = k == 0, k == C.N - 1
    if not mobile:
        bl = kit.wrap(w["brief"], STACKS["song"], 28, 740)
        body = 116 + (len(bl) - 1) * 42
    else:
        bl = kit.wrap(w["brief"], STACKS["song"], 25, MW - 128)
        body = 56 + 44 + len(bl) * 38 + 30
    head = (64 if not mobile else 56) if first else 0
    top = (SILK if first else 0) + head
    H = int(top + body + (SILK if last else 0))
    return H, top, head, (H - SILK if last else H), bl


def mixed(d, x, y, text, size, color, lat_scale=1.08):
    """作品名横排：汉字行楷，西文换 Instrument Serif 斜体（行楷字库里的西文是凑数的）"""
    for run in re.findall(r"[A-Za-z][A-Za-z0-9]*(?: [A-Za-z][A-Za-z0-9]*)*|[^A-Za-z]+", text):
        if re.match(r"[A-Za-z]", run):
            x += d.text(x, y, run, "brush-lat", size * lat_scale, color) + size * 0.12
        else:
            x += d.text(x, y, run.rstrip(), "brush", size, color) + (size * 0.3 if run.endswith(" ") else 0)
    return x


def slip_row(w, t, k, mobile=False):
    slug = w["slug"]
    kind, arrow = link_word(w)
    title = C.alt_work(w) + f" — AI 写了 {loc(slug):,} 行"
    first, last = k == 0, k == C.N - 1
    W = DW if not mobile else MW
    H, top, head, bot, bl = slip_geom(w, k, mobile)
    oy = sum(slip_geom(C.WORKS[j], j, mobile)[0] for j in range(k))
    d = doc(W, H, title)
    paper(d, t, 0, top - head, W, bot - top + head, seed=4, vignette=False, oy=oy)
    if first:
        silk(d, t, 0, 0, W, SILK)
        hy = SILK + head - (22 if not mobile else 18)
        hs = 23 if not mobile else 20
        hx = 56 if not mobile else 26
        hw = d.text(hx, hy, f"签条　全部{cn(C.N)}件，点一条就去那一件", "song", hs, t["ink3"])
        d.add(f'<path d="M{num(hx + hw + 18)} {num(hy - hs * 0.32)}H{num(W - hx)}" stroke="{t["ink"]}" stroke-opacity=".18" stroke-width="1.2"/>')
    if last:
        silk(d, t, 0, H - SILK, W, SILK)
    if not first:
        d.add(f'<path d="M48 {num(top + 0.75)}H{num(W - 48)}" stroke="{t["ink"]}" stroke-opacity=".14" stroke-width="1.5" stroke-dasharray="2 7"/>')
    st = seal_text(slug)
    link_c = t["red_t"] if kind != "源码" else t["ink2"]
    if not mobile:
        y = top + 66
        sw, sh = seal_size(st, 56 ** 2)
        seal(d, t, 104 - sw / 2, y - 16 - sh / 2, st, w=sw, rot=0)      # 印的中线对齐名字那一行
        mixed(d, 160, y + 2, w["name"], 46, t["ink"])
        for j, ln in enumerate(bl):
            d.text(620, y + j * 42, ln, "song", 28, t["ink2"])
        d.text(1376, y - 4, w["cat_zh"], "song", 23, t["ink3"])
        d.text(1376, y + 30, f"代码{cn(loc(slug))}行", "song", 21, t["ink3"])
        d.text(W - 56, y, f"{kind} {arrow}", "song", 26, link_c, anchor="end")
        return d
    y = top + 56
    sw, sh = seal_size(st, 46 ** 2)
    seal(d, t, 46 - sw / 2, y - 13 - sh / 2, st, w=sw, rot=0)
    mixed(d, 92, y, w["name"], 38, t["ink"])
    d.text(W - 26, y - 4, f"{kind} {arrow}", "song", 22, link_c, anchor="end")
    for j, ln in enumerate(bl):
        d.text(92, y + 44 + j * 38, ln, "song", 25, t["ink2"])
    d.text(92, y + 44 + len(bl) * 38 + 4, f"{w['cat_zh']} · 代码{cn(loc(slug))}行", "song", 20, t["ink3"])
    return d


# ═══════════════════════════════════════════════════════════════════
#  题跋（卷尾）
# ═══════════════════════════════════════════════════════════════════

# 题跋：一段一段，每段里一句一起头（竖排的列在哪里断，是排的人定的）
COLO = [
    [f"卷中山水，是 AI 写下的{cn(TOTAL)}行代码：", "近处的山就是代码本身，竖排着灌进山形里；", "远山的轮廓，是每个仓库全部代码的行长，", "一行不少。"],
    [f"卷上{cn(C.N)}方朱印，是我盖的。", "一件作品一方，验过了才盖。"],
    ["我只做三件事：", "提出问题，想清楚它替谁、解决什么；", "选择方案，在 AI 给的几条路里拍板；", "验收结果，测过、用过，才算做完。",
     "其余的一切，交给 AI。"],
    ["这一卷也一样：", "版式、山和印，还有生成它的代码，", "都出自 AI。我选了方向，验了收。"],
]
COLO_TEXT = "".join("".join(p) for p in COLO)


def seal_book(d, t, gx, gy, cell, row, sh2, lab, mobile=False):
    """印谱：十五方印排成一页，每方底下注上作品名"""
    for k, w in enumerate(C.WORKS):
        c, r = k % 5, k // 5
        cx, cy = gx + c * cell + cell / 2, gy + r * row
        s = seal_text(w["slug"])
        sh = sh2 if len(s) == 2 else (sh2 * 0.84 if not re.fullmatch(r"[A-Za-z ]+", s) else sh2 * 0.8)
        sw = seal_box(s)[0] / seal_box(s)[1] * sh
        seal(d, t, cx - sw / 2, cy + (sh2 - sh) / 2, s, h=sh, rot=((k * 37) % 7 - 3) * 0.5,
             cls="" if mobile else "stamp", extra="" if mobile else delay(0.6 + k * 0.05))
        d.text(cx, cy + sh2 + lab * 1.5, place(w["slug"]), "song", lab, t["ink3"], anchor="middle")


def colophon(t, mobile=False):
    title = "题跋：" + COLO_TEXT + " 作品集：decli.github.io"
    k_ = kuan()
    if not mobile:
        W, H = DW, 900
        d = doc(W, H, title)
        frame(d, t, W, H, x=34)
        # 印谱在左，题跋在右；字号从大往小试，直到右边的字不压到印谱
        gx, gy, cell = 80, 104, 120
        book_r = gx + 5 * cell
        xr = W - 100
        for fs, step, mh in ((28, 50, 640), (27, 47, 650), (26, 45, 660), (25, 43, 670), (24, 41, 680)):
            cols = sum(len(vcolumns(d, ln, fs, mh, 0.14)) for p in COLO for ln in p)
            left = xr - 84 - 56 - cols * step - (len(COLO) - 1) * (step * 0.6) - step - 70
            if left > book_r + 30:
                break
        vtext(d, xr, 88, "题跋", "brush", 84, t["ink"], 1e9, track=0.1)
        x = xr - 84 - 56
        top = 96
        for k, para in enumerate(COLO):
            _, wdt, _ = vblock(d, x, top, para, "song", fs, t["ink2"] if k != 1 else t["ink"], mh, col_step=step, track=0.14,
                               emph=("验过了才盖", t["red"]) if k == 1 else None)
            x -= wdt + step * 1.6 - fs
        # 款：年月 + 名字，落在最后一列的左边、靠下；底下压名章
        kt = f"{k_} decli 识"
        kh = vlen(d, kt, fs, 0.2)
        ky = top + mh - kh - 110
        vtext(d, x - step * 0.2, ky, kt, "song", fs, t["ink"], 1e9, track=0.2)
        seal(d, t, x - step * 0.2 - fs / 2 - 32, ky + kh + 22, "decli", w=64, rot=-2.5, cls="stamp", extra=delay(0.4))
        seal_book(d, t, gx, gy, cell, 172, 62, 21)
        d.text(gx + 10, gy + 3 * 172 + 12, f"印谱　{cn(C.N)}方，一件作品一方", "song", 21, t["ink3"])
        d.text(gx + 10, H - SILK - 92, "© 2026 decli · 作品集 decli.github.io ↗", "song", 24, t["ink2"])
        d.text(gx + 10, H - SILK - 52, "字：马善政楷书、思源宋体、Instrument Serif、Geist Mono，都是 SIL OFL 1.1，按图切字嵌入", "song", 22, t["ink3"])
        roller(d, t, 0, 0, H, 34, "l")
        return d
    W = MW
    paras = COLO[:3]
    H = 1450
    d = doc(W, H, title)
    frame(d, t, W, H, x=22)
    xr = W - 34
    vtext(d, xr, 60, "题跋", "brush", 60, t["ink"], 1e9, track=0.1)
    x = xr - 60 - 30
    for k, para in enumerate(paras):
        # 手机上栏数紧，一段连着排，自动折
        _, wdt, _ = vtext(d, x, 64, "".join(para), "song", 23, t["ink2"] if k != 1 else t["ink"], 640, col_step=40, track=0.12,
                          emph=("验过了才盖", t["red"]) if k == 1 else None)
        x -= wdt + 34
    kt = f"{k_} decli 识"
    kh = vlen(d, kt, 22, 0.2)
    ky = 64 + 640 - kh - 70
    vtext(d, x - 4, ky, kt, "song", 22, t["ink"], 1e9, track=0.2)
    seal(d, t, x - 4 - 11 - 24, ky + kh + 16, "decli", w=48, rot=-2.5)
    seal_book(d, t, 46, 800, 112, 152, 54, 18, mobile=True)
    d.text(52, H - SILK - 76, "© 2026 decli · decli.github.io ↗", "song", 22, t["ink2"])
    d.text(52, H - SILK - 40, "字：马善政楷书、思源宋体、Instrument Serif、Geist Mono", "song", 20, t["ink3"])
    roller(d, t, 0, 0, H, 22, "l")
    return d


# ═══════════════════════════════════════════════════════════════════
#  生成
# ═══════════════════════════════════════════════════════════════════

def build(out: pathlib.Path, prefix="assets/"):
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for f in assets.glob("*.svg"):
        f.unlink()
    for f in (HERE / "code").glob("*.txt"):     # 只有上版面的六件用得到代码摘录
        if f.stem not in FEATURED:
            f.unlink()
    sizes = {}

    def emit(name, fn):
        for mode, t in T.items():
            for dev in ("d", "m"):
                svg = fn(t, mobile=dev == "m").render()
                sizes[f"{name}-{dev}-{mode}"] = kit.write(assets, f"{name}-{dev}-{mode}", svg)

    emit("hero", hero)
    emit("range", range_panel)
    for i, s in enumerate(FEATURED):
        emit(f"work-{s}", lambda t, mobile, s=s, i=i: work(C.BY[s], t, i, mobile=mobile))
    for k, w in enumerate(C.WORKS):
        emit(f"slip-{w['slug']}", lambda t, mobile, w=w, k=k: slip_row(w, t, k, mobile=mobile))
    emit("colophon", colophon)
    kit.save_seg()

    def P(base, alt, href):
        return kit.picture(base, alt, "100%", href, prefix=prefix, align="top")

    pics = [P("hero", f"decli 作品长卷 · 引首：一行代码没写。{C.HEAD_A}" + "".join(C.LEDE) + f" 我写的代码〇行，AI 写的 {TOTAL:,} 行。", C.SITE),
            P("range", f"八万行代码的山水：十五个仓库的全部代码一字排开，共 {TOTAL:,} 行。山的轮廓是每一行代码的长度，山的高低是代码量。", C.SITE)]
    pics += [P(f"work-{s}", C.alt_work(C.BY[s]) + f" — AI 写了 {loc(s):,} 行", C.BY[s]["link"]) for s in FEATURED]
    pics += [P(f"slip-{w['slug']}", C.alt_work(w), w["link"]) for w in C.WORKS]
    pics += [P("colophon", "题跋：" + COLO_TEXT + " 作品集 decli.github.io", C.SITE)]
    md = ["<!-- 由 studio/scroll.py 生成，别手改。改文案改 build.py 的数据，再跑 python3 studio/build.py --home scroll -->", "",
          "<!-- 整卷放在同一个 <p> 里、每张图 align=top：图和图之间不留行距缝，从上到下是一张纸 -->",
          "<p>" + "".join(pics) + "</p>", ""]
    (out / "README.md").write_text("\n".join(md))
    tot = {}
    for k, v in sizes.items():
        key = "-".join(k.split("-")[-2:])
        tot[key] = tot.get(key, 0) + v
    big = sorted(sizes.items(), key=lambda kv: -kv[1])[:5]
    print("  一页加载：" + "  ".join(f"{k} {v / 1024:.0f} KB" for k, v in tot.items()))
    print("  最大的几张：" + "  ".join(f"{k} {v / 1024:.0f} KB" for k, v in big))


if __name__ == "__main__":
    build(kit.ROOT if "--home" in sys.argv else kit.ROOT / "styles" / "scroll")
