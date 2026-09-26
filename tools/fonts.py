#!/usr/bin/env python3
"""
开发时用：从完整字体里切出每套实验风格真正用到的字，存成 woff2，放进各自的 fonts/ 目录。

    pip install fonttools brotli
    python3 tools/fonts.py --src <放原始字体的目录>

需要的原始字体（都是 SIL OFL 1.1，允许嵌入和子集化）：
    fusion-pixel.ttf        缝合像素字体 Fusion Pixel     npm: @fontpkg/fusion-pixel
    NotoSerifSC[wght].ttf   思源宋体 Noto Serif SC 可变   github.com/google/fonts → ofl/notoserifsc

为什么要切：整套中文字体几 MB 到几十 MB，塞进 SVG 不现实；
而一套风格实际用到的字只有几百个，切出来几十 KB。
字表由各风格的 chars() 给出 —— 改了文案、加了作品，重跑一次这个脚本就行。
Action 里只用切好的小文件，不需要原始字体，也不需要 fonttools。
"""

import argparse
import importlib.util
import io
import pathlib
import sys

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parents[1]

# 风格 → [(字体文件, 输出名, 可变字体轴设置)]
JOBS = {
    "arcade": [("fusion-pixel.ttf", "pixel.woff2", None)],
    "editorial": [("NotoSerifSC[wght].ttf", "serif-black.woff2", {"wght": 900}),
                  ("NotoSerifSC[wght].ttf", "serif-medium.woff2", {"wght": 500})],
}
SCRIPTS = {"arcade": "styles/arcade/game.py", "editorial": "styles/editorial/cover.py"}


def load_chars(style):
    path = ROOT / SCRIPTS[style]
    spec = importlib.util.spec_from_file_location(f"style_{style}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.chars()


def cut(src, text, axes):
    font = TTFont(src)
    if axes:
        from fontTools.varLib import instancer
        font = instancer.instantiateVariableFont(font, axes)
    opts = subset.Options()
    opts.layout_features = ["kern", "liga"]
    opts.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]  # 保留版权和许可证说明
    s = subset.Subsetter(opts)
    s.populate(text=text)
    s.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="放原始字体的目录")
    ap.add_argument("styles", nargs="*", default=list(JOBS))
    a = ap.parse_args()
    for style in a.styles:
        text = "".join(sorted(set(load_chars(style))))
        for fname, out, axes in JOBS[style]:
            data = cut(pathlib.Path(a.src) / fname, text, axes)
            dest = ROOT / "styles" / style / "fonts" / out
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            print(f"✓ {style}/{out}  {len(text)} 字  {len(data) / 1024:.0f} KB", file=sys.stderr)
