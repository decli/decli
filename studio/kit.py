"""
studio/kit.py —— 两套新主页共用的排版工具箱。

跟旧 build.py 最大的不同：字体是嵌进每张 SVG 里的，所以字宽不用再估 ——
用 fontTools 直接读字体的字宽表，量出来的就是浏览器画出来的。
于是右对齐、居中、折行、「接在一段字后面的小标签」都能做到像素级准确。

字体从哪来：
  1. 先找原始字体（FONT_SRC 里的路径，开发机上才有）——量字、切字都用它；
  2. 找不到就用仓库里切好的母版 studio/fonts/*.woff2（只含本页用得到的字）。
  改了文案、出现母版里没有的字时，build 会报错，提示带上原始字体重切一次母版：
      python3 studio/build.py --masters --fontsrc <原始字体目录>

每张 SVG 只嵌它自己用到的那几十个字：一张作品行 10～30 KB，首屏 60 KB 上下。
同一张图的亮 / 暗两版用字一样，切一次复用。
"""

from __future__ import annotations

import base64
import hashlib
import html
import io
import os
import pathlib
import re
import sys

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTERS = ROOT / "studio" / "fonts"

NOTO = "/usr/share/fonts/opentype/noto/"
FONTSRC = pathlib.Path(os.environ.get("FONTSRC", "/home/claude/fontsrc"))  # 原始字体目录；没有就用 studio/fonts/ 里的母版

# key → (原始文件, TTC 里的序号)。全部 SIL OFL 1.1，允许子集化后嵌入。
FONT_SRC = {
    "instr":    (FONTSRC / "InstrumentSerif-Regular.woff2", None),
    "instr-it": (FONTSRC / "InstrumentSerif-Italic.woff2", None),
    "geist":    (FONTSRC / "Geist-Regular.ttf", None),
    "geist-m":  (FONTSRC / "Geist-Medium.ttf", None),
    "geist-sb": (FONTSRC / "Geist-SemiBold.ttf", None),
    "geist-b":  (FONTSRC / "Geist-Bold.ttf", None),
    "mono":     (FONTSRC / "GeistMono-Regular.ttf", None),
    "mono-m":   (FONTSRC / "GeistMono-Medium.ttf", None),
    "serif-sc-r":  (pathlib.Path(NOTO + "NotoSerifCJK-Regular.ttc"), 2),
    "serif-sc-sb": (pathlib.Path(NOTO + "NotoSerifCJK-SemiBold.ttc"), 2),
    "serif-sc-b":  (pathlib.Path(NOTO + "NotoSerifCJK-Bold.ttc"), 2),
    "serif-sc-k":  (pathlib.Path(NOTO + "NotoSerifCJK-Black.ttc"), 2),
    "sans-sc":     (pathlib.Path(NOTO + "NotoSansCJK-Regular.ttc"), 2),
    "sans-sc-m":   (pathlib.Path(NOTO + "NotoSansCJK-Medium.ttc"), 2),
    "sans-sc-b":   (pathlib.Path(NOTO + "NotoSansCJK-Bold.ttc"), 2),
    "sans-sc-k":   (pathlib.Path(NOTO + "NotoSansCJK-Black.ttc"), 2),
    # 「长卷」用：马善政楷书（毛笔字，只切标题那几十个字）
    "brush":       (FONTSRC / "MaShanZheng-Regular.ttf", None),
}
LICENSE_NOTE = {
    "instr": "Instrument Serif — SIL OFL 1.1",
    "geist": "Geist / Geist Mono — SIL OFL 1.1",
    "noto": "Noto Serif / Sans CJK (思源宋体 / 黑体) — SIL OFL 1.1",
    "brush": "Ma Shan Zheng (马善政楷书) — SIL OFL 1.1",
}

SYS_SANS = ("-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',"
            "'Noto Sans SC','Noto Sans CJK SC',sans-serif")
SYS_SERIF = "'Songti SC','STSong','Noto Serif SC','Noto Serif CJK SC',serif"
SYS_MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"


