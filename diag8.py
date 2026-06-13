# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check style at pos 11197
print("=== Style at pos 11197 ===")
print(repr(content[11190:11300]))

# Check what's around body close
body_close = content.find('</body>')
print(f"\n=== 200 chars before </body> ===")
print(repr(content[body_close-200:body_close+20]))

# Check style at pos 37821 (the new settings style)
print(f"\n=== Style at pos 37821 ===")
style_content = content[37821:37900]
print(repr(style_content))

# Count total divs
opens = content.count('<div')
closes = content.count('</div>')
print(f"\n=== TOTALS ===")
print(f"Opens: {opens}, Closes: {closes}, Diff: {opens-closes}")

# Script tags
import re
scripts = re.findall(r'<script[\s\S]*?</script>', content)
print(f"\n=== Script tags: {len(scripts)} ===")
for i, s in enumerate(scripts):
    short = s.strip()[:80]
    print(f"  {i}: {short}")
