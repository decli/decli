"""
实验风格共用的小工具。数据（WORKS、文案、配色之外的一切）全部从仓库根目录的 build.py 读，
保证作品信息只有一份。

- font_face(): 把 fonts/ 下切好的 woff2 子集嵌进 SVG。SVG 当图片用时拿不到任何外部资源，
  字体只能以 data: 形式塞进去。实测 raw.githubusercontent.com 那条
  「default-src 'none'」的 CSP 挡不住它（CSP 只在 SVG 被当成文档直接打开时生效）。
  浏览器万一不认，font-family 里还有系统字体兜底，字照样能读。
- write_hashed(): 会变的图（比分、状态、封面）文件名里带内容哈希。
  raw.githubusercontent.com 给图片发 max-age=300，同一个地址换了内容，
  访客最多要等五分钟才看得到；换了地址就是当场生效。
"""

import base64
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build as base  # noqa: E402  —— WORKS / CATS / POC / e() / tw() / wrap() ……

REPO = "https://github.com/decli/decli"


def font_face(family, path):
    data = base64.b64encode(pathlib.Path(path).read_bytes()).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{data}) format('woff2')}}"


def font_face_subset(family, path, text):
    """只嵌这一张图真正用到的字。fonts/ 下存的是整套风格可能用到的全部字（几百 KB），
    一张封面只用得到其中几十个。装了 fonttools 就当场再切一刀；没装就整份嵌进去，照样能用。"""
    try:
        import io

        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError:
        return font_face(family, path)
    font = TTFont(path)
    s = subset.Subsetter()
    s.populate(text=text)
    s.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{data}) format('woff2')}}"


def write_hashed(folder, prefix, content):
    """写成 <prefix>-<哈希>.svg，顺手删掉同前缀的旧文件，返回新文件名。"""
    folder = pathlib.Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(content.encode()).hexdigest()[:8]
    name = f"{prefix}-{digest}.svg"
    for old in folder.glob(f"{prefix}-*.svg"):
        if old.name != name:
            old.unlink()
    (folder / name).write_text(content)
    return name


def svg(w, h, title, body, css=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="title">\n<title id="title">{base.e(title)}</title>\n'
        f"<style>{css}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>\n"
        f"{body}\n</svg>\n"
    )


def picture(prefix, name, alt, width=None, href=None, themed=True, attrs=""):
    """跟着 GitHub 明暗主题切换的一张图；prefix 是 assets 目录相对 README 的路径。"""
    w = f' width="{width}"' if width else ""
    if themed:
        img = (
            f'<picture><source media="(prefers-color-scheme: dark)" srcset="{prefix}{name}-dark.svg">'
            f'<img alt="{base.e(alt)}" src="{prefix}{name}-light.svg"{w}{attrs}></picture>'
        )
    else:
        img = f'<img alt="{base.e(alt)}" src="{prefix}{name}"{w}{attrs}>'
    return f'<a href="{href}">{img}</a>' if href else img


def work(slug):
    return next(w for w in base.WORKS if w["slug"] == slug)
