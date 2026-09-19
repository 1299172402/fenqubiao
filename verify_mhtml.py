"""校验 MHTML：解码后统计期刊行数、分区数，并打印首尾刊名。"""

import email
import glob
import os
import re

DIR = r"d:\Documents\GitHub\fenqubiao\mhtml"

for path in sorted(glob.glob(os.path.join(DIR, "*.mhtml"))):
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f)

    html = ""
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            payload = part.get_payload(decode=True)
            if payload:
                html = payload.decode("utf-8", "replace")
                break

    # 抓取表格中的每一行数据
    titles = re.findall(r'href="[^"]*?/Journal/Detail/[^"]+"[^>]*>([^<]+)</a>', html)
    classes = re.findall(r'<span class="class" id="c\d+" data-attr="([^"]*)"', html)

    name = os.path.basename(path)
    print(f"{name}")
    print(f"  html_len={len(html)}  期刊数={len(titles)}  分区数={len(classes)}")
    if titles:
        print(f"  首={titles[0]}  尾={titles[-1]}")
    print()
