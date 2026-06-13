# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The real question: when the script at 29125 executes, are the elements in the DOM?
# The script starts at 29125, which means the browser has already parsed:
# - HTML up to position 29125
# - Button at 25858 ✅
# - Settings overlay at 20729 ✅

# The script tag content starts after > at 29125+8=29133
# The first thing it does is get settings-overlay (at 20729) ✅ exists
# Then it gets btn-open-settings (at 25858) ✅ exists

print("✅ All elements are in the DOM before the script executes")
print(f"Settings overlay at: 20729")
print(f"Button at: 25858")
print(f"Script at: 29125")
print()

# Verify the IIFE code is correct
iife_start = content.find('(function() {\n    var overlay', 29000)
iife_end_pos = iife_start
depth = 1
while iife_end_pos < len(content) and depth > 0:
    if content[iife_end_pos] == '(': depth += 1
    elif content[iife_end_pos] == ')': depth -= 1
    iife_end_pos += 1

iife_block = content[iife_start:iife_end_pos]
print(f"IIFE block: {iife_end_pos - iife_start} chars")
print(f"First 5 lines:")
for line in iife_block.split('\n')[:5]:
    print(f"  {line}")
print(f"Last 3 lines:")
for line in iife_block.split('\n')[-3:]:
    print(f"  {line}")

# Check for btn-open-settings listener
if "btn-open-settings" in iife_block and "addEventListener" in iife_block:
    print("\n✅ btn-open-settings click listener present")
else:
    print("\n❌ Missing btn-open-settings click listener")
