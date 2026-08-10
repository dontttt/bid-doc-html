---
name: bid-doc-html
description: >-
  把投标技术参数与对应图片转换为排版精良、图文一一对应的画册风单文件 HTML 产品说明书/白皮书。
  当用户要制作「投标产品说明书 / 产品白皮书 / 投标画册 / 参数配图文档」，或提供了投标参数 docx、
  希望生成可分享的图文 HTML 时调用。默认家具画册风、简体中文、图片 base64 内嵌（分享不丢图）、A4 打印友好。
summary: "投标参数+配图 → 画册风自包含 HTML 说明书"
read_when:
  - 用户要制作投标产品说明书或白皮书
  - 用户提供投标参数 docx 需要生成图文 HTML
  - 用户提到"投标画册""参数配图""产品说明书 HTML"
agent_created: true
---

# Bid Doc HTML

把「投标技术参数 + 对应图片」转换成排版精良、图文一一对应的**单文件 HTML 说明书**。默认画册风、中文、base64 内嵌图片（可直接分享不丢图）。

## When to use / When NOT to use

**用本技能**：投标产品说明书、产品白皮书、投标画册、参数配图文档；用户给了 docx 参数表、或参数+图片想快速成稿。
**不要用本技能**：纯文字合同/标书正文撰写（用文档协作类技能）；需要真实 Word(.docx) 可编辑交付（用 docx 技能）；非投标类的通用网页/海报（用 frontend-design / canvas-design）。

## Quick start

```bash
# 路径A：用户给了 docx（推荐，零依赖，仅需 Python 标准库）
python <skill>/scripts/make_doc.py <参数表.docx> [输出目录] \
  [--title "标题"] [--layout gallery|block] [--theme gov] [--accent #c0392b] [--json]

# 校验脚本本身（不依赖真实文件，CI/本地冒烟）
python <skill>/scripts/make_doc.py --self-test
```

- 输出：`<输出目录>/index.html`（图片 base64 内嵌）+ `<输出目录>/images/`
- 脚本自动探测文档形态（单表格 / 段落型产品 / 传统章节）并选对应解析器
- 完整 CLI 见末尾「命令行参数」

## TL;DR

| 场景 | 做法 |
|------|------|
| 用户给了 docx | 跑 `python scripts/make_doc.py <docx> [输出目录]` → 交付 `index.html` |
| 用户没 docx，只有参数+图片 | 发简报模板（`references/brief-template.md`）引导结构化提交 → 基于 `assets/template.html` 手动组装 |
| 用户要当模板长期增删改 | 用 `assets/editor.html` 作工作台：开箱即投标骨架、任意增删/替换章节与图片、导入↔导出自循环、图片自动压缩；复制一份到项目目录即专属模板 |

## Locked Defaults

- **输出**：单文件 HTML，图片 base64 内嵌，零外部依赖
- **风格**：家具画册风（大图 + 图文并排 + 留白 + 浅底 + 单一强调色）
- **语言**：简体中文
- **响应式 + A4 打印友好**（打印保留主题色）

## Workflow

### 路径A：用户提供 docx（推荐）

1. 运行脚本（见 Quick start）。自动：解包 docx → 提取图文 → 按编号分章节 → 注入 `template.html` → base64 内嵌图片。
2. **验收**（见下「交付验收清单」）后，用 `present_files` 打开 `index.html` 预览。
3. 告知用户后编辑能力：打开 `editor.html` 可全文编辑、增删章节/图片、导出独立 HTML / PDF；或在浏览器打开 `index.html`，底部工具栏提供标注/调整/编辑三大模式。

### 路径B：用户没有 docx

1. 把 `references/brief-template.md` 发给用户，引导按「参数↔配图对应表」结构化提交。
2. Read 工具读取图片文件夹，确认编号与段落绑定关系。
3. 以 `assets/template.html` 为底座替换占位符（`{{TITLE}}`/`{{SUBTITLE}}`/`{{HERO_SRC}}`/`{{INTRO_ITEMS}}`/`{{SECTIONS}}`/`{{THEME_CLASS}}`），图片路径 `src="images/图N.jpg"` → base64 内嵌。
4. 验收 + 交付（同路径A）。

