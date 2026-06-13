# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all <script> tags
import re
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
print(f"Found {len(scripts)} script tags")
for i, s in enumerate(scripts):
    print(f"\n--- Script {i} ({len(s)} chars) ---")
    print(s[:200])

# Check for content after </script>
last_script_end = content.rfind('</script>')
after_script = content[last_script_end + len('</script>'):]
print(f"\n=== Content after last </script> ({len(after_script)} chars) ===")
print(repr(after_script))

# Check the settings-overlay block structure - count opening/closing divs
idx = content.find('settings-overlay"')
if idx >= 0:
    block = content[idx:idx+3000]
    # Count divs
    opens = block.count('<div ')
    closes = block.count('</div>')
    print(f"\n=== Settings block: {opens} <div> opens, {closes} </div> closes ===")
