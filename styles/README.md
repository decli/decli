# 风格实验室

主页现在用的是根目录那套「极光」。这里放着几套备选，每一套都能直接点进去看完整效果。

前两套（[终端](terminal/)、[便当格](bento/)）只是换了视觉。下面三套换的是**人和主页怎么互动**：

| | 街机 · 人机对弈 | 对话 · AI 分身 | 刊物 · 零行 |
| --- | --- | --- | --- |
| 访客在做什么 | **玩**：点棋盘，和 AI 下五子棋 | **聊**：点问题，一层层展开回答 | **读**：每天来，都是新的一期 |
| 交互靠什么 | 预填好的 issue 链接 + Action 落子、AI 回一手 | `<details>` 对话树（零延迟）+ issue 里真的由 AI 回话 | 每天定时出刊 + 明暗主题各是一版 |
| 视觉 | PICO-8 十六色、像素字体、合成器浪潮落日、扫描线 | 会转的渐变光球、聊天气泡、输入框 | 米白纸 / 墨色、思源宋体、瑞士海报式封面画 |
| 需要的密钥 | 不需要 | 可选：`LLM_API_KEY`（跟 codeless 同一把） | 不需要 |
| 维护 | 零：state.json 由 Action 自己改 | 零：对话树在 chat.py 里改文案 | 零：每天自己出刊 |

## 街机 · 人机对弈 → [看整页](arcade/)

<a href="arcade/"><img alt="街机风格" src="arcade/assets/cells/h.svg" width="40"><img alt="" src="arcade/assets/cells/a.svg" width="40"></a>

主页是一台街机。标题画面是合成器浪潮式的像素落日，下面是一块 9×9 的按钮棋盘：你执粉，AI 执蓝。
点任意空位 → GitHub 打开一个预填好的 issue → 点 Submit → Action 落子、让 AI 回一手、重画棋盘，
再在 issue 里回一句「AI 回了 F6，轮到你」。比分、名人堂、最近落子都记在 [state.json](arcade/state.json) 里。

「人出判断，AI 出产能」—— 这一次是真的在对弈。

## 对话 · AI 分身 → [看整页](chat/)

<a href="chat/"><picture><source media="(prefers-color-scheme: dark)" srcset="chat/assets/hero-dark.svg"><img alt="AI 分身" src="chat/assets/hero-light.svg" width="420"></picture></a>

整页是一段对话。开场是 AI 分身的一句话（先「正在输入」一秒多再冒出来），
下面是几颗可以点的问题：点一下，回答立刻展开，回答里还能接着点下一个问题。
想问树上没有的，点最底下那个输入框 —— 它是一个链接，开一个 issue，
Action 读作品资料、调模型写回复贴回去。没配 key 也能跑，只是回一段固定的话。

## 刊物 · 零行 → [看整页](editorial/)

主页是一本每天清晨六点（San Jose）自己出刊的杂志，刊名「零行」—— 十五个作品，一行代码没写。
每天换一件作品当封面故事，封面画按作品自己的主色生成（落日、圆弧、方格、条形四种构图）。
亮色主题是日刊，暗色主题是夜刊，导读都不一样 —— 夜刊里有一条写着「你切到了暗色主题」。

## 换成其中一套

每套目录里都有一个 `workflow.yml`，开头写着上线的两三步。大意都是：

```sh
python3 styles/<风格>/<脚本>.py --home               # README 生成到仓库根目录
cp styles/<风格>/workflow.yml .github/workflows/     # 让交互跑起来
```

`workflow.yml` 放在 `styles/` 下是不生效的，GitHub 只跑 `.github/workflows/` 里的 —— 所以现在这几套只是能看，不会动你的仓库。

## 字体

街机用的是[缝合像素字体](https://github.com/TakWolf/fusion-pixel-font)，刊物用的是[思源宋体](https://github.com/notofonts/noto-cjk)，
都是 SIL OFL 1.1，允许嵌入和子集化。每套只切出自己用得到的那几百个字（[`tools/fonts.py`](../tools/fonts.py)），
街机 5 KB，刊物两个字重各 60 KB 左右；刊物每期封面再按当期用到的字切一刀，一张封面 40 KB 上下。

SVG 当图片加载时拿不到外部资源，字体只能以 data: 形式嵌进去。实测 raw.githubusercontent.com 那条
`default-src 'none'` 的 CSP 挡不住它 —— CSP 只在 SVG 被当成文档直接打开时生效，在 README 里当图片显示不受影响。
万一某个浏览器不认，font-family 里还有系统字体兜底，字照样能读。
