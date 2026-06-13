# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The stale closure at 11172 merges with the DXF closure due to paren counting
# Let's see the actual content of the big script tag
big_script_end = content.find('</script>', 11142)
big_script_content = content[11142:big_script_end]

# Count top-level (function() blocks
import re
fn_blocks = list(re.finditer(r'\(function\s*\(\s*\)\s*\{', big_script_content))
print(f"Top-level IIFEs in big script: {len(fn_blocks)}")
for m in fn_blocks:
    pos = m.start()
    # Find the end
    depth = 1
    i = pos
    while i < len(big_script_content) and depth > 0:
        if big_script_content[i] == '(':
            depth += 1
        elif big_script_content[i] == ')':
            depth -= 1
        i += 1
    block = big_script_content[pos:i]
    first_line = block.strip()[:80].replace('\n', ' ')
    print(f"\nIIFE at {pos} (length {i-pos}):")
    print(f"  {first_line}")
    if 'settings-overlay' in block:
        print(f"  -> SETTINGS PANEL")
    elif 'dxf' in block.lower():
        print(f"  -> DXF FLOW")

# Also find the standalone settings IIFE
standalone_settings = content.find('(function() {\n    var overlay = document.getElementById', 30000)
if standalone_settings >= 0:
    depth = 1
    i = standalone_settings
    while i < len(content) and depth > 0:
        if content[i] == '(': depth += 1
        elif content[i] == ')': depth -= 1
        i += 1
    print(f"\nStandalone settings IIFE at {standalone_settings} (ends at {i})")
    print(f"Length: {i - standalone_settings}")
