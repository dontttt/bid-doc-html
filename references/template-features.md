# Template Features 详细文档

> 供深度定制参考。正常使用无需阅读——make_doc.py 和 editor.html 已封装全部功能。

## 标注引擎（Annotation）

SVG overlay 实现，坐标按百分比存储（缩放/手机端不偏移）。

- **标注模式**开关：`body.annot-on` 类控制。开启后 `.annotools` 子菜单展开。
- **工具**：箭头（`<line>` + `<marker>` 箭头）、圆圈（`<ellipse>`）。从文字处拖到图片要点处画出。
- **说明文字**：绘制后 `prompt()` 填写。留空只显示图形；有文字时显示且可拖动（坐标 `lx/ly`）。
- **线型粗细**：`STATE.lineW`，三档 1.5/2.4/3.5px。
- **虚实线**：`STATE.dash`，`stroke-dasharray` 控制。
- **当前工具高亮**：`data-tool` + `markActiveTool()`，蓝色内框。
- **撤销/清空**：`STATE.shapes.pop()` / `STATE.shapes=[]`。
- **持久化**：`localStorage('bid_state_v1')`，导出时序列化到 `window.__EMBEDDED_STATE__`。
- **CSS 类**：`.anno`（SVG overlay）、`.aarrow`（箭头线）、`.ashape`（圆圈）、`.alabel`（文字标签）。

## 调整模式（Layout Adjustment）

`body.adj-on` 类控制。图片和文字框右下角出现缩放手柄 `.rs`。

- **图片**：拖主体平移（`STATE.imgs[iid].tx/ty`），拖手柄缩放宽度（`STATE.imgs[iid].w`）。作用于 `.imgwrap` 包裹层。
- **文字框**：拖主体平移（`STATE.texts[iid].tx/ty`），拖手柄缩放宽高（`STATE.texts[iid].w/h`）。高度超内容时内部滚动。
- 覆盖范围：封面标题/副标题、配置清单、各章节正文——全文覆盖。

## 编辑模式（Text Editing）

`body.edit-on` 类控制。所有 `.text` 块变为 `contenteditable`。

- **直接编辑**：点击文字即可修改，聚焦时有强调色 outline。
- **选区级格式化**（`fmt-bar` 顶部工具条）：
  - 字体：`execFontStyle('fontFamily', value)` 包裹 `<span style="font-family:...">`
  - 字号：同上，`fontSize`，档位 12/14/16/18/20/24/32px
  - 粗细：同上，`fontWeight`，档位 300-900
  - 加粗：`document.execCommand('bold')`（原生 `<b>`/`<strong>` toggle）
  - 下划线：`document.execCommand('underline')`
  - 颜色：8 预设色块 + `<input type="color">` 取色器
- **跨元素选区**：`surroundContents` 失败时降级为 `extractContents` + `insertNode`。
- **清除格式**：`stripFormatting()` 用 TreeWalker 剥离 `<span>/<b>/<strong>/<u>/<font>`。
- 编辑模式与标注/调整模式互斥。

## 全局字体（Global Font）

- CSS 变量 `--font` 挂载到 `body`，`body.style.setProperty('--font', value)`。
- 可选：SimSun/SimHei/KaiTi/Microsoft YaHei/FangSong/Arial。
- 存于 `STATE.font`，独立于选区级格式化。

## 主题（Themes）

11 套预设，CSS 变量覆盖（`body.theme-*` 类）：

| 主题 | 类名 | 强调色 | 适用场景 |
|------|------|--------|---------|
| 青绿（默认） | `theme-""` | `#0f766e` | 通用 |
| 暖木家具 | `theme-wood` | `#9c6b3f` | 家具/家居 |
| 科技蓝 | `theme-tech` | `#1d4ed8` | 软硬件/科技 |
| 简约黑白 | `theme-mono` | `#111` | 极简 |
| 政务红 | `theme-gov` | `#c0392b` | 政府/国企 |
| 薄荷绿 | `theme-mint` | `#10b981` | 清新明亮 |
| 活力橙 | `theme-orange` | `#ea580c` | 年轻活力 |
| 暗夜深蓝 | `theme-dark` | `#38bdf8` | 深色/高端 |
| 莫兰迪 | `theme-morandi` | `#7d8a7f` | 低饱和高级 |
| 雅紫 | `theme-purple` | `#7c3aed` | 文创/教育 |
| 大地卡其 | `theme-khaki` | `#92711f` | 自然质朴 |

