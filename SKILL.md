---
name: guoxue-jingdian-gongdu
version: "1.1.0"
display_name: 国学经典书籍网站生成器
display_name_en: Classic Book Co-reading Site Generator
description: "国学经典书籍网站生成器。用户只需说一句，agent 即上网找公有领域底本、整理数据并构建自包含单文件 HTML（手机优先、分页、注音、工具箱、研读、安心签、省察）。双击即开、零登录零后端。TRIGGER when: 用户说「帮我做一个《书名》的在线共读网站」或想把国学经典做成可分享的网站。"
description_zh: "国学经典书籍网站生成器：把公有领域经典做成单文件、手机优先的在线共读网站——一天一章、左侧目录随阅读自动高亮定位、分享本章生成直达该章的链接、疑难字注音、工具箱、研读专区、每日安心签、省察笔记。用户只需说一句「帮我做《书名》的在线共读网站」，agent 即上网找底本、整理数据并构建出自包含 HTML，双击即开、零登录零后端。"
description_en: "Generate a single-file, mobile-first online co-reading site for public-domain classic books: daily chapter, scroll-spy TOC, share-a-chapter #ch-N link, pinyin annotation, toolbox, study section, daily calm quote, reflection notes. The user just says one sentence and the agent fetches text, structures data, builds self-contained HTML."
category: education
author: AIYAZONE
---

# 国学经典书籍网站生成器（guoxue-jingdian-gongdu）

## 试试这样用

- 帮我做一个《大学》的在线共读网站
- 我想给《论语》做一个一天一章的群内共读阅读器
- 用国学经典书籍网站生成器做《道德经》的可分享直达站点
- 给《止学》做一个手机优先的在线共读网站

## 给用户：一句话就够了

> 你（用户）只要说一句：**「帮我做一个《书名》的在线共读网站。」**
>
> 书的正文、译文、注释、研读资料——**你都不用准备**。这些由我（agent）上网找公开底本并整理；你只管看完后提修改意见。

## Overview

把任意一本可公开（公有领域）的经典，做成**单文件、手机优先、可群内共读**的网站。核心体验：一天一章自动排程、左侧目录随阅读自动高亮定位、每章「分享本章」生成直达该章的链接、阅读进度书签、疑难字注音、工具箱、研读专区、每日「安心签」、每章「省察」自省笔记。

本技能 = **一个 token 化模板 + 一个通用构建脚本 + 一份数据 Schema**。换一本书，agent 上网取底本、整理成数据、改 `config.json`，跑一次构建即可得到自包含 HTML——无外部依赖、无登录、无云端，双击即开，也能托管到任意静态空间。

**线上示例**：《中庸》共读站 `https://zhongyong.aiyazone.com` 和《大学》共读站 `https://daxue.aiyazone.com` 均由国学经典书籍网站生成器生成。

## When to Use

- 用户说「帮我做一个《X》的在线共读网站 / 阅读器 / 一天一章共读」。
- 用户想把《中庸》模式复用到《大学》《止学》《素书》《论语》等书，且**没有现成数据**，希望 agent 自行上网找。

## Agent 工作流程（你来执行，用户无需关心）

1. **确认范围**：问清书名、大概章数、是否要「朱注/四书互参」（《四书》类才有，其它书可省）、是否要注音。
2. **上网找底本**：用 `WebSearch` / `WebFetch` 从维基文库、国学网等抓取**公有领域**原文，按章拆分写入 `chapters.json`（`[{n, label, text}]`，必需）。同时抓逐句译文、章内注释/串讲、研读素材。
3. **整理数据**：严格按 `references/data-schema.md` 落盘各 JSON。关键校验：`anshen` 长度=章数、`reflections` 覆盖每章、`content.json` 为 dict（非 list）、`study.json` 中 `structure`/`spine` 为列表（非字符串）、`modern_anxiety` 字段名为 `theme/stress/remedy/quote`（非 `title/problem/cure`）、`p1.json` 中 `bibliography` 每条 2 值（非 3）、`echoes` 每条 4 值。网络素材不足时，译文/注释可基于原文**自撰疏通**并在研读「引用说明」标注为自撰；只收公有领域原文，不复制现代受版权保护的内容。
4. **写 `config.json`**：必须填 `book`/`key`/`favchar`/`theme`/`subtitle`/`intro`/`sidebar_foot`；`share_base` 留空（运行时自动用 `location.origin`）。**`subtitle` 必须有且须准确**——格式如「《礼记》第四十二篇 · 曾子述 · 四书之首」，用于封面标题下方一行说明。不确定字段就照抄 `samples/config.json` 再改。
5. **构建**：
   ```bash
   python3 scripts/build_reader.py 项目目录 --out 项目目录/dist/index.html
   ```
   构建后检查无残留 token：`grep -oE "{{[A-Z_]+}}|__[A-Z_]+__" 项目目录/dist/index.html` 应为空。
