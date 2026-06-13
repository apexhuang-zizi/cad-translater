# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if getOverlay exists
if 'getOverlay' in content:
    print("getOverlay found!")
    idx = content.find('getOverlay')
    print(f"At {idx}: {repr(content[idx:idx+80])}")
else:
    print("getOverlay NOT found - fix didn't apply")

# Check overlay. uses
import re
all_overlays = [(m.start(), content[m.start():m.start()+20]) for m in re.finditer(r'overlay\.', content)]
print(f"\nAll 'overlay.' uses ({len(all_overlays)}):")
for pos, snippet in all_overlays:
    print(f"  at {pos}: {snippet}")

# Find the closure boundaries more carefully
closure_start = content.find('var getOverlay')
if closure_start < 0:
    closure_start = content.find('var overlay = document.getElementById')

# Find the END of this closure by counting parentheses
if closure_start >= 0:
    print(f"\nClosure starts at {closure_start}")
    # Find the IIFE end: ); at the top level of this IIFE
    # The IIFE is: (function() { ... });
    # Count braces to find the end
    brace_depth = 0
    paren_depth = 0
    in_str = False
    str_char = None
    i = closure_start
    
    # Find the opening (
    paren_open = content.find('(function()', closure_start)
    if paren_open >= 0:
        i = paren_open
        paren_depth = 1
        brace_depth = 0
        
        while i < len(content) and paren_depth > 0:
            ch = content[i]
            if ch in ('"', "'", '`') and (i == 0 or content[i-1] != '\\'):
                if not in_str:
                    in_str = True
                    str_char = ch
                elif ch == str_char:
                    in_str = False
            elif not in_str:
                if ch == '(':
                    paren_depth += 1
                elif ch == ')':
                    paren_depth -= 1
                    if paren_depth == 0:
                        print(f"IIFE ends at {i}")
                        print(f"End: {repr(content[i-5:i+10])}")
                        break
            i += 1
else:
    print("Closure start not found")
