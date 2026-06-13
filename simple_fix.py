# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Simplest fix: the settings JS closure is a IIFE that runs immediately.
# Since it's inside the big script tag which ends at ~30679, but HTML elements 
# are at ~30737+, the DOM elements don't exist yet.
# 
# Instead of restructuring the whole file, let's just change the overlay var 
# from immediate evaluation to lazy lookup (use a function to get the element).
#
# Find: var overlay = document.getElementById('settings-overlay');
# Replace with: var getOverlay = function() { return document.getElementById('settings-overlay'); };

old = "var overlay = document.getElementById('settings-overlay');"
new = "var getOverlay = function() { return document.getElementById('settings-overlay'); };"

if old not in content:
    print("ERROR: Could not find the overlay line!")
    sys.exit(1)

print(f"Found at position: {content.find(old)}")
content = content.replace(old, new, 1)  # Replace only first occurrence

# Now replace all `overlay.` with `getOverlay().` in the settings closure
# But be careful - the DXF closure also has closures with different variables
# Let's do targeted replacements

# The settings closure runs from (function() { var getOverlay...) to ...();
# After the overlay var line, all uses of 'overlay.' in the settings block
# need to become 'getOverlay().'

# Find the full settings closure
closure_start = content.find('var getOverlay')
# Find the end of this closure (next standalone IIFE or DXF comment)
dxf_marker = '// DXF Import Flow'
closure_end = content.find(dxf_marker)
if closure_end < 0:
    closure_end = content.find('})();', closure_start + 500)
    if closure_end >= 0:
        # Find the end of the IIFE
        closure_end = content.find('})();', closure_end)

print(f"Closure range: {closure_start} to {closure_end}")

settings_block = content[closure_start:closure_end]
overlay_uses = len(settings_block.split('overlay.')) - 1
print(f"'overlay.' uses in settings closure: {overlay_uses}")

# Replace all overlay. with getOverlay(). in the settings block
settings_block = settings_block.replace('overlay.', 'getOverlay().')
new_closure_block = settings_block

# Rebuild content
content = content[:closure_start] + new_closure_block + content[closure_end:]

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n=== Verification ===")
# Check that getOverlay is used consistently in settings closure
import re
scripts = re.findall(r'<script[\s\S]*?</script>', content)
for i, s in enumerate(scripts):
    if 'getOverlay' in s:
        print(f"Script {i} has getOverlay")
        print(f"  getOverlay uses: {s.count('getOverlay')}")
        print(f"  overlay. uses: {s.count('overlay.')}")
