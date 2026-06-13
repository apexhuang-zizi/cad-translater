# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Strategy: 
# 1. Remove BOTH settings style blocks entirely
# 2. Remove the old duplicate gear button
# 3. Place everything cleanly right before </body>

# Find the settings panel HTML block
start_marker = '<!-- Translator v2 Settings Panel -->'
start = content.find(start_marker)

# Find the old duplicate gear button (the second btn-open-settings)
# The new one is at position `start + gear_offset`, the old one comes after
gear_positions = []
idx = 0
while True:
    pos = content.find('btn-open-settings', idx)
    if pos == -1:
        break
    gear_positions.append(pos)
    idx = pos + 1

print(f"Gear button positions: {gear_positions}")

# The new button is right after the settings HTML (within 100 chars of start)
new_btn = gear_positions[0] if len(gear_positions) >= 1 else -1
# Old button is the second one (after the new style block)
old_btn = gear_positions[1] if len(gear_positions) >= 2 else -1

# Find the old style block that follows the old button
old_style_start = content.find('<style>', old_btn) if old_btn >= 0 else -1
old_style_end = content.find('</style>', old_style_start) if old_style_start >= 0 else -1

print(f"New button at: {new_btn}")
print(f"Old button at: {old_btn}")
print(f"Old style start: {old_style_start}, end: {old_style_end}")

# Also find the new style block (comes right after new button)
new_style_start = content.find('<style>', new_btn) if new_btn >= 0 else -1
new_style_end = content.find('</style>', new_style_start) if new_style_start >= 0 else -1

print(f"New style start: {new_style_start}, end: {new_style_end}")

# The full block to remove: from settings panel start to end of old style block
# But we need to keep the new style block and move it to before </body>

# Actually, let's remove EVERYTHING from start_marker to end of new style block
# Then re-insert it all right before </body>

# Find end of new style block
# The new style block ends at new_style_end
# But there might be the old button + old style between new style and </body>
# Let's find the actual end of ALL settings-related content

# The content after new_style_end until </body>
after_new_style = content[new_style_end + 8:]  # +8 for </style>
# Find </body>
body_close = content.find('</body>')
print(f"</body> at {body_close}")

# Everything from start_marker to body_close is the settings block + potential garbage
# Remove it all
content_clean = content[:start] + content[new_style_end + 8:body_close]

# Now re-insert the settings block right before </body>
settings_block = content[start:new_style_end + 8]
content_final = content_clean + '\n' + settings_block + content[body_close:]

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content_final)

# Verify
print("\n=== Verification ===")
import re
styles = list(re.finditer(r'<style[^>]*>', content_final))
print(f"Style tags: {len(styles)}")
for i, m in enumerate(styles):
    close = content_final.find('</style>', m.end())
    print(f"  Style {i}: pos {m.start()}, closes at {close}, len {close-m.end()}")

body_idx = content_final.find('</body>')
script_idx = content_final.rfind('<script>')
print(f"Last </script> at {script_idx}")
print(f"</body> at {body_idx}")
if script_idx < body_idx:
    between = content_final[script_idx:body_idx]
    if '<style>' in between:
        print("WARNING: <style> found between </script> and </body>")
    else:
        print("OK: No stray <style> between </script> and </body>")