CSS 变量（7+1 个）：`--accent`/`--bg`/`--ink`/`--muted`/`--accent-soft`/`--accent-ink`/`--line`/`--img-bg`。

**深色主题自适应**：`theme-dark` 时 body 背景独立覆盖 `#0a0f1e`，所有文字用 `var(--muted)`/`var(--ink)`，标注标签描边用 `var(--bg)`，工具栏按钮背景用 `var(--accent-soft)`。

## 图名编辑（Caption Editing）

- `figcaption` 在编辑/标注模式下 `contenteditable`，内容存 `STATE.captions[iid]`。
- 显示开关：`STATE.showCaptions`（默认 true），工具条按钮切换。

## A4 / PDF

- `.page` 容器：`width:210mm; min-height:297mm`。
- `@media print`：`@page{size:A4;margin:0}`，`page-break-inside:avoid`。
- `print-color-adjust:exact` 保留主题色（所有元素）。
- 导出 PDF：浏览器打印 → 另存为 PDF → A4 → 边距 0 → 勾选背景图形。

## 重置（Reset）

红色按钮 + `confirm()` 确认。清空：`STATE.shapes`/`imgs`/`texts`/`captions`，恢复 `lineW=2.4`/`dash=false`/`showCaptions=true`/`font=""`，DOM 同步还原（`stripFormatting()` + 清除内联样式）。

## State 结构

```javascript
STATE = {
  shapes: [{r, tool, x1, y1, x2, y2, label, lx, ly}],  // 标注
  imgs:   {iid: {tx, ty, w}},                           // 图片调整
  texts:  {iid: {tx, ty, w, h}},                        // 文字框调整
  captions: {iid: "文字"},                               // 图名编辑
  theme: "",                                            // 主题
  lineW: 2.4,                                           // 线宽
  dash: false,                                          // 虚线
  showCaptions: true,                                   // 图名开关
  font: ""                                              // 全局字体
}
```

持久化：`localStorage('bid_state_v1')`。导出：序列化到 `window.__EMBEDDED_STATE__`。

## editor.html 编辑器

全功能文档编辑器，数据驱动架构（`doc` 对象 → `renderAll()` → DOM）。

- **数据模型**：`doc = {meta, heroImg, intro, sections: [{id, title, body, images: []}]}`
- **文字编辑**：所有文字 `contentEditable`，`data-bind` 属性 + `syncBind()`/`setByPath()` 自动同步。
- **章节管理**：`addSectionAt(idx)` / `moveSection(id, dir)` / `deleteSection(id)` / `renumber()`。
- **图片管理**：`pickImage()` → `fileToBase64()` → 追加到 section。悬停显示替换/删除按钮。
- **格式化**：`buildFmtBar()` 构建 fmt-bar，包含对齐/列表/高亮/斜体/删除线/清除格式等。
- **图片缩放**：`<i class="rs">` 手柄，`.media:hover .rs` 悬停显示。
- **导出**：`exportDoc()` 生成自包含 HTML（CSS 提取 + 数据内嵌 base64）。
- **自动保存**：`scheduleSave()` 800ms 防抖，`localStorage('bid_editor_doc')`。
- **PDF 导出**：`exportPdf()` → `window.print()`，`showPdfHint()` 操作指引蒙层。

### execCommand 支持

| 命令 | 功能 |
|------|------|
| `bold` | 加粗 toggle |
| `italic` | 斜体 toggle |
| `underline` | 下划线 toggle |
| `strikeThrough` | 删除线 toggle |
| `removeFormat` | 清除格式 |
| `justifyLeft/Center/Right/Full` | 对齐 |
| `insertUnorderedList` | 无序列表 |
| `insertOrderedList` | 有序列表 |
| `outdent/indent` | 缩进 |
