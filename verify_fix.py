# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()
import re
scripts = re.findall(r'<script[\s\S]*?</script>', content)
for i, s in enumerate(scripts):
    go = s.count('getOverlay')
    ov = s.count('overlay.')
    if go > 0 or ov > 0:
        print(f'Script {i}: getOverlay={go}, overlay.={ov}')