### 路径C：用户要当"模板工作台"长期增删改（推荐作为交付前精修）

用 `assets/editor.html`（全功能编辑器，开箱即带投标骨架：封面+产品配置清单+2 示例章节）：
1. **改文字**：直接点任意文字编辑。
2. **图片**：封面「+ 上传」/图片悬停「替换·删除」；章节「+ 上传图片」后可替换/删除；上传自动压缩（≤1600px、JPEG 0.85）控制体积。
3. **章节**：底部「+ 添加章节」、章节间「+ 在此添加」、右上角「↑↓ 删除」。
4. **样式**：顶部工具栏字号/粗细/颜色/全文字体/11 套主题即时调。
5. **保存闭环**：「📥 导出 HTML」产出单文件成品（CSS+图全内嵌，可分享/打印）；「📤 导入 HTML」把导出的成品再读回继续编辑——形成导出↔导入完整闭环。浏览器 `localStorage` 自动存草稿（file:// 下个别浏览器可能不持久，重要成果请以导出 HTML 为准）。

> `index.html`（docx 生成物）仅适合轻量标注/调整/选区级格式化与打印，不可增删章节图片、重跑 docx 会覆盖手动改动——它不是模板，精修请用 editor.html。

## 交付验收清单（Definition of done）

- [ ] 文档标题、副标题正确，无占位文本/TODO
- [ ] 章节数与源文件一致（非 0、非异常多）；编号 `1、2、3` 顺序正确
- [ ] 每段有配图；缺图时已提示用户补到 `images/` 并更新 `<img src>`
- [ ] 参数数字与源文件一致；关键项（★）、规格（规格尺寸）已高亮样式
- [ ] 全文无残留 `{{...}}` 占位符
- [ ] 图片均为 base64 内嵌（离线分享不丢图）；产物 < 20MB（超标提示改用相对路径版）
- [ ] 主题/强调色符合项目调性（政府国企优先 `gov`、家具家居 `wood`）

## 示例（few-shot）

见 `references/examples.md`：含「单表格型」「段落型产品」「无 docx 纯参数+图片」三种输入→输出片段，照抄即可对齐风格。

## 边界情况与排错

| 场景 | 处理 |
|------|------|
| docx 图片链接损坏/缺失 | 脚本跳过该图并告警；提示用户补图到 `images/` 并更新 `index.html` 的 `<img src>` |
| docx 无任何图片 | 脚本仍生成 HTML，提示用户后续补图 |
| 非 docx 输入（PDF/纯文字） | 引导走路径B（简报模板），或先转为 docx |
| 脚本执行失败 | 检查 Python 环境 → 检查 docx 是否损坏 → 降级为路径B |
| 输出 > 20MB | 提示用户可选相对路径版（`images/` 文件夹）代替 base64 内嵌 |
| 用户要中英双语 | 简报模板增加英文列，生成时双语并列 |
| 用户要换强调色 | 生成时加 `--theme gov` 或 `--accent #c0392b`；或指引在 editor.html / index.html 工具栏切换 11 套主题 |

## Image Delivery Options（用户给图的三种方式）

1. **文件夹 + 编号命名**（`图1-外观.jpg`）→ 最省事，直接读
2. **对话里直接上传**，说明"第N张对应第X段"
3. **图未出、占位** → 文案写"此处需图：原理示意图"，先留白，用户后补

## One-Shot Quality Tips（交付时告知用户）

- 先给一页"范例"对齐风格：旧文档/截图，照版式复刻比文字描述准
- 参数用表格给，别揉进句子
- 一次给全，不分批

## Built-in Features（生成后用户可用，无需 AI 介入）

