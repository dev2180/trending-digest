"""Compact summary of out/ for the Docker Agent tester (keeps its token use small)."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("out/digest.json", encoding="utf-8"))
h = open("out/digest.html", encoding="utf-8").read()
pos = [h.find(f'href="{r["url"]}"') for r in d]
print(f"{len(d)} repos | html has all: {min(pos) >= 0} | html in order: {pos == sorted(pos)}")
for i, r in enumerate(d, 1):
    print(f"{i}. {r['name']} | {r['url']} | stars={r['stars']} | {r.get('category', '')} | {r['eli5']}")
