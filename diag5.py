# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('<!-- Translator v2 Settings Panel -->')
end_marker = '<!-- Settings gear button -->'
end_pos = content.find(end_marker)

settings_block = content[start:end_pos]
print(f"Block length: {len(settings_block)}")
print(f"Block starts: {settings_block[:100]}")
print(f"Block ends: {settings_block[-100:]}")

# Count <div carefully - exclude </div> from count
import re
all_divs = re.findall(r'<div[^>]*>', settings_block)
closes = settings_block.count('</div>')
opens = len(all_divs)
print(f"Opens: {opens}, Closes: {closes}")

# Check if the issue is that the settings block extends further than I think
# Let's find the actual CSS block boundary
style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', settings_block, re.DOTALL)
print(f"\nStyle blocks in settings: {len(style_blocks)}")
for i, s in enumerate(style_blocks):
    print(f"  Style {i}: {len(s)} chars")

# Now check the entire content for remaining div balance
all_opens = content.count('<div')
all_closes = content.count('</div>')
print(f"\n=== ENTIRE FILE ===")
print(f"Total opens: {all_opens}, closes: {all_closes}, diff: {all_opens - all_closes}")
