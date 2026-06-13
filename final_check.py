# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check what's at 11226
ctx = content[11220:11280]
print(f"At 11226: {repr(ctx)}")

# Check if there's still a stale IIFE
# Find all (function() that contain settings-overlay
import re
for m in re.finditer(r'\(function\(\)', content):
    block = content[m.start():m.start()+200]
    if 'settings-overlay' in block:
        print(f"\nIIFE at {m.start()}:")
        print(f"  {block[:100]}")

# Find the stale one specifically
stale = content.find('var getOverlay')
if stale >= 0:
    print(f"\ngetOverlay still at {stale}")
    print(f"  {content[stale:stale+80]}")
else:
    print("\ngetOverlay removed OK")

# Check for var overlay = document.getElementById
overlay_vars = list(re.finditer(r'var overlay = document\.getElementById', content))
print(f"\nvar overlay declarations: {len(overlay_vars)}")
for m in overlay_vars:
    print(f"  at {m.start()}: {content[m.start():m.start()+60]}")
