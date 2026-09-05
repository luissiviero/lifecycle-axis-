import re, sys, os
R="/home/user/lifecycle-axis-"
def fm_keys(p):
    L=open(p,encoding="utf-8").read().splitlines()
    assert L[0]=="---", p+": no front matter"
    keys=[];vals={}
    for l in L[1:]:
        if l=="---": break
        if ":" in l:
            k,v=l.split(":",1); keys.append(k.strip()); vals[k.strip()]=v.strip()
    return keys,vals,L
def headings(L): return [l for l in L if l.startswith("## ") or l.startswith("### ")]
bad=0
def err(m):
    global bad; bad+=1; print("FAIL",m)
d=sys.argv[1]
for name in ("intent.md","spec.md","plan.md"):
    p=os.path.join(d,name)
    if not os.path.exists(p): print("skip",name); continue
    tk,tv,tL=fm_keys(os.path.join(R,"docs/sdlc/templates",name))
    k,v,L=fm_keys(p)
    if k!=tk: err(f"{name}: front-matter keys differ\n  template={tk}\n  got     ={k}")
    for kk,vv in v.items():
        if " #" in vv or vv.startswith("#"): err(f"{name}: inline comment on {kk}: {vv!r}")
    if v.get("status")!="in-review": err(f"{name}: status={v.get('status')!r}")
    if v.get("approved-by") or v.get("approved-on"): err(f"{name}: approved-by/on set")
    if v.get("id")!=os.path.basename(d): err(f"{name}: id={v.get('id')!r}")
    th=headings(tL); h=headings(L)
    if h!=th: err(f"{name}: headings differ\n  template={th}\n  got     ={h}")
    if name=="plan.md":
        on=False
        for l in L:
            if l.startswith("## "): on=l.startswith("## Files that change")
            elif on and l.lstrip().startswith("-") and ("*" in l.split("—")[0].split(" - ")[0]): err(f"plan: glob in file list: {l.strip()}")
    print(f"ok {name}: {len(L)} lines")
sys.exit(1 if bad else 0)