标注引擎（箭头/圆圈/线型/虚实/说明文字拖动） · 图片与文字框拖拽缩放 · 选区级文字格式化（字体/字号/粗细/颜色/对齐/列表/高亮/斜体/删除线） · 全文字体切换 · 11 套主题（含深色自适应，箭头/标注颜色随主题变化） · 图名编辑与显示开关 · 一键重置 · A4/PDF 导出（所见即所得，保留主题色） · 上传图片自动压缩（≤1600px / JPEG 0.85） · 导入 HTML 继续编辑（导出↔导入闭环） · 一键主题预览悬浮条（右下角 🎨，11 套主题带名称即时预览） · localStorage 自动保存草稿

> **生成的 `index.html` 也可当模板**：编辑模式下每章节右上角「✕ 删除」、右下角「＋ 添加章节」浮动按钮可增删章节；每张图悬停有「替换/删除」、空图位可「＋ 上传图片」（均自动压缩）。改完「导出含标注」即可保存成品（含所有增删改）。

## 命令行参数（scripts/make_doc.py）

| 参数 | 说明 |
|------|------|
| `docx` | 参数表 .docx 路径（必填，除非 `--self-test`） |
| `out` | 输出目录（默认 docx 同目录下 `bid-doc/`） |
| `--title` | 自定义文档标题 |
| `--layout` | `gallery`（图文画廊，默认）/ `block`（逐句配图块），用于表格/段落型文档 |
| `--theme` | 预设主题：`wood`/`tech`/`gov`/`mint`/`orange`/`dark`/`morandi`/`purple`/`khaki`/`mono`（默认青绿） |
| `--accent` | 自定义强调色十六进制（如 `#c0392b`），覆盖主题色 |
| `--json` | 以 JSON 输出结果摘要（标题/章节数/布局/主题/大小/产物路径），便于自动化与评测 |
| `--self-test` | 运行内置冒烟测试后退出，不依赖真实文件 |

## Resources

| 路径 | 用途 |
|------|------|
| `scripts/make_doc.py` | 端到端生成器（Python 标准库，零安装）。docx → index.html，含 `--self-test`/`--json` |
| `assets/template.html` | 画册风 HTML 底座（内联 CSS + 标注引擎 + 调整 + 编辑 + 11 主题 + PDF 打印） |
| `assets/editor.html` | 全功能文档编辑器/模板工作台（开箱投标骨架 + 增删章节/图片 + 导入↔导出 HTML/PDF + 图片自动压缩） |
| `references/brief-template.md` | 标准简报模板（引导用户结构化提交参数+配图） |
| `references/template-features.md` | 模板功能详细文档（CSS/JS/State，供深度定制） |
| `references/examples.md` | few-shot 示例（三种输入形态→输出片段） |
| `tests/validate_output.py` | 校验已生成的 `index.html`（占位符/章节/图片/主题），供 CI 与人工复检 |
| `tests/run_all.py` | 全套自检入口：make_doc 自测 + 生成校验 + editor 契约检查，一条命令跑完 |

> 测试：本机 `python tests/run_all.py`（推荐，跑全套）；或单独 `python scripts/make_doc.py --self-test`、`python tests/validate_output.py <index.html>`。

## 设计原则（本技能工程实践，吸收优质 skill 优点）

- **渐进式披露**：SKILL.md 只放触发词/流程/验收，细节下沉到 `references/` 与代码，保持 <200 行可读。
- **可运行测试**：`make_doc.py --self-test` + `tests/run_all.py` 不依赖真实文件即可冒烟，CI 友好。
- **few-shot 示例**：`references/examples.md` 给输入→输出片段，降低对齐风格成本。
- **验收清单（Definition of done）**：交付前逐项核对，避免占位符/丢图/数字不一致。
- **单文件零依赖**：HTML 内联 CSS+JS、图片 base64 内嵌，分享不丢图、离线可开。
- **双形态**：`make_doc.py` 批量从 docx 出稿；`editor.html` 交互精修，二者互补。
