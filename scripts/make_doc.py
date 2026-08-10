# -*- coding: utf-8 -*-
"""
bid-doc-html 生成器（技能自带，可独立运行，Python 标准库，零安装）

用法:
  python make_doc.py <参数表.docx> [输出目录]
      [--title "自定义标题"] [--layout gallery|block]
      [--theme wood|tech|gov|...] [--accent #c0392b]
      [--json] [--self-test] [--help]

输出: <输出目录>/index.html （单文件，图片 base64 内嵌）+ <输出目录>/images/

示例:
  python make_doc.py 投标参数.docx ./out --title "XX项目产品说明书" --theme gov
  python make_doc.py 投标参数.docx --self-test     # 内部冒烟测试，不依赖真实文件
"""
import sys, os, re, json, base64, zipfile, argparse
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

MIME = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp"}

THEME_NAMES = {"", "wood", "tech", "mono", "gov", "mint", "orange",
               "dark", "morandi", "purple", "khaki"}

# 全局选项（由 argparse 注入，供 finalize 使用）
_OPT = {"theme": "", "accent": None}


# ---------- 颜色工具（--accent 推导强调色三件套） ----------
def _hex2rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb2hex(rgb):
    return "#" + "".join("%02x" % max(0, min(255, int(v))) for v in rgb)


def _mix(h, target, t):
    r = _hex2rgb(h)
    return _rgb2hex(tuple(r[i] + (target[i] - r[i]) * t for i in range(3)))


def _is_hex(s):
    return bool(re.match(r'^#?[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$', s or ""))


# ---------- 基础工具 ----------
def text_of(p):
    return "".join(t.text or "" for t in p.iter(W + "t"))


HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "template.html")


def _warn(msg):
    print("[warn] " + msg, file=sys.stderr)


def finalize(html):
    """注入主题类与自定义强调色，并返回最终 HTML。"""
    tc = ("theme-" + _OPT["theme"]) if _OPT["theme"] else ""
    html = html.replace("{{THEME_CLASS}}", tc)
    if _OPT["accent"]:
        a = _OPT["accent"]
        soft = _mix(a, (255, 255, 255), 0.82)
        ink = _mix(a, (0, 0, 0), 0.35)
        css = (":root{--accent:" + a + ";--accent-soft:" + soft + ";--accent-ink:" + ink + ";}\n"
               "body{--accent:" + a + "!important;--accent-soft:" + soft + "!important;--accent-ink:" + ink + "!important;}\n")
        html = html.replace("</style>", css + "</style>")
    return html


