# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The issue: style tag 0 at pos 11197 is the OLD duplicate settings style
# It's inside the script block area (after the first </script> at ~11003)
# Let's see what's between script 0 end and style 0 start

script0_end = content.find('</script>', 0)  # end of engine key toggle script
style0_start = content.find('<style>', script0_end)
style0_end = content.find('</style>', style0_start)

print(f"Script 0 ends at: {script0_end}")
print(f"Style 0 starts at: {style0_start}")
print(f"Style 0 ends at: {style0_end}")

# Show the content between script0 end and style0 end
between = content[script0_end:style0_end + 8]
print(f"\n=== Between script 0 end and style 0 end ({len(between)} chars) ===")
print(repr(between[:500]))
print("...")
print(repr(between[-200:]))

# The problem is clear: the old settings style block is between script blocks
# and it's displayed as text. We need to remove it.

# Also check: style 1 (new settings style at 37821) should stay
style1_end = content.find('</style>', 37821)
print(f"\n=== New settings style ends at: {style1_end} ===")
print(f"Content after: {repr(content[style1_end:style1_end+30])}")