class Face:
    """一个字体文件：量字宽、记下用过哪些字。"""

    def __init__(self, key):
        self.key = key
        self.used: set[str] = set()
        src, num = FONT_SRC[key]
        self.from_master = not src.exists()
        path = MASTERS / f"{key}.woff2" if self.from_master else src
        if not path.exists():
            sys.exit(f"缺字体 {key}：既没有原始字体 {src}，也没有母版 {path}")
        self.path = path
        self.font = TTFont(path, fontNumber=num if (num is not None and not self.from_master) else -1, lazy=True)
        self.upm = self.font["head"].unitsPerEm
        self.cmap = self.font.getBestCmap()
        self.hmtx = self.font["hmtx"].metrics
        os2 = self.font["OS/2"]
        self.asc = os2.sTypoAscender / self.upm
        self.desc = -os2.sTypoDescender / self.upm
        self.cap = getattr(os2, "sCapHeight", 0) / self.upm or 0.7
        self.xh = getattr(os2, "sxHeight", 0) / self.upm or 0.5
        self._master_bytes = None

    def has(self, ch):
        return ord(ch) in self.cmap

    def adv(self, ch):
        g = self.cmap.get(ord(ch))
        return self.hmtx[g][0] / self.upm if g else 1.0

    def glyph_path(self, ch, size, x=0.0, y=0.0):
        """把一个字形转成 SVG path（y 向下）。拿来做遮罩、做超大字。"""
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.transformPen import TransformPen
        gs = self.font.getGlyphSet()
        g = self.cmap[ord(ch)]
        pen = SVGPathPen(gs)
        s = size / self.upm
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, y)))
        return pen.getCommands()

    # ── 切字 ──
    def master_bytes(self):
        if self._master_bytes is None:
            self._master_bytes = self.path.read_bytes()
        return self._master_bytes


_FACES: dict[str, Face] = {}


def face(key) -> Face:
    if key not in _FACES:
        _FACES[key] = Face(key)
    return _FACES[key]


# 一个 CSS 字体栈 = 按顺序试的几个 Face：西文先用西文字体，中文落到思源。浏览器逐字回退，跟这里一致。
CJK_PREFER = set("—")


class Stack:
    def __init__(self, keys, fallback):
        self.keys = keys
        self.fallback = fallback

    def resolve(self, ch):
        if ch in CJK_PREFER:            # 中文里的破折号要用中文字体的：两个连成一条，在字身中间，不是西文那种短横
            for k in self.keys:
                if "-sc" in k and face(k).has(ch):
                    return face(k)
        for k in self.keys:
            f = face(k)
            if f.has(ch):
                return f
        if ch.strip() == "":
            return face(self.keys[0])
        # 母版只含用过的字：新文案里的生字落到这里，图上会变成豆腐块或系统字体 —— 停下来，提示重切母版
        if any(face(k).from_master for k in self.keys):
            sys.exit(f"字体母版里没有「{ch}」（{' / '.join(self.keys)}）。带上原始字体重切一次："
                     "FONTSRC=<原始字体目录> python3 studio/build.py --home zero --masters（中文字体见 studio/README.md）")
        # 原始字体里都没有这个字：落到最后一个
        return face(self.keys[-1])

    def css(self):
        return ",".join(f"'{fam(k)}'" for k in self.keys) + "," + self.fallback


def fam(key):
    return "x" + key.replace("-", "")


HALT = set("，。、；：！？「」『』（）《》【】“”‘’")


def ink(s):
    """排出来的样子：中文的「——」换成一个整的两字线 ⸺（思源字体里两个 U+2014 之间有缝，⸺ 是连着的一条）。"""
    return s.replace("——", "⸺")


def measure(s, stack: Stack, size, track=0.0, halt=False):
    """量一串字的宽度（不含最后一个字后面的字距）。track 以 em 计。
    halt=True 时中文标点按半宽算 —— 对应渲染时打开 OpenType 的 halt 特性。"""
    s = ink(s)
    w = 0.0
    for ch in s:
        f = stack.resolve(ch)
        a = f.adv(ch)
        if halt and ch in HALT and a >= 0.9:
            a = 0.5
        w += a * size + track * size
    return w - (track * size if s else 0)


# ── 折行 ──
# 中文不按字折，按词折：开发机上用 jieba 分词，分出来的结果缓存进 studio/seg.json，
# 这样没装 jieba 的机器上 build 出来的折行也一模一样。缓存里没有的新句子退回按字折。
NO_START = set("，。、；：！？）」』》”’,.;:!?)%·…—⸺")
NO_END = set("「『（《“‘(")
SEG_CACHE = ROOT / "studio" / "seg.json"
_seg = None
_seg_dirty = False


