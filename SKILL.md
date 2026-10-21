---
name: classic-book-co-reader
version: "1.0.0"
display_name: 古籍共读网站生成器
display_name_en: Classic Book Co-reading Site Generator
description_zh: "把公有领域古籍做成单文件、手机优先的在线共读网站：一天一章、左侧目录随阅读自动高亮定位、分享本章生成直达该章的链接、疑难字注音、工具箱、研读专区、每日安心签、省察笔记。用户只需说一句「帮我做《书名》的在线共读网站」，agent 即上网找底本、整理数据并构建出自包含 HTML，双击即开、零登录零后端。"
description_en: "Generate a single-file, mobile-first online co-reading site for public-domain classic books: daily chapter, scroll-spy TOC, share-a-chapter #ch-N link, pinyin annotation, toolbox, study section, daily calm quote, reflection notes. The user just says one sentence, such as build me a co-reading site for 《book》, and the agent fetches the public-domain text online, structures the data, and builds a self-contained HTML that opens by double-click, with no login and no backend."
description: "生成「古籍/经典共读」单文件网站的专业技能。用户只需说一句『帮我做一个《书名》的在线共读网站』，agent 即上网找公有领域底本、整理数据并构建出自包含单文件 index.html（手机优先、分页、左侧目录随阅读自动高亮定位、每章分享生成直达该章的链接、阅读书签、注音、工具箱、研读专区、安心签、省察笔记），双击即可在浏览器打开。This skill should be used when a user asks to build a book co-reading site or classic-text reader and expects the agent to gather the book text from the web."
examples:
  - 帮我做一个《大学》的在线共读网站
  - 我想给《论语》做一个一天一章的群内共读阅读器
  - 用古籍共读生成器做《道德经》的可分享直达站点
  - 给《止学》做一个手机优先的在线共读网站
---

# 古籍共读网站生成器（classic-book-co-reader）

## 给用户：一句话就够了

> 你（用户）只要说一句：**「帮我做一个《书名》的在线共读网站。」**
>
> 书的正文、译文、注释、研读资料——**你都不用准备**。这些由我（agent）上网找公开底本并整理；你只管看完后提修改意见。

## Overview

把任意一本可公开（公有领域）的古籍/经典，做成**单文件、手机优先、可群内共读**的网站。核心体验：一天一章自动排程、左侧目录随阅读自动高亮定位、每章「分享本章」生成直达该章的链接、阅读进度书签、疑难字注音、工具箱（设置/笔记/分享）、研读专区（结构脉络/概念词典/名句/互参/专题）、每日「安心签」、每章「省察」自省笔记。

本技能 = **一个 token 化模板 + 一个通用构建脚本 + 一份数据 Schema**。换一本书，agent 上网取底本、整理成数据、改 `config.json`，跑一次构建即可得到自包含 `index.html`——无外部依赖、无登录、无云端，双击即开，也能托管到任意静态空间。

**线上示例**：《中庸》共读站 `https://zhongyong.aiyazone.com` 就是由本 skill 生成的成品，可直接点开体验全部功能（手机优先、每章「分享本章」生成直达该章的链接、疑难字注音、工具箱、研读专区、每日安心签、省察笔记）。

## When to Use

- 用户说「帮我做一个《X》的在线共读网站 / 阅读器 / 一天一章共读」。
- 用户想把《中庸》模式复用到《大学》《止学》《素书》《论语》等书，且**没有现成数据**，希望 agent 自行上网找。

## Agent 工作流程（你来执行，用户无需关心）

1. **确认范围**：问清书名、大概章数（如《大学》11 章、《中庸》33 章）、是否要「朱注/四书互参」（《四书》类才有，其它书可省）、是否要读音/通假注音。
2. **上网找底本**：用 `WebSearch` / `WebFetch` 从维基文库、国学网、古诗文网等抓取**公有领域**原文，按章拆分写入 `chapters.json`（`[{n, label, text}]`，必需）。按需抓逐句译文、章内注释/串讲、研读素材。
3. **整理数据**：严格按 `references/data-schema.md` 落盘各 JSON；务必 `anshen` 长度 = 章数、`reflections` 覆盖每章。网络素材不足时，译文/注释可基于原文**自撰疏通**并在研读「引用说明」标注为自撰；只收公有领域原文，不复制现代受版权保护的内容。
4. **写 `config.json`**：填 `book`/`key`/`favchar`/`theme`/`intro`/`sidebar_foot`；`share_base` 留空（运行时自动用 `location.origin`）。不确定字段就照抄 `samples/config.json` 再改。
5. **构建**：
   ```bash
   python3 scripts/build_reader.py 项目目录 --out 项目目录/dist/index.html
   ```
   构建后检查无残留 token：`grep -oE "{{[A-Z_]+}}|__[A-Z_]+__" 项目目录/dist/index.html` 应为空。
6. **自检与交付**：浏览器打开 `dist/index.html` 检查目录跳转、分页/连续切换、「分享本章」链接是否直达该章、注音开关、安心签、省察笔记可写；确认无误后把 `index.html` 交给用户（用户双击即看，或自行托管）。

