# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check the potential conflict: script 0's engine-btn listener
# Let me check what it does when clicking engine-btn inside settings modal
script0_start = content.find('<script>\n// Engine key visibility toggle')
script0_end = content.find('</script>', script0_start)
script0 = content[script0_start:script0_end]

# Find the click listener on .engine-btn
if 'engine-btn' in script0:
    # Show the complete click handler
    idx = script0.find(".engine-btn")
    if idx >= 0:
        event_block = script0[idx:idx+800]
        print("Script 0 engine-btn code:")
        print(event_block)
        
        if "settings-overlay" in event_block or "settings" in event_block.lower():
            print("\n⚠️  Script 0 catches clicks INSIDE settings panel too!")
        else:
            print("\n✅ No apparent conflict - but event delegation might catch settings panel clicks")
