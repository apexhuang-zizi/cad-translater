# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and remove the old residual settings block
# It's between script tags: after </script> of app.js and before its closing
marker = '<!-- Settings gear button in header -->'
start = content.find(marker)
if start < 0:
    print("Marker not found")
else:
    # Find the end of the old style block
    style_start = content.find('<style>', start)
    style_end = content.find('</style>', style_start)
    if style_end >= 0:
        end = style_end + 8  # include </style>
        # Remove everything from marker to end of </style>
        # But preserve surrounding whitespace
        before = content[:start].rstrip('\n')
        after = content[end:].lstrip('\n')
        content = before + '\n' + after
        print(f"Removed old residual block from {start} to {end} ({end-start} chars)")
    else:
        print("Style end not found!")
else:
    print("No residual block found (might have been removed already)")

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
print("\n=== Verification ===")
import re
styles = list(re.finditer(r'<style[^>]*>', content))
print(f"Style tags: {len(styles)}")
for i, m in enumerate(styles):
    close = content.find('</style>', m.end())
    first_line = content[m.end():m.end()+60].replace('\n', ' ')
    print(f"  Style {i}: pos {m.start()}, len {close-m.end()}, starts: {first_line}")

body_idx = content.find('</body>')
last_script = content.rfind('<script')
print(f"Last </script> before body: {content.rfind('</script>', last_script)}")
print(f"</body> at: {body_idx}")
print(f"Content between last </script> and </body>: {body_idx - content.rfind('</script>', last_script) - 9} chars")

# Check div balance
print(f"\nDivs: opens={content.count('<div')}, closes={content.count('</div>')}")
