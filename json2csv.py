"""把浏览器抓下来的原始 JSON 转成 CSV。

用法: python json2csv.py <源文件> <目标csv> <表头1,表头2,...>
"""

import csv
import json
import sys

src, dst, header = sys.argv[1], sys.argv[2], sys.argv[3].split(",")

with open(src, encoding="utf-8") as f:
    raw = f.read()

# 文件带 "Result: " 前缀和尾部工具输出，从第一个 '[' 起用 raw_decode 取 JSON 值
rows, _ = json.JSONDecoder().raw_decode(raw[raw.index("[") :])

with open(dst, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(rows)

print(f"wrote {len(rows)} rows -> {dst}")
