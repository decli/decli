<!-- 这个文件由 styles/editorial/cover.py 生成。改内容请改 styles/editorial/cover.py 里的数据，再跑 python3 styles/editorial/cover.py -->

<a href="https://decli.github.io"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/cover-dark-802c3849.svg"><img alt="《零行》日刊 第 1 期，2026 年 9 月 26 日。封面故事：老爸下象棋 —— 按 14 寸平板放大布局的中国象棋，三档 AI，落子有语音播报。 导读：特稿：十五个作品，一行代码没写；实测：一句话做一个网站，花了 $0.0127；家事：给老爸的象棋，为什么要放大到 14 寸；方法：人出判断，AI 出产能" src="assets/cover-light-f7a1df4f.svg" width="100%"></picture></a>

<p align="center"><sub>《零行》第 1 期 · 每天清晨六点（San Jose）自动出刊 · 切换 GitHub 的明暗主题，拿到的是日刊或夜刊</sub></p>

## 封面故事 · 老爸下象棋

> 按 14 寸平板放大布局的中国象棋，三档 AI，落子有语音播报。

Android 平板上的中国象棋，按 14 寸横屏放大过布局，三档 AI，落子有音效和语音播报。

<sub>Android · 象棋 · 大屏</sub>

[源码](https://github.com/decli/chinesechess03)

## 特稿 · 十五个作品，一行代码没写

从 UI 交互设计到每一行代码编写，全部由 AI 完成。

我只做三件事：**提出问题**、**选择方案**、**验收结果**。剩下的 —— 从界面设计到每一行代码 —— 全部交给 AI。不是尝鲜，这是 AI Native 时代工作的新范式。

## 实测 · 一句话做一个网站，花了 $0.0127

codeless 的一次 POC：一句「做一个咖啡店单页官网」，AI 在断网的沙箱里调了 13 次模型，验收测试一轮全绿，推送后 CI 自动部署，点开链接就能访问。

```mermaid
flowchart LR
  A[一句话需求] --> B[断网沙箱里写代码<br/>13 次模型调用]
  B --> C{验收测试}
  C -- 全绿 --> D[CI 部署] --> E[上线，$0.0127]
  C -- 没过 --> F[AI 自己修] --> C
```

[看 codeless 的源码](https://github.com/decli/codeless) · [POC 实测记录](https://github.com/decli/codeless/blob/main/docs/06-poc-findings.md)

<details><summary><b>往期 · 全部 15 件作品</b></summary>

| 作品 | 它替谁解决什么 | 入口 |
| --- | --- | --- |
| **codeless**<br><sub>在线应用</sub> | 说一句话，它写代码、跑测试、改 bug，再部署成能打开的网站。 | [源码](https://github.com/decli/codeless) |
| **信风 Tradewind**<br><sub>在线应用</sub> | 外贸全流程管理，从询盘到退税，一个 PI 号串到底。 | [在线](https://decli.github.io/ftms/) · [源码](https://github.com/decli/ftms) |
| **EMS 外贸营销系统**<br><sub>在线应用</sub> | AI Agent 驱动的外贸增长，从找到买家到收到货款。 | [在线](https://decli.github.io/ems/) · [源码](https://github.com/decli/ems) |
| **思维小画本**<br><sub>在线应用</sub> | 把做不下去的纸质练习册，改成十二个会读题的平板游戏。 | [在线](https://decli.github.io/logicc/) · [源码](https://github.com/decli/logicc) |
| **WxMark**<br><sub>在线应用</sub> | 公众号 Markdown 排版，一键复制成能直接粘贴的 HTML。 | [在线](https://decli.github.io/wxformat3/) · [源码](https://github.com/decli/wxformat3) |
| **IP 归属地监控**<br><sub>浏览器扩展</sub> | 工具栏直接显示出口国家，代理有没有生效一眼可见。 | [源码](https://github.com/decli/IP_Geolocation_Extension_Chrome) |
| **职得投 JobOrNot**<br><sub>浏览器扩展</sub> | 把简历和岗位 JD 摆在一起比，诚实回答值不值得投。 | [源码](https://github.com/decli/JobOrNot) |
| **公众号数据导出**<br><sub>浏览器扩展</sub> | 在本地导出公众号文章的阅读、点赞、分享数据，拿来复盘选题。 | [源码](https://github.com/decli/weixin_public_export) |
| **TabInfoCopy**<br><sub>浏览器扩展</sub> | 一键复制当前标签页的标题和网址。 | [源码](https://github.com/decli/TabInfoCopy) |
| **IP Display**<br><sub>浏览器扩展</sub> | 显示当前 IP 与归属地。IP 归属地监控的前身，留着做个记录。 | [源码](https://github.com/decli/IPDisplayExtension) |
| **PageScroll**<br><sub>用户脚本</sub> | 任意网页上一个可拖动的悬浮胶囊，一点回顶或到底。 | [源码](https://github.com/decli/pagescroll) |
| **Bing 壁纸批量下载**<br><sub>用户脚本</sub> | 勾选多张壁纸，一次批量下载 4K 原图。 | [源码](https://github.com/decli/BingWDByte4KBatchDownloader) |
| **MacPleco**<br><sub>桌面应用</sub> | 不制造焦虑的 Mac 清理工具，删什么都先进废纸篓。 | [下载](https://github.com/decli/MacPleco/releases/latest) · [源码](https://github.com/decli/MacPleco) |
| **取件码助手**<br><sub>移动应用</sub> | 从短信里挑出还没取的取件码，像取件小票一样大字摆出来。 | [源码](https://github.com/decli/CodeHelper) |
| **老爸下象棋**<br><sub>移动应用</sub> | 按 14 寸平板放大布局的中国象棋，三档 AI，落子有语音播报。 | [源码](https://github.com/decli/chinesechess03) |

</details>

<details><summary><b>编者按 · 我相信的几件事</b></summary>

**人出判断，AI 出产能。** 我只做三件事：提出问题、选择方案、验收结果。剩下的，从 UI 交互设计到每一行代码，全部交给 AI。

**不摆示意图。** 作品集里的每一张截图都来自项目本身。拿不出真图的，宁可不放预览，也不摆一张摆拍出来的示意图。

**一页只做一件事。** 作品集首页曾经加过戳泡泡和连连看，后来都拿掉了 —— 入口页多一个玩意儿，主线就模糊一分。

</details>

---

<sub>撰文 AI · 审校 decli · 排版 cover.py · 本期出刊于 2026-09-26</sub>