6. **自检与交付**：浏览器打开 HTML 检查封面 subtitle 正确、目录跳转、分页/连续切换、「分享本章」链接是否直达该章、注音开关有效、安心签、省察笔记可写；确认无误后把 HTML 交给用户。

## Architecture（一眼看懂）

```
项目目录/                ← agent 新建，数据来自网上抓取
├── config.json          ← 书名/键/subtitle/主题色/引言等（必需）
├── chapters.json        ← 每章原文 [{n,label,text}]（必需，来自网络底本）
├── sentences.json       ← 逐句译文 {"1": [["原文","译文"],...]}（强烈建议）
├── content.json         ← 章内详解：注释/串讲/解读/导读/省察（强烈建议，dict 格式）
├── study.json           ← 研读专区：结构/概念/名句/安心签/当代处境（可选）
├── p1.json             ← 参考书目/人物/省察问/章间呼应（可选）
├── p2.json             ← 朱注/经典互参/以经解经专题（可选）
├── pinyin.json         ← 注音/通假词典（强烈建议，没有就无法注音）
└── dist/               ← 构建产物（单文件 HTML，双击即开）

skill 自带：
├── assets/reader-template.html   ← token 化 UI 模板
├── scripts/build_reader.py        ← 通用构建引擎
├── references/data-schema.md      ← 每个 JSON 的字段契约
└── samples/                     ← 3 章最小可运行示例
```

## Resources

### scripts/
- `build_reader.py`：通用构建引擎。支持的 token：`{{BOOK}}`/`{{KEY}}`/`{{TOTAL_CN}}`/`{{FAVICON}}`/`{{THEME}}`/`{{INTRO}}`/`{{SUBTITLE}}`/`{{SIDEBAR_FOOT}}` 与 `__DATA__`/`__TOC_ITEMS__`/`__CHAPTERS_HTML__`/`__STUDY_HTML__`/`__ANSHEN__`/`__SHENGQ__`/`__SHARE_BASE__`/`__CN__`/`__TOTAL__`。

### references/
- `data-schema.md`：必须精读——每个字段名、格式、嵌套结构都有严格约定。新增 `subtitle` 字段。

### assets/
- `reader-template.html`：已 token 化的生产级阅读器 UI。**通常无需修改**。

### samples/
- `samples/`：3 章最小可运行示例。agent 复制 JSON 作为新书数据骨架最快。

## Hard-won Gotchas（必须遵守）

1. **单文件自包含、零登录、零后端**：产物无外部 JS/CSS 请求、无登录、无云端依赖；`file://` 也能开。进度/笔记/书签仅存本机 localStorage。**不要往模板里加任何登录 / 云端同步 / WB_CLOUD 代码**。
2. **封面 subtitle 必须准确**：`config.json` 的 `subtitle` 字段显示在封面首页标题下方，如「《礼记》第四十二篇 · 曾子述 · 四书之首」。不可省略、不可写错——作者归因错误是硬伤。
3. **数据格式精确匹配 schema**：`content.json` 为 dict（key 为章号字符串），非 list；`study.json` 的 `structure`/`spine` 为 list of lists，非字符串；`modern_anxiety` 字段名为 `theme/stress/remedy/quote`；`p1.json` 的 `bibliography` 每条 2 值（书名+说明），`echoes` 每条 4 值；`p2.json` 的 `sishu`/`topics` 为 list of dicts（非 list of lists）。
4. **注音是必需品**：`pinyin.json` 包含 `PINYIN`（单字→拼音）、`TONGGJIA`（单字→通假说明）、`PHRASE`（二字词→[拼音,说明]）。没有它，注音开关打开也无效果——疑难字如「絜矩」「心广体胖」「淇澳」将无标注。
5. **数据来源与版权**：只收公有领域经典原文，疏通/译文/解读/省察文字自撰或注明出处；引用说明（研读第十版块）声明出处。简体化后务必查 BMP 外生僻字。
6. **分享链接**：`share_base` 留空→运行时用 `location.origin`，任何域名自适配。`shareChapter` 先 `history.replaceState` 同步 hash 再分享。
7. **构建后校验清单**：① 无残留 token ② 封面 subtitle 准确 ③ 注音开关有效 ④ 研读各板块格式正确 ⑤ 章节数、安神签数、省察问数一致 ⑥ 概念词典互见列有真实引文（非数字占位）。

## 复用到其他书

1. 复制 `samples/*.json` 到新项目目录作为骨架。
2. WebSearch/WebFetch 抓目标书底本，覆盖 `chapters.json` 等 + 改 `config.json`。
3. 《四书》类可保留 `p2.json` 朱注/四书互参；非朱子体系书通常省略 p2.json。
4. 务必将 `samples/config.json` 中的 `subtitle` 改为新书的正确信息——**不可留用示例或错误的作者归因**。
5. `python3 scripts/build_reader.py 新项目目录 --out 新项目目录/dist/index.html` → 双击打开。