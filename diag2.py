# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check the end of the file
tail = content[-2000:]
# Encode to utf-8 then decode with errors replaced
print("=== LAST 2000 CHARS (repr) ===")
print(repr(tail))

# Also check if overlay variable is in a closure
idx = content.find("(function() {")
if idx >= 0:
    print("\n=== FOUND CLOSURE ===")
    print(content[idx:idx+50])