def _jieba():
    try:
        sys.path.insert(0, "/home/claude/vendor")
        import logging
        import warnings
        warnings.filterwarnings("ignore")
        import jieba  # noqa
        jieba.setLogLevel(logging.ERROR)
        return jieba
    except Exception:
        return None


# 分词词典里没有、但不能拆开的词
WORDS = ["提出问题", "选择方案", "验收结果", "十二个", "玩意儿", "全链路", "增长系统", "取件码", "示意图", "公众号",
         "出口国家", "归属地", "废纸篓", "跑测试", "写代码", "修 bug", "AI 写的", "生成它的", "摆拍", "真图"]


def segment(text):
    global _seg, _seg_dirty
    import json
    if _seg is None:
        _seg = json.loads(SEG_CACHE.read_text()) if SEG_CACHE.exists() else {}
        if _seg.get("__words__") != WORDS and _jieba():   # 词表改过：缓存作废，重新分
            _seg = {"__words__": WORDS}
            _seg_dirty = True
    if text in _seg:
        return _seg[text]
    jb = _jieba()
    if jb:
        for wd in WORDS:
            jb.add_word(wd, freq=200000)
        toks = [t for t in jb.cut(text) if t]
    else:
        toks = re.findall(r"[A-Za-z0-9$%+#@&/_.'’\-]+|\s+|.", text)
    # 「——」是一个符号，不许拆
    out = []
    for tk in toks:
        if tk == "—" and out and out[-1].endswith("—"):
            out[-1] += tk
        else:
            out.append(tk)
    if jb:
        _seg[text] = out
        _seg_dirty = True
    return out


def save_seg():
    import json
    if _seg_dirty and _seg is not None:
        SEG_CACHE.write_text(json.dumps(_seg, ensure_ascii=False, indent=0, sort_keys=True))


def _kind(tok):
    if tok.isspace():
        return "space"
    if all(c in NO_START or c in NO_END or c in "，。、；：！？" for c in tok):
        return "punct"
    if re.match(r"[A-Za-z0-9]", tok):
        return "latin"
    return "cjk"


PROTECT = ["那个 0 和 0 里的光标", "我对 codeless 说的那句话", "版式、配色、动效", "能直接粘贴", "AI Native 时代", "AI Agent", "Docker + CI", "IPv4 / IPv6 与归属地", "GitHub Releases", "UI 交互设计", "修 bug",
           "Chrome 扩展", "一键复制", "到退税", "全部交给 AI", "全部由 AI 完成",
           "19 页", "55 米", "30 秒", "SEO / GEO"]   # 数字跟单位不分行


PARTICLE = "的了么呢吗吧着过地得"
LATIN = r"[A-Za-z0-9$%+#@&/_.'’\-]+"


