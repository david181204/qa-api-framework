counts={}
with open("app.log","r",encoding="utf-8") as f:
    for line in f:
        parts = line.split()
        if len(parts)<3:
            continue
        level = parts[2].upper()      # 第3个字段是级别
        counts[level] = counts.get(level, 0) + 1

for level, count in counts.items():
    print(f"{level}: {count}")