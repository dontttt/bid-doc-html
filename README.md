# bid-doc-html

把「投标技术参数 + 对应图片」转换成排版精良、图文一一对应的**单文件 HTML 说明书**。

> 适用于：投标产品说明书 / 产品白皮书 / 投标画册 / 参数配图文档。
> 默认画册风（家具介绍风格）、简体中文、图片 base64 内嵌（分享不丢图）、A4 打印友好。

## 特性

- **单文件 HTML**：图片 base64 内嵌，零外部依赖，可直接发给客户/评委。
- **画册风排版**：大图为主、图文并排或上下叠放、留白充足、浅底 + 单一强调色。
- **内嵌标注引擎**：箭头/圆圈指向图片，可调线型粗细/虚实（无需 AI 介入）。
- **图片与文字框拖拽缩放**，选区级文字格式化（字体/字号/粗细/颜色/对齐/列表/高亮）。
- **11 套主题**（含深色自适应），全文字体一键切换。
- **A4 / PDF 导出**（所见即所得），localStorage 自动保存。
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
python scripts/make_doc.py <参数表.docx> [输出目录] [--title "标题"]
```

- 自动解包 docx → 提取图文 → 按编号分章节 → 注入 `assets/template.html` → base64 内嵌图片。
- 输出：`<输出目录>/index.html`（默认 docx 同目录下 `bid-doc/`）。

### 路径 B：你只有参数 + 图片

参考 `references/brief-template.md` 按「参数↔配图对应表」结构化提交，基于 `assets/template.html` 组装。

### 路径 C：编辑已生成的文档

打开 `assets/editor.html` 全功能编辑器，或用 `index.html` 底部工具栏的标注 / 调整 / 编辑模式。

## 文件结构

| 路径 | 用途 |
|------|------|
| `SKILL.md` | 技能定义与完整工作流 |
| `scripts/make_doc.py` | docx → index.html 端到端生成器（Python 标准库） |
| `assets/template.html` | 画册风 HTML 底座（内联 CSS + 标注引擎 + 编辑 + 11 主题 + PDF 打印） |
| `assets/editor.html` | 全功能文档编辑器 |
| `references/brief-template.md` | 标准简报模板 |
| `references/template-features.md` | 模板功能详细文档（CSS/JS/State，供深度定制） |

## 许可

[MIT](./LICENSE) © dontttt