def extract(docx_path, out_dir):
    """提取 docx 文本与图片，返回 blocks 列表与封面图。"""
    img_dir = os.path.join(out_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    z = zipfile.ZipFile(docx_path)
    rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
    rid2target = {r.get("Id"): r.get("Target") for r in rels}

    media = [n for n in z.namelist()
             if n.startswith("word/media/") and not n.endswith("/") and os.path.splitext(n)[1]]
    renamed = {}
    cnt = 0

    def ensure_name(orig):
        nonlocal cnt
        if orig in renamed:
            return renamed[orig]
        cnt += 1
        ext = os.path.splitext(orig)[1].lower()
        new = f"图{cnt}{ext}"
        renamed[orig] = new
        try:
            with open(os.path.join(img_dir, new), "wb") as f:
                f.write(z.read("word/media/" + os.path.basename(orig)))
        except KeyError:
            _warn("图片缺失，跳过: " + orig)
        return new

    doc = ET.fromstring(z.read("word/document.xml"))
    body = doc.find(W + "body")

    blocks = []
    for el in body:
        tag = el.tag.split('}')[-1]
        if tag == "p":
            txt = text_of(el).strip()
            imgs = []
            for blip in el.iter(A + "blip"):
                rid = blip.get(R + "embed")
                if rid and rid in rid2target:
                    imgs.append(ensure_name(os.path.basename(rid2target[rid])))
            style = ""
            ppr = el.find(W + "pPr")
            if ppr is not None:
                ps = ppr.find(W + "pStyle")
                if ps is not None:
                    style = ps.get(W + "val") or ""
            if txt or imgs:
                blocks.append({"text": txt, "images": imgs, "style": style})
        elif tag == "tbl":
            ttxt, timgs = [], []
            for p in el.iter(W + "p"):
                t = text_of(p).strip()
                if t:
                    ttxt.append(t)
                for blip in p.iter(A + "blip"):
                    rid = blip.get(R + "embed")
                    if rid and rid in rid2target:
                        timgs.append(ensure_name(os.path.basename(rid2target[rid])))
            blocks.append({"text": " | ".join(ttxt), "images": timgs, "style": "table", "is_table": True})
    return blocks


def group(blocks, title_override=None):
    title = title_override or "投标产品说明书"
    subtitle = "依据投标技术参数生成，逐项响应，附细节图示。"
    intro = ""
    sections = []
    current = None
    cover_images = []

    for b in blocks:
        text = (b.get("text") or "").strip()
        imgs = b.get("images") or []
        if not title_override and text and len(sections) == 0 and not current and not cover_images and not intro:
            if len(text) > 4:
                title = text
                continue
        if text.startswith("包含") or (not sections and not current and text and "：" in text[:30]):
            intro = text
            continue
        m = re.match(r'^(\d+)[、.．](.*)$', text)
        if m and text not in ("图",):
            after = m.group(2)
            is_sub = bool(after) and after[0].isdigit() and "." in after[:3]
            if is_sub:
                if current is None:
                    current = {"title": "产品参数", "paras": [], "images": []}
                    sections.append(current)
                current["paras"].append("◆ " + text)
                if imgs:
                    current["images"].extend(imgs)
                continue
            current = {"title": text, "paras": [], "images": []}
            sections.append(current)
            if imgs:
                current["images"].extend(imgs)
            continue
        if imgs:
            if current is None:
                cover_images.extend(imgs)
            else:
                current["images"].extend(imgs)
        if text and text != "图":
            if current is not None:
                current["paras"].append(text)

    if cover_images and sections and re.match(r'^1[、.．]', sections[0]["title"]):
        for im in reversed(cover_images):
            if im not in sections[0]["images"]:
                sections[0]["images"].insert(0, im)
    return title, subtitle, intro, sections, cover_images


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def para_html(p):
    p = p.strip()
    if p.startswith("◆"):
        return f'<p class="sub">{esc(p[1:].strip())}</p>'
    if p.startswith("★"):
        return f'<p class="key">{esc(p)}</p>'
    return f'<p>{esc(p)}</p>'


def render_para(p):
    """渲染参数段落：兼容字符串（旧表格路径）与 (cls,text) 元组（段落路径）。"""
    if isinstance(p, (tuple, list)):
        cls, txt = p[0], p[1]
    else:
        txt = p
        cls = "key" if txt.startswith("★") else ("spec" if txt.startswith("规格尺寸") else "para")
    txt = esc(txt.strip())
    if cls == "key":
        return f'<p class="key">{txt}</p>'
    if cls == "spec":
        return f'<p class="spec">{txt}</p>'
    if cls == "sub":
        return f'<p class="sub">{txt}</p>'
    return f'<p>{txt}</p>'


def media_html(imgs):
    seen, uniq = set(), []
    for i in imgs:
        if i not in seen:
            seen.add(i); uniq.append(i)
    imgs = uniq
    if not imgs:
        return ""
    if len(imgs) == 1:
        return (f'<figure class="media"><span class="imgwrap">'
                f'<img src="images/{esc(imgs[0])}" alt=""><i class="rs"></i></span>'
                f'<figcaption>{esc(imgs[0])}</figcaption></figure>')
    grid = "".join(f'<span class="imgwrap"><img src="images/{esc(i)}" alt=""><i class="rs"></i></span>' for i in imgs)
    caps = "　".join(imgs)
    return (f'<figure class="media"><div class="grid2">{grid}</div>'
            f'<figcaption>{esc(caps)}</figcaption></figure>')


def build(blocks, out_dir, title_override=None):
    title, subtitle, intro, sections, cover_images = group(blocks, title_override)
    sec_html = []
    for idx, s in enumerate(sections):
        num = re.match(r'^(\d+(?:\.\d+)?)', s["title"])
        num = num.group(1) if num else str(idx + 1)
        name = re.sub(r'^\d+(?:\.\d+)*[.、 ]?', '', s["title"]).strip() or s["title"]
        paras = "".join(para_html(p) for p in s["paras"])
        media = media_html(s["images"])
        reverse = " reverse" if idx % 2 == 1 else ""
        sec_html.append(f'''
  <section class="block wrap">
    <div class="row{reverse}">
      <div class="text">
        <span class="tag">{esc(num)}</span>
        <h2>{esc(name)}</h2>
        {paras}
      </div>
      {media}
    </div>
  </section>''')

    intro_items = ""
    if intro:
        for it in re.split(r'[，,]', intro):
            it = it.strip()
            if it:
                intro_items += f"<li>{esc(it)}</li>"
    else:
        for s in sections:
            t = re.sub(r'^\d+[、.．]', '', s["title"]).strip()
            intro_items += f"<li>{esc(t)}</li>"

    html = open(TEMPLATE, encoding="utf-8").read()
    html = html.replace("{{TITLE}}", esc(title))
    html = html.replace("{{SUBTITLE}}", esc(subtitle))
    html = html.replace("{{HERO_SRC}}", "images/" + esc(cover_images[0] if cover_images else ""))
    html = html.replace("{{INTRO_ITEMS}}", intro_items)
    html = html.replace("{{SECTIONS}}", "".join(sec_html))

    img_dir = os.path.join(out_dir, "images")

    def embed(m):
        fn = m.group(1)
        p = os.path.join(img_dir, fn)
        if os.path.exists(p):
            ext = fn.rsplit(".", 1)[1].lower()
            mime = MIME.get(ext, "image/png")
            data = base64.b64encode(open(p, "rb").read()).decode()
            return f'src="data:{mime};base64,{data}"'
        return m.group(0)

    html = re.sub(r'src="images/([^"]+)"', embed, html)
    html = finalize(html)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    return title, len(sections), round(len(html) / 1024, 1)


def extract_table_products(docx_path, out_dir):
    """解析「序号 | 货物名称 | 技术参数要求+图片」型单表格。"""
    img_dir = os.path.join(out_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    z = zipfile.ZipFile(docx_path)
    rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
    rid2target = {r.get("Id"): r.get("Target") for r in rels}
    renamed, cnt = {}, 0

    def ensure_name(orig):
        nonlocal cnt
        if orig in renamed:
            return renamed[orig]
        cnt += 1
        ext = os.path.splitext(orig)[1].lower() or ".png"
        new = f"图{cnt}{ext}"
        try:
            with open(os.path.join(img_dir, new), "wb") as f:
                f.write(z.read("word/media/" + os.path.basename(orig)))
        except KeyError:
            _warn("图片缺失，跳过: " + orig)
        renamed[orig] = new
        return new

    doc = ET.fromstring(z.read("word/document.xml"))
    body = doc.find(W + "body")
    table = body.find(W + "tbl")
    if table is None:
        return []
    products = []
    for row in table.iter(W + "tr"):
        tcs = list(row.iter(W + "tc"))
        if len(tcs) < 3:
            continue
        seq = " ".join(text_of(p) for p in tcs[0].iter(W + "p")).strip()
        name = " ".join(text_of(p) for p in tcs[1].iter(W + "p")).strip()
        param = tcs[2]
        paras = [text_of(p).strip() for p in param.findall(W + "p")]
        paras = [p for p in paras if p]
        imgs, seen = [], set()
        for blip in param.iter(A + "blip"):
            rid = blip.get(R + "embed")
            if rid and rid in rid2target:
                fn = os.path.basename(rid2target[rid])
                if fn not in seen:
                    seen.add(fn)
                    imgs.append(ensure_name(fn))
        if not name or name == "货物名称":
            continue
        products.append({"seq": seq, "name": name, "paras": paras, "images": imgs})
    return products


def classify_para(t):
    """段落型投标参数：区分产品标题 / 关键项 / 规格 / 子项 / 普通项。"""
    if re.match(r'^\d+[一-鿿]+$', t):          # 无分隔符 + 纯中文 = 顶层产品标题，如「1两门铁衣柜」
        return 'product'
    if t.startswith('★'):
        return 'key'
    if t.startswith('规格尺寸'):
        return 'spec'
    if re.match(r'^\d+[、.．]', t):            # 「N、子项：」或「N.N子项」= 子标题；长描述 = 普通参数项
        if t.endswith('：') or t.endswith(':') or len(t) <= 14:
            return 'sub'
        return 'para'
    return 'para'


def extract_para_products(docx_path, out_dir):
    """解析「段落型」投标参数：产品标题 + 规格 + 编号参数项 + 散落的图片。"""
    img_dir = os.path.join(out_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    z = zipfile.ZipFile(docx_path)
    rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
    rid2target = {r.get("Id"): r.get("Target") for r in rels}
    renamed, cnt = {}, 0

    def ensure_name(orig):
        nonlocal cnt
        if orig in renamed:
            return renamed[orig]
        cnt += 1
        ext = os.path.splitext(orig)[1].lower() or ".png"
        new = f"图{cnt}{ext}"
        try:
            with open(os.path.join(img_dir, new), "wb") as f:
                f.write(z.read("word/media/" + os.path.basename(orig)))
        except KeyError:
            _warn("图片缺失，跳过: " + orig)
        renamed[orig] = new
        return new

    doc = ET.fromstring(z.read("word/document.xml"))
    body = doc.find(W + "body")
    products, current, pending = [], None, []
    cumul = None
    for el in body:
        if el.tag.split('}')[-1] != "p":
            continue
        t = text_of(el).strip()
        imgs = []
        for blip in el.iter(A + "blip"):
            rid = blip.get(R + "embed")
            if rid and rid in rid2target:
                imgs.append(ensure_name(os.path.basename(rid2target[rid])))
        cls = classify_para(t) if t else 'img'
        if cls == 'product':
            seq = re.match(r'^(\d+)', t).group(1)
            name = re.sub(r'^\d+[、.．]?', '', t).strip()
            current = {"seq": seq, "name": name, "paras": [], "images": [],
                       "blocks": [], "header_imgs": []}
            if pending:
                current["header_imgs"].extend(pending)
                current["images"].extend(pending)
                pending = []
            products.append(current)
            cumul = None
            continue
        if current is None:
            current = {"seq": "", "name": "概述", "paras": [], "images": [],
                       "blocks": [], "header_imgs": []}
            products.append(current)
            cumul = None
        if t:
            blk = {"cls": cls, "text": t, "images": []}
            current["blocks"].append(blk)
            current["paras"].append((cls, t))
            cumul = blk
        else:
            for im in imgs:
                if cumul is not None:
                    cumul["images"].append(im)
                    if im not in current["images"]:
                        current["images"].append(im)
                elif current is not None and not current["blocks"]:
                    current["header_imgs"].append(im)
                    if im not in current["images"]:
                        current["images"].append(im)
                else:
                    if im not in pending:
                        pending.append(im)
    return products


def build_table(products, out_dir, title_override=None):
    """表格型文档：每个产品=参数块+图片画廊。"""
    title = title_override or "投标产品说明书"
    subtitle = "依据投标技术参数逐项响应，含整体外观与细节图示。"
    img_dir = os.path.join(out_dir, "images")

    def b64(fn):
        p = os.path.join(img_dir, fn)
        if os.path.exists(p):
            ext = fn.rsplit(".", 1)[1].lower()
            return f'data:{MIME.get(ext, "image/png")};base64,' + base64.b64encode(open(p, "rb").read()).decode()
        return ""

    sec_html, intro_items = [], ""
    for prod in products:
        try:
            num = f"{int(prod['seq']):02d}"
        except ValueError:
            num = prod["seq"]
        paras = "".join(render_para(p) for p in prod["paras"])
        gallery = "".join(
            f'<span class="imgwrap"><img src="{b64(im)}" alt=""><i class="rs"></i></span>'
            for im in prod["images"]
        )
        intro_items += f"<li>{esc(prod['name'])}</li>"
        sec_html.append(f'''
  <section class="block wrap row product">
    <div class="text">
      <span class="tag">{esc(num)}</span>
      <h2>{esc(prod['name'])}</h2>
      {paras}
    </div>
    <div class="gallery">{gallery}</div>
  </section>''')

    hero = products[0]["images"][0] if products and products[0]["images"] else ""
    html = open(TEMPLATE, encoding="utf-8").read()
    html = html.replace("{{TITLE}}", esc(title))
    html = html.replace("{{SUBTITLE}}", esc(subtitle))
    html = html.replace("{{HERO_SRC}}", "images/" + esc(hero))
    html = html.replace("{{INTRO_ITEMS}}", intro_items)
    html = html.replace("{{SECTIONS}}", "".join(sec_html))

    extra = '''
  .row.product{display:block;}
  .product .text{max-width:100%;margin-bottom:22px;}
  .product .text h2{font-size:clamp(22px,3vw,30px);}
  .product .text p{color:var(--ink);font-size:14px;line-height:1.75;margin:9px 0;}
  .product .text p.spec{background:var(--accent-soft);color:var(--accent-ink);
    border-left:3px solid var(--accent);border-radius:0 8px 8px 0;
    padding:10px 14px;font-weight:600;margin:10px 0 18px;}
  .product .gallery{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:6px;}
  .product .gallery .imgwrap{position:relative;display:block;width:100%;line-height:0;}
  .product .gallery .imgwrap img{width:100%;border-radius:10px;display:block;
    background:var(--img-bg);box-shadow:0 6px 16px rgba(0,0,0,.07);object-fit:contain;max-height:230px;}
  @media (max-width:760px){ .product .gallery{grid-template-columns:repeat(2,1fr);} }
'''
    html = html.replace("</style>", extra + "\n</style>")
    html = re.sub(r'src="images/([^"]+)"',
                  lambda m: f'src="{b64(m.group(1).split("/")[-1])}"' if os.path.exists(
                      os.path.join(img_dir, m.group(1).split("/")[-1])) else m.group(0), html)
    html = finalize(html)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    return title, len(products), round(len(html) / 1024, 1)


def render_block_item(b):
    """渲染单块：文字段 + 紧随其后的图片（图文一体）。"""
    cls = b.get("cls", "para")
    t = esc(b.get("text", ""))
    if cls == 'key':
        txt = f'<p class="key">{t}</p>'
    elif cls == 'spec':
        txt = f'<p class="spec">{t}</p>'
    elif cls == 'sub':
        txt = f'<p class="sub">{t}</p>'
    else:
        txt = f'<p>{t}</p>'
    gallery = "".join(
        f'<span class="imgwrap"><img src="images/{esc(im)}" alt=""><i class="rs"></i></span>'
        for im in b.get("images", [])
    )
    if gallery:
        return (f'<div class="block-item">'
                f'<div class="btxt text">{txt}</div>'
                f'<div class="b-item-gallery">{gallery}</div>'
                f'</div>')
    return f'<div class="block-item"><div class="btxt text">{txt}</div></div>'


def build_blocks(products, out_dir, title_override=None):
    """段落型文档（块布局）：每句话 + 其后图片 = 一块内容。"""
    title = title_override or "投标产品说明书"
    subtitle = "依据投标技术参数逐项响应，含整体外观与细节图示。"
    img_dir = os.path.join(out_dir, "images")

    def b64(fn):
        p = os.path.join(img_dir, fn)
        if os.path.exists(p):
            ext = fn.rsplit(".", 1)[1].lower()
            return f'data:{MIME.get(ext, "image/png")};base64,' + base64.b64encode(open(p, "rb").read()).decode()
        return ""

    sec_html, intro_items = [], ""
    for prod in products:
        try:
            num = f"{int(prod['seq']):02d}"
        except ValueError:
            num = prod["seq"]
        intro_items += f"<li>{esc(prod['name'])}</li>"
        header_gal = "".join(
            f'<span class="imgwrap"><img src="images/{esc(im)}" alt=""><i class="rs"></i></span>'
            for im in prod.get("header_imgs", [])
        )
        items = "".join(render_block_item(b) for b in prod.get("blocks", []))
        sec_html.append(f"""
  <section class="block wrap row product">
    <div class="prod-head">
      <div class="prod-tit text">
        <span class="tag">{esc(num)}</span>
        <h2>{esc(prod['name'])}</h2>
      </div>
      <div class="hero-gallery">{header_gal}</div>
    </div>
    <div class="items">{items}</div>
  </section>""")

    hero = ""
    for prod in products:
        if prod.get("header_imgs"):
            hero = prod["header_imgs"][0]
            break
    if not hero and products and products[0].get("images"):
        hero = products[0]["images"][0]

    html = open(TEMPLATE, encoding="utf-8").read()
    html = html.replace("{{TITLE}}", esc(title))
    html = html.replace("{{SUBTITLE}}", esc(subtitle))
    html = html.replace("{{HERO_SRC}}", "images/" + esc(hero))
    html = html.replace("{{INTRO_ITEMS}}", intro_items)
    html = html.replace("{{SECTIONS}}", "".join(sec_html))

    extra = """
  .row.product{display:block;}
  .prod-head{border-bottom:2px solid var(--accent);padding-bottom:14px;margin-bottom:10px;}
  .prod-head .tag{color:var(--accent);font-size:12.5px;letter-spacing:.18em;display:block;margin-bottom:6px;font-weight:800;}
  .prod-head h2{font-size:clamp(22px,3vw,30px);margin:0;}
  .hero-gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-top:16px;}
  .hero-gallery .imgwrap img{max-height:300px;}
  .items{margin-top:6px;}
  .block-item{margin:0 0 20px;break-inside:avoid;}
  .block-item .btxt p{margin:8px 0;font-size:14px;line-height:1.75;color:var(--ink);}
  .block-item .btxt p.spec{background:var(--accent-soft);color:var(--accent-ink);
    border-left:3px solid var(--accent);padding:9px 12px;border-radius:0 8px 8px 0;font-weight:600;}
  .block-item .btxt p.key{background:var(--accent-soft);border-left:3px solid var(--accent);
    padding:9px 12px;border-radius:0 8px 8px 0;color:var(--accent-ink);font-weight:600;}
  .block-item .btxt p.sub{font-weight:800;color:var(--ink);font-size:15px;margin:14px 0 4px;}
  .b-item-gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:8px;}
  .b-item-gallery .imgwrap img{max-height:240px;}
  @media (max-width:760px){ .hero-gallery,.b-item-gallery{grid-template-columns:repeat(2,1fr);} }
"""
    html = html.replace("</style>", extra + "\n</style>")
    html = re.sub(r'src="images/([^"]+)"',
                  lambda m: f'src="{b64(m.group(1).split("/")[-1])}"' if os.path.exists(
                      os.path.join(img_dir, m.group(1).split("/")[-1])) else m.group(0), html)
    html = finalize(html)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    return title, len(products), round(len(html) / 1024, 1)


# ---------- 自测：构造最小 docx，断言关键产物 ----------
def _build_sample_docx(path):
    """写一份最小、脚本可解析的 docx（段落 + 内嵌图片），仅供 --self-test。"""
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC")
    ct = ('<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Default Extension="png" ContentType="image/png"/>'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')
    drels = ('<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>'
             '</Relationships>')
    doc = ('<?xml version="1.0"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
           'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
           'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
           'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
           '<w:body>'
           '<w:p><w:r><w:t>1、产品概述</w:t></w:r></w:p>'
           '<w:p><w:r><w:t>型号 ABC-100，适用场景广泛。</w:t></w:r></w:p>'
           '<w:p><w:r><w:t>2、技术参数</w:t></w:r></w:p>'
           '<w:p><w:r><w:t>处理量 ≥ 1000 t/h。</w:t></w:r></w:p>'
           '<w:p><w:r><w:drawing><wp:inline><wp:docPr/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
           '<pic:pic><pic:blipFill><a:blip r:embed="rId1"/></pic:blipFill><pic:spPr/></pic:pic>'
           '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
           '</w:body></w:document>')
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/_rels/document.xml.rels", drels)
        z.writestr("word/document.xml", doc)
        z.writestr("word/media/image1.png", png)


def self_test():
    import tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="bid_selftest_")
    try:
        docx = os.path.join(tmp, "sample.docx")
        _build_sample_docx(docx)
        out = os.path.join(tmp, "out")
        blocks = extract(docx, out)
        title, nsec, size = build(blocks, out, "自测说明书")
        html_path = os.path.join(out, "index.html")
        html = open(html_path, encoding="utf-8").read()
        checks = {
            "无残留占位符 {{...}}": "{{" not in html,
            "生成了章节区块": 'class="block' in html,
            "图片已 base64 内嵌": "data:image" in html,
            "封面图已写入": 'src="data:image' in html,
        }
        ok = all(checks.values())
        print("=== bid-doc-html 自测 ===")
        for k, v in checks.items():
            print(("  [PASS] " if v else "  [FAIL] ") + k)
        print(f"  标题={title} 章节数={nsec} 大小={size}KB")
        print("结果: " + ("PASS ✅" if ok else "FAIL ❌"))
        return ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(
        prog="make_doc.py",
        description="投标参数 docx → 画册风单文件 HTML 说明书（图片 base64 内嵌）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
               "  python make_doc.py 投标参数.docx ./out --title \"XX项目产品说明书\" --theme gov\n"
               "  python make_doc.py 投标参数.docx --self-test")
    ap.add_argument("docx", nargs="?", help="参数表 .docx 路径")
    ap.add_argument("out", nargs="?", help="输出目录（默认 docx 同目录下 bid-doc/）")
    ap.add_argument("--title", help="自定义文档标题")
    ap.add_argument("--layout", choices=["gallery", "block"], default="gallery",
                    help="表格/段落型文档的布局：gallery=图文画廊(默认)，block=逐句配图块")
    ap.add_argument("--theme", choices=sorted(THEME_NAMES - {""}),
                    help="预设主题：wood/tech/gov/mint/orange/dark/morandi/purple/khaki/mono（默认青绿）")
    ap.add_argument("--accent", help="自定义强调色十六进制，如 #c0392b（覆盖主题色）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果摘要（便于自动化/评测）")
    ap.add_argument("--self-test", action="store_true", help="运行内置冒烟测试后退出（不依赖真实文件）")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(0 if self_test() else 1)

    if not args.docx:
        ap.error("缺少参数：docx 文件路径")
    if not os.path.exists(args.docx):
        ap.error(f"文件不存在：{args.docx}")
    if not args.docx.lower().endswith(".docx"):
        ap.error(f"不是 .docx 文件：{args.docx}（本工具仅支持 Word 文档）")

    if args.theme:
        _OPT["theme"] = args.theme
    if args.accent:
        if not _is_hex(args.accent):
            ap.error(f"--accent 需为十六进制颜色，如 #c0392b，收到：{args.accent}")
        _OPT["accent"] = args.accent if args.accent.startswith("#") else "#" + args.accent

    out = args.out or os.path.join(os.path.dirname(os.path.abspath(args.docx)), "bid-doc")
    os.makedirs(out, exist_ok=True)

    try:
        blocks = extract(args.docx, out)
        z = zipfile.ZipFile(args.docx)
        doc = ET.fromstring(z.read("word/document.xml"))
        body = doc.find(W + "body")
        has_table = body.find(W + "tbl") is not None
        has_product = any(
            classify_para(text_of(el).strip()) == "product"
            for el in body if el.tag.split('}')[-1] == "p"
        )
        if has_table:
            products = extract_table_products(args.docx, out)
            title, nsec, size = (build_blocks if args.layout == "block" else build_table)(products, out, args.title)
        elif has_product:
            products = extract_para_products(args.docx, out)
            if products:
                title, nsec, size = (build_blocks if args.layout == "block" else build_table)(products, out, args.title)
            else:
                title, nsec, size = build(blocks, out, args.title)
        else:
            title, nsec, size = build(blocks, out, args.title)
    except zipfile.BadZipFile:
        ap.error(f"无法读取（可能不是有效 docx 或已损坏）：{args.docx}")
    except Exception as e:  # noqa: BLE001
        ap.error(f"生成失败：{type(e).__name__}: {e}")

    if size > 20480:
        _warn(f"产物 {size}KB 超过 20MB，分享前建议改用相对路径图片版（images/ 文件夹）。")

    result = {"title": title, "sections": nsec, "layout": args.layout,
              "theme": _OPT["theme"] or "default", "size_kb": size,
              "output": os.path.join(out, "index.html")}
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"完成: 标题={title}  章节数={nsec}  布局={args.layout}  "
              f"主题={_OPT['theme'] or 'default'}  产物={result['output']}  大小={size}KB")


if __name__ == "__main__":
    main()