def wrap(text, stack, size, width, track=0.0, max_lines=None, halt=False):
    """按词折行，避头尾，尽量在标点后折，不留孤字。"""
    toks = segment(text)
    # 粘连：避头的标点粘到前一个词上，避尾的括号粘到后一个词上
    units = []
    for tk in toks:
        if units and (tk[0] in NO_START):
            units[-1] = units[-1] + tk
        elif units and units[-1] and units[-1][-1] in NO_END:
            units[-1] = units[-1] + tk
        else:
            units.append(tk)
    # 短引号整体不拆：「找到买家」
    merged, buf = [], None
    for u in units:
        if buf is not None:
            buf += u
            if "」" in u or "』" in u or len(buf) > 12:
                merged.append(buf)
                buf = None
            continue
        if ("「" in u or "『" in u) and "」" not in u and "』" not in u:
            buf = u
            continue
        merged.append(u)
    if buf is not None:
        merged.append(buf)
    units = merged
    n = len(units)
    W = lambda s_: measure(s_.strip(), stack, size, track, halt)  # noqa: E731
    # 不许拆开的词组：在这些词组中间折行要付很高的代价
    offs = [0]
    for u in units:
        offs.append(offs[-1] + len(u))
    full = "".join(units)
    guarded = []
    for ph in PROTECT:
        k = full.find(ph)
        while k >= 0:
            guarded.append((k, k + len(ph)))
            k = full.find(ph, k + 1)
    INF = float("inf")
    best = [INF] * (n + 1)
    prev = [0] * (n + 1)
    best[0] = 0.0
    for j in range(1, n + 1):
        for i in range(j - 1, -1, -1):
            line = "".join(units[i:j])
            w = W(line)
            if w > width and j - i > 1:
                break
            last = j == n
            slack = max(0.0, width - w)
            cost = 10.0
            if not last:
                cost += (slack / width) ** 2 * 100
                k = _kind(units[j - 1].rstrip()[-1:] if units[j - 1].strip() else " ")
                endc = units[j - 1].rstrip()[-1:] if units[j - 1].strip() else " "
                rest = "".join(units[j:]).lstrip()
                nxt = rest[:1]
                lat = lambda c: bool(re.match(r"[A-Za-z0-9]", c))  # noqa: E731
                if endc in "。！？—":         # 句号、破折号处折最自然
                    cost -= 6
                elif endc in "，、；：）」』》—…":
                    pass
                elif lat(endc) and lat(nxt):
                    cost += 2
                elif lat(endc) or lat(nxt):
                    cost += 14
                else:
                    cost += 40
                if nxt and nxt in "的了么呢吗吧着过地得":
                    cost += 40
                if endc and endc in "到从把在和与跟给对向被让为将由":
                    cost += 30
                if any(a < offs[j] < b for a, b in guarded):
                    cost += 200
            else:
                vis = len(re.sub(r"[\s，。、；：！？」』）]", "", line))
                if j - i < n and (vis < 4 or re.fullmatch(LATIN + r"[，。！？]?", line.strip())):
                    cost += 400       # 末行不留孤字，也不留一个孤零零的西文词（「HTML。」）
                elif w < width * 0.2 and best[i] > 0:
                    cost += 60
            if best[i] + cost < best[j]:
                best[j] = best[i] + cost
                prev[j] = i
    lines = []
    j = n
    while j > 0:
        i = prev[j]
        lines.append("".join(units[i:j]).strip())
        j = i
    lines.reverse()
    # 单个词比整行还宽：按字硬折
    out = []
    for ln in lines:
        while W(ln) > width and len(ln) > 1:
            k = len(ln)
            while k > 1 and W(ln[:k]) > width:
                k -= 1
            out.append(ln[:k])
            ln = ln[k:]
        out.append(ln)
    lines = out
    if max_lines and len(lines) > max_lines:
        keep = lines[:max_lines]
        last = keep[-1]
        while last and measure(last + "…", stack, size, track, halt) > width:
            last = last[:-1]
        keep[-1] = last.rstrip("，、；：。 ") + "…"
        lines = keep
    return lines


def justify(text, stack, size, width, track=0.0, halt=False):
    """齐行段落的折行：每行尽量填满（行尾空出来的会被 textLength 摊到字距里，空得越多越难看），
    中文字之间都能折，但词中间折、「的」「了」打头、拆开固定词组都要付代价 ——
    宁可多一行，也不让「的，」「了——」这种东西站在行首。"""
    units = segment(text)
    atoms, word_end = [], []
    for u in units:
        parts = re.findall(LATIN + r"|\s+|.", u)
        for k, p in enumerate(parts):
            last = k == len(parts) - 1
            if atoms and (p[0] in NO_START or (atoms[-1] and atoms[-1][-1] in NO_END)):
                atoms[-1] += p
                word_end[-1] = last
            else:
                atoms.append(p)
                word_end.append(last)
    n = len(atoms)
    offs = [0]
    for a in atoms:
        offs.append(offs[-1] + len(a))
    full = "".join(atoms)
    guarded = []
    for ph in PROTECT:
        k = full.find(ph)
        while k >= 0:
            guarded.append((k, k + len(ph)))
            k = full.find(ph, k + 1)
    lat = lambda c: bool(re.match(r"[A-Za-z0-9]", c))  # noqa: E731
    INF = float("inf")
    best, prev = [INF] * (n + 1), [0] * (n + 1)
    best[0] = 0.0
    for j in range(1, n + 1):
        for i in range(j - 1, -1, -1):
            line = "".join(atoms[i:j]).strip()
            w = measure(line, stack, size, track, halt)
            if w > width and j - i > 1:
                break
            cost = 10.0
            if j < n:
                cost += ((width - w) / width) ** 2 * 3000
                endc = line[-1:] or " "
                nxt = "".join(atoms[j:]).lstrip()[:1]
                if endc in "，。、；：！？）」』》—⸺…":
                    pass
                elif atoms[j].isspace() or atoms[j - 1].isspace():
                    pass
                elif lat(endc) or lat(nxt):
                    cost += 4
                elif word_end[j - 1]:
                    cost += 8
                else:
                    cost += 40
                if nxt and nxt in PARTICLE:
                    cost += 120
                if endc in "到从把在和与跟给对向被让为将由":
                    cost += 20
                if any(a < offs[j] < b for a, b in guarded):
                    cost += 200
                head = full[:offs[j]]
                if head.count("「") > head.count("」"):      # 短引语不拆
                    cost += 60
            else:
                vis = len(re.sub(r"[\s，。、；：！？」』）]", "", line))
                if n > j - i and vis < 4:
                    cost += 400
            if best[i] + cost < best[j]:
                best[j], prev[j] = best[i] + cost, i
    out, j = [], n
    while j > 0:
        i = prev[j]
        out.append("".join(atoms[i:j]).strip())
        j = i
    return out[::-1]