## Architecture（一眼看懂）

```
项目目录/                ← agent 新建，数据来自网上抓取
├── config.json          ← 书名/键/主题色/引言等（必需）
├── chapters.json        ← 每章原文 [{n,label,text}]（必需，来自网络底本）
├── sentences.json       ← 逐句译文（可选，自撰或网上找）
├── content.json         ← 章内详解：注释/串讲/解读/导读/省察（可选）
├── study.json           ← 研读专区：结构/概念/名句/安心签/当代处境（可选）
├── p1.json             ← 参考书目/人物/省察问/章间呼应（可选）
├── p2.json             ← 朱注/经典互参/以经解经专题（可选）
├── pinyin.json         ← 注音/通假词典（可选）
└── dist/index.html     ← 构建产物（单文件，双击即开）

skill 自带：
├── assets/reader-template.html   ← token 化 UI 模板（{{BOOK}}/{{KEY}}/__DATA__ 等）
├── scripts/build_reader.py        ← 通用构建引擎（数据 → 单文件 HTML）
├── references/data-schema.md      ← 上述每个 JSON 的字段契约 + 示例
└── samples/                     ← 3 章最小可运行示例（含 index.html），数据骨架复制最快
```

**关键设计**：UI/交互逻辑全部在 `reader-template.html`，数据经构建脚本注入为内联 JS 变量。换书 = 换数据 + 改 config，**不碰模板**。

## Resources

### scripts/
- `build_reader.py`：通用构建引擎。读 `config.json` + 数据 JSON，注入 `reader-template.html` 的 `{{BOOK}}`/`{{KEY}}`/`{{TOTAL_CN}}`/`{{FAVICON}}`/`{{THEME}}`/`{{INTRO}}`/`{{SIDEBAR_FOOT}}` 与 `__DATA__`/`__TOC_ITEMS__`/`__CHAPTERS_HTML__`/`__STUDY_HTML__`/`__ANSHEN__`/`__SHENGQ__`/`__SHARE_BASE__`/`__CN__`/`__TOTAL__` 等 token，输出自包含 `index.html`。已用《中庸》全量数据 + `samples` 全量验证通过（无残留 token、JS 语法 OK、零登录零后端）。

### references/
- `data-schema.md`：每个 JSON 的字段契约与示例，构建前必读。

### assets/
- `reader-template.html`：已 token 化的生产级阅读器 UI（响应式、分页、目录、注音、工具箱、研读、安心签、省察）。**通常无需修改**；若需改版式/配色，改这里并在 `build_reader.py` 同步 token。

### samples/
- `samples/`：3 章最小可运行示例（含已构建 `index.html`）。agent 复制其中的 JSON（config.json、chapters.json 等）作为新书数据骨架最快。

## Hard-won Gotchas（必须遵守）

1. **单文件自包含、零登录、零后端**：产物无外部 JS/CSS 请求、无登录、无云端依赖；`file://` 也能开。进度/笔记/书签仅存本机 localStorage，不跨设备。本 skill 生成的阅读器零登录、零后端——**不要往模板里加任何登录 / 云端同步 / WB_CLOUD 代码**（曾因临时加云端而引入「未登录禁用省察笔记」的 bug，已彻底移除）。
2. **数据来源与版权**：只收公有领域古籍原文（维基文库/国学网等可作底本），疏通/译文/解读/省察文字自撰或注明出处，不复制现代出版物受保护内容；引用说明（研读第十版块）声明出处。简体化后务必查 BMP 外生僻字，避免乱码。
3. **分享链接**：`share_base` 留空→运行时用 `location.origin`，任何域名自适配；放到子路径托管才需显式填。`shareChapter` 先 `history.replaceState` 同步直达该章的链接再分享，避免系统分享/Web 复制丢 hash。
4. **数据校验**：`anshen` 长度=章数；`reflections` 覆盖每章；`concepts` 形如 `[term, pinyin, defi, "1,2,3", [[ch,sent],...]]`（第 4 项是逗号分隔章号串，第 5 项是互见列表）；`structure`/`quotes`/`spine`/`echoes` 见 schema。

## 复用到《大学》《止学》《素书》等

1. 把 `samples/` 下的示例 JSON（`config.json`、`chapters.json` 等）复制到新项目目录作为骨架，例如 `cp samples/*.json 新项目目录/`（或新建目录再写）。
2. 用 WebSearch/WebFetch 抓目标书底本，覆盖 `chapters.json` 等 + 改 `config.json`（`book`/`key`/`favchar`/`intro`…）。
3. 《四书》类（大学/中庸/论语/孟子）可保留 `p2.json` 的 `zhuzhu`/`sishu`；《止学》《素书》等非朱子体系书通常**省略 p2.json 的朱注与四书互参**，仅用 content/study/p1 即足够。
4. `python3 scripts/build_reader.py 新项目目录 --out 新项目目录/dist/index.html` → 双击打开 `dist/index.html` 即可。
