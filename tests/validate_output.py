# -*- coding: utf-8 -*-
"""
校验已生成的 index.html 是否满足交付基线（人工复检 / CI 用）。

用法:
  python tests/validate_output.py <index.html> [--json]

退出码: 0 = 通过, 1 = 不通过
"""
import sys, os, re, argparse, json


def validate(path):
    if not os.path.exists(path):
        return {"ok": False, "checks": {}, "error": f"文件不存在：{path}"}
    html = open(path, encoding="utf-8").read()
    checks = {
        "无残留占位符 {{...}}": "{{" not in html,
        "含章节区块 class=block": 'class="block' in html,
        "含产品配置清单": "产品配置清单" in html or "<ul>" in html,
        "含封面标题区": "<h1>" in html,
        # 回归守卫：字号/粗细/颜色调整依赖选区缓存，缺失则点击工具栏无效
        "字号调整选区缓存已内置": "savedRange" in html and "captureSelection" in html,
    }
    # 图片：要么 base64 内嵌，要么引用了 images/ 目录（需同目录图片配合）
    has_embed = "data:image" in html
    has_rel = 'src="images/' in html
    checks["图片已内嵌或引用目录"] = has_embed or has_rel
    if has_rel and not has_embed:
        checks["提示:相对路径图片需 images/ 同目录"] = True  # 信息项，不判失败
    ok = all(v for k, v in checks.items() if not k.startswith("提示"))
    return {"ok": ok, "checks": checks, "size_kb": round(len(html) / 1024, 1)}


def main():
    ap = argparse.ArgumentParser(description="校验 bid-doc-html 生成的 index.html")
    ap.add_argument("html", help="index.html 路径")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()
    res = validate(args.html)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"=== 校验 {args.html} ===")
        for k, v in res["checks"].items():
            print(("  [PASS] " if v else "  [FAIL] ") + k)
        if "size_kb" in res:
            print(f"  大小={res['size_kb']}KB")
        print("结果: " + ("PASS ✅" if res["ok"] else "FAIL ❌"))
    sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