def fill(text, stack, size, width, track=0.0):
    """正文齐行用：按字填满一行（中文本来就可以在任意两个字之间折），
    但西文单词不拆、避头尾、最后一行不少于 2 个字。配合 textLength 两端对齐。"""
    toks = re.findall(r"[A-Za-z0-9$%+#@&/_.'’\-]+|\s+|.", text)
    lines, cur = [], ""
    for tk in toks:
        trial = cur + tk
        if measure(trial.rstrip(), stack, size, track) <= width or not cur.strip():
            cur = trial
            continue
        if tk[0] in NO_START:          # 标点不放行首：把前一个字（或整个西文词）带下去
            m = re.search(r"[A-Za-z0-9$%+#@&/_.'’\-]+$", cur)
            k = len(m.group()) if m else 1
            cur, tk = cur[:-k], cur[-k:] + tk
        while cur and cur[-1] in NO_END:  # 开括号不放行尾
            tk = cur[-1] + tk
            cur = cur[:-1]
        lines.append(cur.rstrip())
        cur = tk.lstrip()
    if cur.strip():
        lines.append(cur.rstrip())
    while len(lines) > 1 and len(lines[-1].strip("，。、；：！？」")) < 4 and len(lines[-2]) > 8:
        lines[-1] = lines[-2][-1] + lines[-1]
        lines[-2] = lines[-2][:-1]
    return lines


def esc(s):
    return html.escape(str(s), quote=True)


def num(v):
    """数字输出得短一点，SVG 小一点。"""
    if isinstance(v, float):
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        return s if s not in ("-0", "") else "0"
    return str(v)


# ── 子集缓存：同样的字表只切一次 ──
_SUBSET_CACHE: dict[tuple, bytes] = {}


def cut(key, chars):
    chars = "".join(sorted(set(chars)))
    ck = (key, chars)
    if ck in _SUBSET_CACHE:
        return _SUBSET_CACHE[ck]
    f = face(key)
    src, num_ = FONT_SRC[key]
    # recalcTimestamp=False：同样的字切出来的字节完全一样，重新生成不会让没改的图也冒出 diff
    if f.from_master:
        font = TTFont(io.BytesIO(f.master_bytes()), recalcTimestamp=False)
    else:
        font = TTFont(src, fontNumber=num_ if num_ is not None else -1, recalcTimestamp=False)
    opts = subset.Options()
    opts.layout_features = ["kern", "liga", "calt", "tnum", "palt", "halt", "case", "ss01", "zero"]
    opts.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]
    opts.hinting = False
    opts.desubroutinize = True
    opts.notdef_outline = True
    opts.flavor = "woff2"
    s = subset.Subsetter(opts)
    s.populate(text=chars)
    s.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    data = buf.getvalue()
    _SUBSET_CACHE[ck] = data
    return data


# ═══════════════════════════════════════════════════════════════════
#  SVG 文档
# ═══════════════════════════════════════════════════════════════════

