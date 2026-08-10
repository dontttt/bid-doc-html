# -*- coding: utf-8 -*-
"""
bid-doc-html 全套自检：一条命令跑完所有验证。

用法:
  python tests/run_all.py

退出码: 0 = 全部通过, 1 = 有失败
"""
import sys, os, subprocess, re, tempfile, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = ROOT
PY = sys.executable


def step(name, fn):
    print("\n=== " + name + " ===")
    try:
        ok = fn()
    except Exception as e:
        print("  [ERR] 异常: " + str(e))
        return False
    print("  " + ("PASS ✅" if ok else "FAIL ❌"))
    return ok


def t_self_test():
    r = subprocess.run([PY, os.path.join(SKILL, "scripts", "make_doc.py"), "--self-test"],
                       cwd=SKILL, capture_output=True, text=True)
    print(r.stdout.strip())
    return r.returncode == 0


def t_generate_and_validate():
    # 用 make_doc 内部的样例构造器生成临时 docx，再走完整 CLI 生成
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "make_doc", os.path.join(SKILL, "scripts", "make_doc.py"))
    md = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(md)
    tmp = tempfile.mkdtemp()
    docx = os.path.join(tmp, "sample.docx")
    md._build_sample_docx(docx)
    out = os.path.join(tmp, "out")
    r = subprocess.run(
        [PY, md.__file__, docx, out, "--title", "自检样例", "--json"],
        cwd=SKILL, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout.strip()); print(r.stderr.strip()); return False
    info = json.loads(r.stdout.strip())
    print("  生成: 章节=%d 大小=%.1fKB" % (info["sections"], info["size_kb"]))
    v = subprocess.run([PY, os.path.join(SKILL, "tests", "validate_output.py"),
                        os.path.join(out, "index.html")],
                       cwd=SKILL, capture_output=True, text=True)
    print(v.stdout.strip())
    gen = open(os.path.join(out, "index.html"), encoding="utf-8").read()
    needed = ["wireTemplateEditing", "addSectionAtEnd", "buildThemeFab", "function wireMedia"]
    miss = [s for s in needed if s not in gen]
    if miss:
        print("  生成产物缺失能力: " + ", ".join(miss))
        return False
    print("  生成产物含增删章节/图片/主题悬浮条: OK")
    return v.returncode == 0


def t_editor_contract():
    html = open(os.path.join(SKILL, "assets", "editor.html"), encoding="utf-8").read()
    required = ["function importDoc", "function parseExportedHtml",
                "function exportDoc", "function addSection",
                "function fileToBase64", "captureSelection", "savedRange",
                "function buildThemeFab"]
    missing = [s for s in required if s not in html]
    if missing:
        print("  缺失: " + ", ".join(missing))
        return False
    # 用 node 解析默认 doc 字面量（Python 无法 eval 带裸 key 的 JS 对象）
    m = re.search(r"var doc = (\{[\s\S]*?\n\});", html)
    if not m:
        print("  未找到默认 doc 字面量"); return False
    node_js = os.path.join(tempfile.mkdtemp(), "check_doc.js")
    with open(node_js, "w", encoding="utf-8") as f:
        f.write(
            "const fs=require('fs');"
            "const html=fs.readFileSync(process.argv[2],'utf8');"
            "var m=html.match(/var doc = (\\{[\\s\\S]*?\\n\\});/);"
            "var d=eval('('+m[1]+')');"
            "console.log(JSON.stringify({sections:d.sections.length,"
            "items:(d.intro&&d.intro.items?d.intro.items.length:0),"
            "title:d.meta.title}));"
        )
    nr = subprocess.run(["node", node_js,
                         os.path.join(SKILL, "assets", "editor.html")],
                        capture_output=True, text=True)
    if nr.returncode != 0:
        print("  node 解析失败: " + nr.stderr.strip()); return False
    d = json.loads(nr.stdout.strip())
    print("  默认 doc: 章节=%d 清单项=%d 标题=%s" %
          (d["sections"], d["items"], d["title"]))
    return d["sections"] >= 1 and d["items"] >= 1


def main():
    results = [
        step("1) make_doc.py 自测", t_self_test),
        step("2) 生成 + 校验产物", t_generate_and_validate),
        step("3) editor.html 契约检查", t_editor_contract),
    ]
    print("\n========================================")
    print("结果: " + ("全部通过 ✅" if all(results) else "存在失败 ❌"))
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
