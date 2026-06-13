# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the stale IIFE at 11172
# Find it: (function() {
#     var getOverlay = function() { return document.getElementById('settings-overlay'); };
# It ends where? We need to find the matching );

# Actually, the stale IIFE and the DXF closure are both inside the same big script tag.
# The stale IIFE throws an error, but the DXF closure should still run.
# However, removing the stale IIFE is the cleanest fix.

# Find the stale IIFE start
stale_start = content.find('// Settings panel management', 11000)
if stale_start < 0:
    print("Could not find stale IIFE start")
    sys.exit(1)

# Find the IIFE end
# The IIFE is: (function() { ... });
# After the IIFE, there's whitespace and then the DXF comment
# The DXF comment is: // DXF Import Flow
dxf_marker = '// DXF Import Flow'
dxf_start = content.find(dxf_marker, stale_start)

if dxf_start < 0:
    print("Could not find DXF marker")
    sys.exit(1)

print(f"Stale IIFE comment at: {stale_start}")
print(f"DXF marker at: {dxf_start}")

# Remove from stale_start to dxf_start
content = content[:stale_start] + content[dxf_start:]

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed stale IIFE")

# Verify
import re
scripts = re.findall(r'<script[\s\S]*?</script>', content)
print(f"Script tags: {len(scripts)}")
for i, s in enumerate(scripts):
    short = s.strip()[:60].replace('\n', ' ')
    has_settings = 'settings-overlay' in s
    has_overlay = 'overlay' in s
    print(f"  {i}: settings={has_settings} overlay={has_overlay} | {short}")

# Check for duplicate IIFEs
iifes = list(re.finditer(r'\(function\s*\(\s*\)\s*\{[\s\S]*?settings-overlay', content))
print(f"\nIIFEs with settings-overlay: {len(iifes)}")
for m in iifes:
    print(f"  at {m.start()}")

# Verify structure
body_close = content.find('</body>')
print(f"</body> at {body_close}")
divs_opens = content.count('<div')
divs_closes = content.count('</div>')
print(f"Divs: open={divs_opens}, close={divs_closes}, diff={divs_opens-divs_closes}")
