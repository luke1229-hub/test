#!/usr/bin/env python3
"""
前台图片本地化与可访问性核验。

用法:
    python verify_front.py <文章完整URL> [--site <站点根URL>] [--external <外站域名关键词>]

示例:
    python verify_front.py "http://testdecor/?p=34" \
        --site http://testdecor --external cdn.sanity.io

输出: 前台状态码、本站图片引用列表及其 HTTP 状态、外站图片残留数。
退出码: 0 = 全部通过; 1 = 存在失败项。
"""
import argparse
import re
import sys
import urllib.request
import urllib.error

NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def fetch(url):
    try:
        with NO_PROXY_OPENER.open(url, timeout=15) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, "ERROR: %s" % e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="页面完整 URL")
    ap.add_argument("--site", default="", help="站点根 URL，用于判定图片是否为本站")
    ap.add_argument("--external", default="cdn.sanity.io", help="外站图片域名关键词")
    args = ap.parse_args()

    status, html = fetch(args.url)
    print("=== 前台页面 ===")
    print("%s -> HTTP %s | %d bytes" % (args.url, status, len(html)))
    ok = status == 200 and bool(html) and not html.startswith("ERROR:")

    srcs = re.findall(r'src="([^"]+)"', html)
    imgs = [s for s in srcs if re.search(r"\.(png|jpe?g|webp|gif|svg)(\?|$)", s, re.I)]

    print("\n=== 页面内图片引用 ===")
    site = args.site.rstrip("/")
    local, foreign = [], []
    for s in imgs:
        (local if (not site or s.startswith(site) or "/wp-content/uploads/" in s) else foreign).append(s)
        print("  %s %s" % ("[本站]" if s not in foreign else "[外站]", s))

    print("\n=== 本站图片可访问性 ===")
    for s in dict.fromkeys(local):
        st, _ = fetch(s)
        print("  HTTP %s  %s" % (st, s))
        if st != 200:
            ok = False

    print("\n=== 外站图片残留 ===")
    ext_hits = html.count(args.external)
    print("  '%s' 出现次数 = %d ; 外站图片引用 = %d" % (args.external, ext_hits, len(foreign)))
    if ext_hits or foreign:
        ok = False

    print("\n=== 结论 ===")
    print("  %s" % ("PASS - 前台 200、图片全部本地且可访问、无外站残留" if ok else "FAIL - 存在未通过项，见上"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
