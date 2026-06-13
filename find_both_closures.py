# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# There are TWO settings closures:
# 1. Stale one at ~11190 — runs too early, overlay=null (BROKEN)
# 2. Correct one at ~39218 — after HTML, overlay exists (GOOD)
#
# We need to remove #1 and keep #2

# Find the first (stale) settings closure
stale_start = content.find('var overlay = document.getElementById')
stale_end = 15668  # IIFE end

# But wait - the stale closure's var overlay was already changed to getOverlay
# by the previous fix. Let me check what exactly is there.

# Find both closures
import re
closures = [(m.start(), content[m.start():m.start()+70].replace('\n',' ')) for m in re.finditer(r'var overlay = document.getElementById\(.+settings', content)]
print(f"Closures with 'var overlay':")
for pos, snippet in closures:
    print(f"  at {pos}: {snippet}")

# Also check getOverlay
get_overlays = [(m.start(), content[m.start():m.start()+70].replace('\n',' ')) for m in re.finditer(r'var getOverlay = function', content)]
print(f"\ngetOverlays:")
for pos, snippet in get_overlays:
    print(f"  at {pos}: {snippet}")

# Check for (function() that contain overlay
fn_starts = [(m.start(),) for m in re.finditer(r'\(function\(\)', content)]
for pos, in fn_starts:
    block = content[pos:pos+200]
    if 'settings-overlay' in block:
        print(f"\nSettings IIFE at {pos}")
        # Find IIFE end
        paren = 1
        i = pos
        while i < len(content) and paren > 0:
            if content[i] == '(':
                paren += 1
            elif content[i] == ')':
                paren -= 1
            i += 1
        iife_end = i
        block = content[pos:i]
        print(f"  Ends at {i} (length {i-pos})")
        print(f"  Has 'overlay.': {block.count('overlay.')}")
        print(f"  Has 'getOverlay.': {block.count('getOverlay().')}")
