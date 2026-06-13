# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The IIFE at 29163 - let me trace parens more carefully
start = 29163
# Count only top-level parens
depth = 0
in_string = False
str_char = None
escape_next = False
i = start

while i < len(content):
    ch = content[i]
    
    if escape_next:
        escape_next = False
        i += 1
        continue
    if ch == '\\':
        escape_next = True
        i += 1
        continue
    
    if not in_string:
        if ch in ('"', "'", '`'):
            in_string = True
            str_char = ch
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                print(f"IIFE ends at {i}")
                print(f"Content around end: {repr(content[i-20:i+10])}")
                break
    else:
        if ch == str_char:
            in_string = False
    i += 1

# Now get the IIFE block
end = i
block = content[start:end+1]
print(f"\nIIFE length: {len(block)}")
print(f"Lines: {block.count(chr(10))}")

# Check: does it contain loadTMStats?
if 'loadTMStats' in block:
    print("Contains loadTMStats")
    idx = block.rfind('loadTMStats')
    print(f"Last loadTMStats: {repr(block[idx:idx+50])}")
