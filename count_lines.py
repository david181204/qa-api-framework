with open("demo.txt","r",encoding="utf-8") as f:
    lines=f.readlines()

non_empty=0
for line in lines:
    if line.strip():
        non_empty+=1

print(f"总行数={len(lines)}，非空行数={non_empty}")