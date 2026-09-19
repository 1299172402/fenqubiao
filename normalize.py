"""统一 MHTML 文件命名，并报告还缺哪些小类学科。

命名规范: 小类_{代码}_{中文名}_2025.mhtml
"""

import csv
import glob
import os
import re

DIR = r"d:\Documents\GitHub\fenqubiao\mhtml"
CSV = r"d:\Documents\GitHub\fenqubiao\小类学科目录_2025.csv"


def cn_name(subject: str) -> str:
    """从 'ACOUSTICS 声学' 中取出 '声学'。"""
    return subject.split()[-1]


# 读取目录，建立 code -> (序号, 学科, 中文名)
catalog = {}
with open(CSV, encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        code = row["代码"].strip()
        catalog[code] = (int(row["序号"]), row["学科"].strip(), cn_name(row["学科"]))

# 1) 统一重命名现有文件
renamed = 0
for path in glob.glob(os.path.join(DIR, "*.mhtml")):
    base = os.path.basename(path)
    m = re.match(r"^小类_([A-Z]{2})_", base)
    if not m:
        print(f"  [跳过] 无法识别代码: {base}")
        continue
    code = m.group(1)
    if code not in catalog:
        print(f"  [跳过] 代码不在目录中: {base}")
        continue

    target = os.path.join(DIR, f"小类_{code}_{catalog[code][2]}_2025.mhtml")
    if os.path.abspath(path) != os.path.abspath(target):
        if os.path.exists(target):
            os.remove(path)
        else:
            os.rename(path, target)
        renamed += 1

# 2) 统计缺失
have = set()
for path in glob.glob(os.path.join(DIR, "*.mhtml")):
    m = re.match(r"^小类_([A-Z]{2})_", os.path.basename(path))
    if m:
        have.add(m.group(1))

missing = [c for c in catalog if c not in have]
missing.sort(key=lambda c: catalog[c][0])

print(f"已重命名: {renamed}")
print(f"已有: {len(have)}  缺失: {len(missing)}  总计: {len(catalog)}")
print()
print("缺失清单 (序号,代码,中文名):")
for c in missing:
    n, _, cn = catalog[c]
    print(f"  {n:3d} {c} {cn}")

# 写出待办文件，供后续脚本读取
with open(r"d:\Documents\GitHub\fenqubiao\_missing.txt", "w", encoding="utf-8") as f:
    for c in missing:
        n, _, cn = catalog[c]
        f.write(f"{n}\t{c}\t{cn}\n")