class Doc:
    """一张 SVG。往里加元素，最后 render() 时再按用到的字切字体、嵌进去。"""

    def __init__(self, w, h, title, stacks: dict[str, Stack]):
        self.w, self.h, self.title = w, h, title
        self.stacks = stacks
        self.defs: list[str] = []
        self.body: list[str] = []
        self.css: list[str] = []
        self.used: dict[str, set] = {}
        self._uid = 0

    def uid(self, p="u"):
        self._uid += 1
        return f"{p}{self._uid}"

    def add(self, s):
        self.body.append(s)
        return self

    def deff(self, s):
        self.defs.append(s)

    def style(self, s):
        self.css.append(s)

    def note(self, stack_name, s):
        st = self.stacks[stack_name]
        for ch in s:
            f = st.resolve(ch)
            self.used.setdefault(f.key, set()).add(ch)
            f.used.add(ch)

    def width(self, s, stack, size, track=0.0, halt=False):
        return measure(s, self.stacks[stack], size, track, halt)

    def wrap(self, s, stack, size, width, track=0.0, max_lines=None, halt=False):
        return wrap(s, self.stacks[stack], size, width, track, max_lines, halt)

    def text(self, x, y, s, stack, size, fill, track=0.0, anchor=None, cls=None, extra="", feat=None,
             opacity=None, halt=False):
        """单行字。track 以 em 计。返回字宽，方便接着往后排。"""
        s = ink(s)
        self.note(stack, s)
        a = [f'x="{num(x)}"', f'y="{num(y)}"', f'font-size="{num(size)}"', f'fill="{fill}"',
             f'font-family="{esc(self.stacks[stack].css())}"']
        if track:
            a.append(f'letter-spacing="{num(track * size)}"')
        if anchor:
            a.append(f'text-anchor="{anchor}"')
        if halt:
            cls = (cls + " " if cls else "") + "halt"
            if ".halt{" not in "".join(self.css):
                self.css.append('.halt{font-feature-settings:"halt"}')
        if cls:
            a.append(f'class="{cls}"')
        if feat:
            a.append(f"style='font-feature-settings:{feat}'")
        if opacity is not None:
            a.append(f'opacity="{num(opacity)}"')
        if extra:
            a.append(extra)
        self.body.append(f'<text {" ".join(a)}>{esc(s)}</text>')
        return self.width(s, stack, size, track, halt)

    def spans(self, x, y, parts, size, anchor=None, cls=None, extra=""):
        """一行里混几种字体 / 颜色：parts = [(字, stack, fill[, track])]。"""
        out = []
        for p in parts:
            s, st, fill = ink(p[0]), p[1], p[2]
            tr = p[3] if len(p) > 3 else 0.0
            self.note(st, s)
            ls = f' letter-spacing="{num(tr * size)}"' if tr else ""
            out.append(f'<tspan font-family="{esc(self.stacks[st].css())}" fill="{fill}"{ls}>{esc(s)}</tspan>')
        a = [f'x="{num(x)}"', f'y="{num(y)}"', f'font-size="{num(size)}"']
        if anchor:
            a.append(f'text-anchor="{anchor}"')
        if cls:
            a.append(f'class="{cls}"')
        if extra:
            a.append(extra)
        self.body.append(f'<text {" ".join(a)}>{"".join(out)}</text>')
        return sum(self.width(p[0], p[1], size, p[3] if len(p) > 3 else 0.0) for p in parts)

    def render(self):
        faces = []
        for key in sorted(self.used):
            data = cut(key, self.used[key])
            b64 = base64.b64encode(data).decode()
            faces.append(f"@font-face{{font-family:'{fam(key)}';src:url(data:font/woff2;base64,{b64}) format('woff2');"
                         f"font-display:block}}")
        css = "".join(faces) + (
            "text{font-kerning:normal;font-synthesis:none;text-rendering:geometricPrecision}"
        ) + "".join(self.css) + "@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}"
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        body = "".join(self.body).replace('<image href="', '<image xlink:href="')
        body = re.sub(r'(<image [^>]*?) href="', r'\1 xlink:href="', body)
        defs = re.sub(r'(<image [^>]*?) href="', r'\1 xlink:href="', defs)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{num(self.w)}" height="{num(self.h)}" viewBox="0 0 {num(self.w)} {num(self.h)}" '
            f'role="img" aria-label="{esc(self.title)}">'
            f"<title>{esc(self.title)}</title><style>{css}</style>{defs}{body}</svg>"
        )


