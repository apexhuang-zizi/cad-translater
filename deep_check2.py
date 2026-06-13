# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check what's at the overlay. usages
positions = [39420, 39590, 39630, 39715]
for pos in positions:
    print(f"\nAt {pos}:")
    print(repr(content[pos:pos+40]))

# Also check: is the settings JS closure (IIFE) containing these overlay. usages
# or are they elsewhere?
# Find where the IIFE starts and ends
iife_start = content.find('(function() {\n    var getOverlay')
iife_end = 15668

# The overlay. at 39424 is way after the IIFE end
# That means the overlay. references are NOT in the settings IIFE closure
# Let me find which closure contains them

# Search for the actual closure context around 39424
ctx = content[max(0,39424-200):39424+20]
print(f"\nContext around first overlay. (39424):")
print(repr(ctx))

# Is there another (function() { around that area?
idx = 39424 - 500
fn = content.rfind('(function() {', max(0, idx), 39424)
if fn >= 0:
    print(f"\nFound (function(){{ at {fn}")
    print(f"Content: {repr(content[fn:fn+60])}")
