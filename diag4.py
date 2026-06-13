# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the settings overlay block precisely
start = content.find('<!-- Translator v2 Settings Panel -->')
# Find the settings gear button comment
end_comment = content.find('<!-- Settings gear button -->', start)
end_block = content.find('</div>', end_comment - 100)

block = content[start:end_block + 6]

# Count divs more carefully
opens = block.count('<div')
closes = block.count('</div>')
print(f"Total: {opens} opens, {closes} closes, diff={opens-closes}")

# Let's trace the nesting manually
lines = block.split('\n')
depth = 0
for i, line in enumerate(lines):
    opens_in_line = line.count('<div')
    closes_in_line = line.count('</div>')
    depth += opens_in_line - closes_in_line
    if i % 10 == 0 or depth != 0:
        marker = " <-- DEPTH ISSUE" if depth != 0 and closes_in_line > 0 else ""
        if opens_in_line > 0 or closes_in_line > 0 or i % 50 == 0:
            print(f"L{i+1} (d={depth}): {line.strip()[:100]}{marker}")

print(f"\nFinal depth: {depth}")
print(f"\nBlock ends with: {repr(block[-80:])}")