# ═══════════════════════════════════════════════════════════════════
#  图片：截图压成 webp 再以 data: 嵌进 SVG
# ═══════════════════════════════════════════════════════════════════

# 作品集仓库的截图目录：默认找跟本仓库并排放着的 decli.github.io，也可以用环境变量 SHOTS 指定
SHOTS = pathlib.Path(os.environ.get("SHOTS", ROOT.parent / "decli.github.io" / "shots"))
if not SHOTS.exists() and pathlib.Path("/home/claude/decli.github.io/shots").exists():
    SHOTS = pathlib.Path("/home/claude/decli.github.io/shots")
SHOT_CACHE = ROOT / "studio" / "shots"
_SIZES = SHOT_CACHE / "sizes.json"


def shot_size(rel):
    """原图尺寸：有原图读原图（顺手记下来），没有就读缓存 —— 没有作品集仓库也能 build。"""
    import json
    sizes = json.loads(_SIZES.read_text()) if _SIZES.exists() else {}
    src = SHOTS / f"{rel}.webp"
    if src.exists():
        from PIL import Image
        wh = list(Image.open(src).size)
        if sizes.get(rel) != wh:
            sizes[rel] = wh
            SHOT_CACHE.mkdir(parents=True, exist_ok=True)
            _SIZES.write_text(json.dumps(sizes, indent=1, sort_keys=True))
        return tuple(wh)
    if rel in sizes:
        return tuple(sizes[rel])
    sys.exit(f"缺截图 {src}（设置环境变量 SHOTS 指向作品集仓库的 shots/ 目录）")


def shot_uri(rel, width, crop=None, quality=74, redact=(), stack=None, tone=None, aspect=None):
    """rel 形如 'ftms/dashboard'。按需打码、裁切、拼接、调色，缩到 width 像素宽，缓存在 studio/shots/ 下。
    redact = [(x0, y0, x1, y1), ...] 按原图比例的框，马赛克掉；
    stack  = [(y0, y1), ...] 只要原图里的这几条横带，上下拼起来（跳过不想露出来的行）；
    tone   = (暗部色, 亮部色) —— 去色后映射到这两个颜色之间（「灰色是 AI 的产出」那套用）。"""
    from PIL import Image, ImageOps
    tag = hashlib.md5(f"{rel}|{width}|{crop}|{quality}|{redact}|{stack}|{tone}|{aspect}".encode()).hexdigest()[:8]
    out = SHOT_CACHE / f"{rel.replace('/', '-')}-{width}-{tag}.webp"
    if not out.exists():
        src = SHOTS / f"{rel}.webp"
        if not src.exists():
            sys.exit(f"缺截图 {src}")
        im = Image.open(src).convert("RGB")
        W0, H0 = im.size
        for bx in redact:
            box = (int(bx[0] * W0), int(bx[1] * H0), int(bx[2] * W0), int(bx[3] * H0))
            region = im.crop(box)
            small = region.resize((max(1, region.size[0] // 18), max(1, region.size[1] // 18)), Image.BILINEAR)
            im.paste(small.resize(region.size, Image.NEAREST), box)
        if stack:
            W, H = im.size
            x0, x1 = (crop[0], crop[2]) if crop else (0, 1)
            parts = [im.crop((int(x0 * W), int(a * H), int(x1 * W), int(b * H))) for a, b in stack]
            out_im = Image.new("RGB", (parts[0].size[0], sum(q.size[1] for q in parts)))
            yy = 0
            for q in parts:
                out_im.paste(q, (0, yy))
                yy += q.size[1]
            im = out_im
        elif crop:  # (x0, y0, x1, y1)，按比例；超出原图的部分用贴边那一圈的底色补（截图本身贴边太紧时留白用）
            W, H = im.size
            box = (round(crop[0] * W), round(crop[1] * H), round(crop[2] * W), round(crop[3] * H))
            if box[0] < 0 or box[1] < 0 or box[2] > W or box[3] > H:
                import statistics
                inner = (max(0, box[0]), max(0, box[1]), min(W, box[2]), min(H, box[3]))
                edge = im.crop((inner[0], inner[1], inner[0] + 6, inner[3])).getdata() if box[0] < 0 else \
                    im.crop((inner[0], inner[1], inner[2], inner[1] + 6)).getdata()
                bg = tuple(int(statistics.median(px[i] for px in edge)) for i in range(3))
                canvas = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), bg)
                canvas.paste(im.crop(inner), (inner[0] - box[0], inner[1] - box[1]))
                im = canvas
            else:
                im = im.crop(box)
        if aspect and abs(im.size[0] / im.size[1] - aspect) > 0.004:
            # 比框扁：底下补一条贴边的底色（裁切线停在界面的空隙上，宁可补也不切进下一行）；比框瘦：左右各补一半
            import statistics
            W1, H1 = im.size
            if W1 / H1 > aspect:
                strip = im.crop((0, H1 - 6, W1, H1)).getdata()
                size_ = (W1, round(W1 / aspect))
                at = (0, 0)
            else:
                strip = list(im.crop((0, 0, 6, H1)).getdata()) + list(im.crop((W1 - 6, 0, W1, H1)).getdata())
                size_ = (round(H1 * aspect), H1)
                at = ((size_[0] - W1) // 2, 0)
            bg = tuple(int(statistics.median(px[i] for px in strip)) for i in range(3))
            canvas = Image.new("RGB", size_, bg)
            canvas.paste(im, at)
            im = canvas
        if tone:
            im = ImageOps.colorize(ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=0.5), black=tone[0], white=tone[1])
        h = round(im.size[1] * width / im.size[0])
        im = im.resize((width, h), Image.LANCZOS)
        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out, "WEBP", quality=quality, method=6)
    data = out.read_bytes()
    from PIL import Image as _I
    w, h = _I.open(out).size
    return "data:image/webp;base64," + base64.b64encode(data).decode(), w, h


