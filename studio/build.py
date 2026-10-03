#!/usr/bin/env python3
"""
第二代主页的生成入口，三套方向。

    python3 studio/build.py                 三套都生成到 styles/scroll/、styles/zero/、styles/aurora-pro/
    python3 studio/build.py --home zero     「零 · 灰与橙」生成到仓库根目录 —— 个人主页上显示的就是它
    python3 studio/build.py --home scroll   换成「长卷」
    python3 studio/build.py --home aurora-pro

作品、文案、配色以外的数据只有一份：根目录 build.py 里的 WORKS / POC / PRINCIPLES …
加一个作品改那里，然后跑这个脚本。

依赖：fonttools、brotli、Pillow（pip install fonttools brotli pillow）。
字体和截图：
  - 母版字体在 studio/fonts/，只含本页用得到的字；文案里出现母版没有的新字时会报错，
    按提示带上原始字体重切一次（python3 studio/build.py --masters）。
  - 截图来自作品集仓库 decli.github.io/shots/，处理后的小图缓存在 studio/shots/。
"""

import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import kit  # noqa: E402
import zero  # noqa: E402
import aurora_pro  # noqa: E402
import scroll  # noqa: E402

STYLES = {"zero": zero, "aurora-pro": aurora_pro, "scroll": scroll}


def main(argv):
    home = None
    if "--home" in argv:
        home = argv[argv.index("--home") + 1]
        if home not in STYLES:
            sys.exit(f"不认识的风格：{home}（可选：{' / '.join(STYLES)}）")
    for name, mod in STYLES.items():
        print(f"▸ {name}")
        mod.build(kit.ROOT / "styles" / name)
    if home:
        print(f"▸ 主页 ← {home}")
        assets = kit.ROOT / "assets"
        if assets.exists():
            shutil.rmtree(assets)
        STYLES[home].build(kit.ROOT)
    if "--masters" in argv:
        kit.cut_masters()
    kit.save_seg()


if __name__ == "__main__":
    main(sys.argv[1:])
