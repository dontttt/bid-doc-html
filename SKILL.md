---
name: bid-doc-html
description: >-
  Generate bid-ready product brochures / white papers as a single self-contained HTML page.
  Use when the user wants to create 投标产品说明书 / 产品白皮书 / 投标画册 from 投标参数
  and paired images. Trigger: 投标说明书, 产品白皮书, 投标画册, 参数配图文档,
  "根据参数做一份图文说明书". Default: furniture-catalog style, Chinese copy, base64-embedded images.
summary: "投标参数+配图 → 画册风自包含HTML说明书"
read_when:
  - 用户要制作投标产品说明书或白皮书
  - 用户提供投标参数docx需要生成图文HTML
  - 用户提到"投标画册""参数配图""产品说明书HTML"
agent_created: true
---

# Bid Doc HTML

把「投标技术参数 + 对应图片」转换成排版精良、图文一一对应的**单文件 HTML 说明书**。默认画册风、中文、base64 内嵌图片（可直接分享不丢图）。

## TL;DR

| 场景 | 做法 |
|------|------|
| 用户给了 docx | 跑 `python scripts/make_doc.py <docx> [输出目录]` → 交付 `index.html` |
| 用户没 docx，只有参数+图片 | 发简报模板（`references/brief-template.md`）引导结构化提交 → 基于 `assets/template.html` 手动组装 |
| 用户要编辑已生成的文档 | 打开 `assets/editor.html` 全功能编辑器，或用 `index.html` 内置工具栏 |

## Locked Defaults

- **输出**：单文件 HTML，图片 base64 内嵌，零外部依赖
- **风格**：家具画册风（大图 + 图文并排 + 留白 + 浅底 + 单一强调色）
- **语言**：简体中文
- **响应式 + A4 打印友好**

## Workflow

### 路径A：用户提供 docx（推荐）

**Step 1 — 运行脚本**

```
python <skill>/scripts/make_doc.py <参数表.docx> [输出目录] [--title "标题"]
```

- 仅依赖 Python 标准库，零安装
- 自动：解包 docx → 提取图文 → 按数字编号分章节（子项如 11.1 折叠进父章节）→ 注入 template.html → base64 内嵌图片
- 输出：`<输出目录>/index.html` + `<输出目录>/images/`
- 默认输出目录：docx 同目录下 `bid-doc/`

**Step 2 — 校验**

- [ ] 章节数合理（非 0、非异常多）
- [ ] 每段有配图（缺图时提示用户补到 `images/` 并更新 `<img src>`）
- [ ] 参数数字与源文件一致
- [ ] 无占位文本/TODO

**Step 3 — 交付**

用 `present_files` 打开 `index.html` 预览。告知用户后编辑能力：
- 打开 `editor.html` 可全文编辑、增删章节/图片、导出独立 HTML / PDF
- 或在浏览器中打开 `index.html`，底部工具栏提供标注/调整/编辑三大模式

### 路径B：用户没有 docx

**Step 1 — 发送简报模板**

把 `references/brief-template.md` 发给用户，引导按「参数↔配图对应表」结构化提交。

**Step 2 — 读取素材**

Read 工具读取图片文件夹，确认编号与段落绑定关系。

**Step 3 — 生成 HTML**

以 `assets/template.html` 为底座，替换占位符：

| 占位符 | 替换为 |
|--------|--------|
| `{{TITLE}}` | 文档标题 |
| `{{SUBTITLE}}` | 副标题 |
| `{{HERO_SRC}}` | 封面图路径 |
| `{{INTRO_ITEMS}}` | 配置清单 `<li>` 列表 |
| `{{SECTIONS}}` | 各章节 HTML |

图片路径 `src="images/图N.jpg"` → base64 内嵌（`src="data:image/png;base64,..."`）。

**Step 4 — 校验 + 交付**

同路径A Step 2-3。

### 路径C：用户要编辑已生成的文档

指引打开 `assets/editor.html`（全功能编辑器）：
- 所有文字直接点击编辑（contentEditable）
- 增删章节、上传/替换/删除图片
- 11 套主题 + 全文字体一键切换
- 导出独立 HTML / PDF

或在浏览器打开 `index.html`，底部工具栏：
- **标注模式**：箭头/圆圈指向图片，可调线型粗细/虚实
- **调整模式**：拖拽缩放图片和文字框
- **编辑模式**：选区级字体/字号/粗细/颜色/对齐/列表/高亮

## Boundary Conditions

| 场景 | 处理 |
|------|------|
| docx 图片链接损坏/缺失 | 脚本跳过该图；提示用户补图到 `images/` 并更新 `index.html` 的 `<img src>` |
| docx 无任何图片 | 脚本仍生成 HTML，提示用户后续补图 |
| 非 docx 输入（PDF/纯文字） | 引导走路径B（简报模板），或先转为 docx |
| 脚本执行失败 | 检查 Python 环境 → 检查 docx 是否损坏 → 降级为路径B |
| 输出 >20MB | 提示用户可选相对路径版（`images/` 文件夹）代替 base64 内嵌 |
| 用户要中英双语 | 简报模板增加英文列，生成时双语并列 |
| 用户要换强调色 | 指引在 editor.html 或 index.html 工具栏切换 11 套主题 |

## Image Delivery Options（用户给图的三种方式）

1. **文件夹 + 编号命名**（`图1-外观.jpg`）→ 最省事，直接读
2. **对话里直接上传**，说明"第N张对应第X段"
3. **图未出、占位** → 文案写"此处需图：原理示意图"，先留白，用户后补

## One-Shot Quality Tips（交付时告知用户）

- 先给一页"范例"对齐风格：旧文档/截图，照版式复刻比文字描述准
- 参数用表格给，别揉进句子
- 一次给全，不分批

## Built-in Features（生成后用户可用，无需AI介入）

标注引擎（箭头/圆圈/线型/虚实/说明文字拖动） · 图片与文字框拖拽缩放 · 选区级文字格式化（字体/字号/粗细/颜色/对齐/列表/高亮/斜体/删除线） · 全文字体切换 · 11套主题（含深色自适应） · 图名编辑与显示开关 · 一键重置 · A4/PDF导出（所见即所得） · localStorage 自动保存 · 导出含标注的独立HTML

> 详细功能文档（CSS类名/JS函数/State结构）见 `references/template-features.md`，供深度定制参考。

## Resources

| 路径 | 用途 |
|------|------|
| `scripts/make_doc.py` | 端到端生成器（Python标准库，零安装）。docx → index.html |
| `assets/template.html` | 画册风HTML底座（内联CSS + 标注引擎 + 调整 + 编辑 + 11主题 + PDF打印） |
| `assets/editor.html` | 全功能文档编辑器（全文contentEditable + 增删章节/图片 + 导出HTML/PDF） |
| `references/brief-template.md` | 标准简报模板（引导用户结构化提交参数+配图） |
| `references/template-features.md` | 模板功能详细文档（CSS/JS/State，供深度定制） |