def png_uri(path):
    data = pathlib.Path(path).read_bytes()
    mime = "image/png" if str(path).endswith(".png") else "image/svg+xml"
    return f"data:{mime};base64," + base64.b64encode(data).decode()


# ═══════════════════════════════════════════════════════════════════
#  Markdown：一张响应式、跟主题切换的图
# ═══════════════════════════════════════════════════════════════════

def picture(base, alt, width="100%", href=None, mobile=True, prefix="assets/", align=None):
    """base-d-light / base-d-dark / base-m-light / base-m-dark 四张。
    手机版一直用到 1151px：窗口窄于这个宽度时 GitHub 的 README 栏不到 720px，桌面版缩过去正文不到 12px。
    第一个命中的 <source> 生效，所以手机两条写在前面。
    align="top"：行内图顶对齐，图和图之间不留行距缝（「长卷」拼成一整张纸用）。"""
    p = prefix
    src = []
    if mobile:
        src.append(f'<source media="(max-width: 1151px) and (prefers-color-scheme: dark)" srcset="{p}{base}-m-dark.svg">')
        src.append(f'<source media="(max-width: 1151px)" srcset="{p}{base}-m-light.svg">')
    src.append(f'<source media="(prefers-color-scheme: dark)" srcset="{p}{base}-d-dark.svg">')
    w = f' width="{width}"' if width else ""
    a = f' align="{align}"' if align else ""
    img = f'<picture>{"".join(src)}<img alt="{esc(alt)}" src="{p}{base}-d-light.svg"{w}{a}></picture>'
    return f'<a href="{href}">{img}</a>' if href else img


def write(out_dir: pathlib.Path, name, svg: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.svg").write_text(svg)
    return len(svg.encode())


def cut_masters(keys=None):
    """把这次 build 用到的所有字，从原始字体切成母版存进仓库。"""
    MASTERS.mkdir(parents=True, exist_ok=True)
    for key, f in sorted(_FACES.items()):
        if keys and key not in keys:
            continue
        if f.from_master:
            print(f"  · {key}: 没有原始字体，保留旧母版", file=sys.stderr)
            continue
        chars = set(f.used)
        # 西文字体整套 ASCII + 常用标点都留着，改英文文案不用重切
        if not key.startswith(("serif-sc", "sans-sc")):
            chars |= set(chr(c) for c in range(0x20, 0x7F)) | set("·—–…’‘“”→←↗↘✓×№•")
        data = cut(key, "".join(chars))
        (MASTERS / f"{key}.woff2").write_bytes(data)
        print(f"  ✓ 母版 {key}: {len(chars)} 字 {len(data) / 1024:.0f} KB", file=sys.stderr)
