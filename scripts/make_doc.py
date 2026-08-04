# -*- coding: utf-8 -*-
"""
bid-doc-html 生成器（技能自带，可独立运行）
用法:
  python make_doc.py <参数表.docx> [输出目录] [--title "自定义标题"]
输出: <输出目录>/index.html （单文件，图片 base64 内嵌）+ <输出目录>/images/
"""
import sys, os, re, json, base64, zipfile, shutil
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

MIME = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp"}

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "template.html")


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
        with open(os.path.join(img_dir, new), "wb") as f:
            f.write(z.read("word/media/" + os.path.basename(orig)))
        return new

    doc = ET.fromstring(z.read("word/document.xml"))
    body = doc.find(W + "body")

    def text_of(p):
        return "".join(t.text or "" for t in p.iter(W + "t"))

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
            # 首段作为标题（仅当未指定）
            if len(text) > 4:
                title = text
                continue
        if text.startswith("包含") or (not sections and not current and text and "：" in text[:30]):
            intro = text
            continue
        m = re.match(r'^(\d+)\.(.*)$', text)
        if m and text not in ("图",):
            after = m.group(2)
            is_sub = bool(after) and after[0].isdigit()
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

    if cover_images and sections and sections[0]["title"].startswith("1.") \
            and cover_images[0] not in sections[0]["images"]:
        sections[0]["images"].insert(0, cover_images[0])
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
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    return title, len(sections), round(len(html) / 1024, 1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    docx = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(docx)), "bid-doc")
    title = None
    if "--title" in sys.argv:
        title = sys.argv[sys.argv.index("--title") + 1]
    os.makedirs(out, exist_ok=True)
    blocks = extract(docx, out)
    title, nsec, size = build(blocks, out, title)
    print(f"完成: 标题={title}  章节数={nsec}  产物={os.path.join(out,'index.html')}  大小={size}KB")


if __name__ == "__main__":
    main()
