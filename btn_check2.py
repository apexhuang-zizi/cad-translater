# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find ALL btn-open-settings occurrences
import re
for m in re.finditer(r'btn-open-settings', content):
    ctx = content[max(0,m.start()-40):m.end()+80]
    is_html = '<button' in ctx or 'btn-open' in ctx and 'getElementById' not in ctx
    print(f"at {m.start()}: {'HTML' if is_html else 'JS'}")
    print(f"  {ctx[:100]}")
    print()
