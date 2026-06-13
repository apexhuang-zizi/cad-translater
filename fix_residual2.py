# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

marker = '<!-- Settings gear button in header -->'
start = content.find(marker)
if start < 0:
    print("Marker not found - already removed")
else:
    style_start = content.find('<style>', start)
    style_end = content.find('</style>', style_start)
    if style_end >= 0:
        end = style_end + 8
        before = content[:start].rstrip('\n')
        after = content[end:].lstrip('\n')
        content = before + '\n' + after
        print(f"Removed old residual block from {start} to {end} ({end-start} chars)")
    else:
        print("Style end not found!")

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
import re
styles = list(re.finditer(r'<style[^>]*>', content))
print(f"\nStyle tags: {len(styles)}")
for i, m in enumerate(styles):
    close = content.find('</style>', m.end())
    first_line = content[m.end():m.end()+60].replace('\n', ' ')
    print(f"  Style {i}: pos {m.start()}, len {close-m.end()}, starts: {first_line}")

body_idx = content.find('</body>')
last_script_close = content.rfind('</script>')
print(f"Last </script> at: {last_script_close}")
print(f"</body> at: {body_idx}")
print(f"Gap: {body_idx - last_script_close - 9} chars between </script> and </body>")
print(f"Divs: opens={content.count('<div')}, closes={content.count('</div>')}")
