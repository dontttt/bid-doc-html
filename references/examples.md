# 示例（few-shot）

照下面三种形态对齐输出风格。括号内为模型应产出的 HTML 片段要点。

## 示例 1：单表格型（序号 | 货物名称 | 技术参数+图）

**输入 docx 形态**：一张大表，每行一个产品，第三列是参数文字 + 内嵌图片。

**触发**：`python scripts/make_doc.py 投标参数.docx --layout gallery`

**输出要点**：
- 每个产品 = 一屏区块：左侧参数（`★` 关键项高亮、`规格尺寸` 胶囊样式），右侧 4 列图片画廊
- 顶部「产品配置清单」由各产品名自动生成
- 编号 `01 / 02 / 03` 顺序

```html
<section class="block wrap row product">
  <div class="text">
    <span class="tag">01</span>
    <h2>两门铁衣柜</h2>
    <p class="key">★ 主体 0.8mm 冷轧钢板</p>
    <p class="spec">规格尺寸：高1850×宽900×深420mm</p>
  </div>
  <div class="gallery">
    <span class="imgwrap"><img src="data:image/png;base64,..." alt=""></span>
  </div>
</section>
```

## 示例 2：段落型产品（编号 + 参数项 + 散图）

**输入 docx 形态**：`1两门铁衣柜` 作产品标题，下面跟 `★关键项`、`规格尺寸：...`、参数句，图片散落其后。

**触发**：`python scripts/make_doc.py 投标参数.docx --layout block`

**输出要点**：
- 每个产品标题独立成节；其下「每句参数 + 紧随其后的图」合成一块（图文一体）
- 标题图进 `.hero-gallery`，细节图进 `.b-item-gallery`

```html
<section class="block wrap row product">
  <div class="prod-head">
    <div class="prod-tit text"><span class="tag">01</span><h2>两门铁衣柜</h2></div>
    <div class="hero-gallery">…图…</div>
  </div>
  <div class="items">
    <div class="block-item">
      <div class="btxt text"><p class="key">★ 主体 0.8mm 冷轧钢板</p></div>
      <div class="b-item-gallery">…细节图…</div>
    </div>
  </div>
</section>
```

## 示例 3：无 docx，纯参数 + 图片文件夹

**用户说**：「参数我发你，图放 `D:/bid/图1.jpg` `图2.jpg`，按编号配。」

**做法（路径B）**：
1. 发 `brief-template.md` 让用户填「参数↔配图对应表」
2. Read 图片文件夹确认编号
3. 以 `assets/template.html` 为底座，替换占位符：

```html
<!-- {{TITLE}} → 某某项目产品说明书 -->
<!-- {{HERO_SRC}} → images/图1.jpg -->
<!-- {{INTRO_ITEMS}} → <li>两门铁衣柜</li><li>办公桌</li> -->
<!-- {{SECTIONS}} → 多个 <section class="block wrap">… -->
<!-- {{THEME_CLASS}} → theme-gov （政府国企项目） -->
```

4. 图片 `src="images/图N.jpg"` → 读文件 base64 内嵌为 `src="data:image/...;base64,..."`
5. 验收（见 SKILL.md 交付验收清单）后 `present_files` 交付

> 风格一致性提醒：大图为主、图文并排或上下叠放、留白充足、浅底 + 单一强调色；参数用表格/列表，不揉进句子。
