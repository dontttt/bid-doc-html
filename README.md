# bid-doc-html

把「投标技术参数 + 对应图片」转换成排版精良、图文一一对应的**单文件 HTML 说明书**。

> 适用于：投标产品说明书 / 产品白皮书 / 投标画册 / 参数配图文档。
> 默认画册风（家具介绍风格）、简体中文、图片 base64 内嵌（分享不丢图）、A4 打印友好。

## 特性

- **单文件 HTML**：图片 base64 内嵌，零外部依赖，可直接发给客户/评委。
- **画册风排版**：大图为主、图文并排或上下叠放、留白充足、浅底 + 单一强调色。
- **内嵌标注引擎**：箭头/圆圈指向图片，可调线型粗细/虚实（无需 AI 介入）。
- **图片与文字框拖拽缩放**，选区级文字格式化（字体/字号/粗细/颜色/对齐/列表/高亮）。
- **11 套主题**（含深色自适应），全文字体一键切换；右下角「🎨 主题」一键预览悬浮条，11 套主题带名称即时切换。
- **生成的 `index.html` 也能当模板**：编辑模式下可「＋ 添加章节 / ✕ 删除章节」、图片「替换 / 删除 / 上传」（自动压缩）。
- **A4 / PDF 导出**（所见即所得），localStorage 自动保存。
- **模板工作台 `editor.html`**：开箱即带投标骨架（封面+配置清单+示例章节），可任意增删/替换章节与图片、导入↔导出 HTML 形成编辑闭环；上传图片自动压缩（≤1600px / JPEG 0.85）控制体积。
- **零依赖生成**：`scripts/make_doc.py` 仅用 Python 标准库，无需 `pip install`。

## 安装（作为 WorkBuddy 技能）

```bash
# 方式一：用户级（所有项目可用）
git clone https://github.com/dontttt/bid-doc-html.git ~/.workbuddy/skills/bid-doc-html

# 方式二：项目级（团队共享）
git clone https://github.com/dontttt/bid-doc-html.git <你的项目>/.workbuddy/skills/bid-doc-html
```

安装后，在对话中触发关键词即可调用：`投标说明书`、`产品白皮书`、`投标画册`、`参数配图文档`。

## 使用

### 路径 A：你已有参数表 docx（推荐）

```bash
python scripts/make_doc.py <参数表.docx> [输出目录] \
  [--title "标题"] [--layout gallery|block] [--theme gov] [--accent #c0392b] [--json]
```

- 自动探测文档形态（单表格 / 段落型产品 / 传统章节）并选对应解析器。
- 自动解包 docx → 提取图文 → 按编号分章节 → 注入 `assets/template.html` → base64 内嵌图片。
- 输出：`<输出目录>/index.html`（默认 docx 同目录下 `bid-doc/`）。
- `--theme gov` 适合政府/国企项目；`--accent #c0392b` 自定义强调色；`--json` 输出机器可读摘要。

### 路径 B：你只有参数 + 图片

参考 `references/brief-template.md` 按「参数↔配图对应表」结构化提交，基于 `assets/template.html` 组装。

### 路径 C：当作"模板工作台"长期精修（推荐）

直接打开 `assets/editor.html`（复制一份到你的项目目录即专属模板）：
- 改文字：点任意文字即编辑；增删章节/图片：底部「+ 添加章节」、图片悬停「替换·删除」。
- 导出闭环：「📥 导出 HTML」产出单文件成品；「📤 导入 HTML」把成品读回继续改。
- 图片上传自动压缩，避免成品体积爆炸。

> `index.html`（docx 生成物）仅适合轻量标注/调整与打印，不可增删章节图片、重跑会覆盖——精修请用 editor.html。

## 测试与校验

```bash
# 全套自检（推荐，一条命令跑完：make_doc 自测 + 生成校验 + editor 契约检查）
python tests/run_all.py

# 单独运行
python scripts/make_doc.py --self-test              # 内置冒烟测试（解析/生成/base64）
python tests/validate_output.py <输出目录>/index.html [--json]   # 校验交付基线
```

## 文件结构

| 路径 | 用途 |
|------|------|
| `SKILL.md` | 技能定义与完整工作流（含何时不用 / Quick Start / 验收清单） |
| `scripts/make_doc.py` | docx → index.html 端到端生成器（Python 标准库，含 `--self-test`/`--json`） |
| `assets/template.html` | 画册风 HTML 底座（内联 CSS + 标注引擎 + 编辑 + 11 主题 + PDF 打印） |
| `assets/editor.html` | 全功能文档编辑器 / 模板工作台（开箱投标骨架 + 增删章节图片 + 导入导出闭环 + 图片压缩） |
| `references/brief-template.md` | 标准简报模板 |
| `references/template-features.md` | 模板功能详细文档（CSS/JS/State，供深度定制） |
| `references/examples.md` | few-shot 示例（三种输入形态 → 输出片段） |
| `tests/validate_output.py` | 生成产物校验脚本（CI / 人工复检） |

## 许可

[MIT](./LICENSE) © dontttt
