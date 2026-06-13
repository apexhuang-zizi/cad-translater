# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The stale IIFE at 11172 throws an error.
# But JS errors in IIFEs don't prevent subsequent code from running
# So the DXF closure (also in the same script tag) should still work.
# And the correct settings IIFE (in a separate script tag) should also work.

# Let me think about this differently. The user says the button is still not clickable.
# Maybe the correct IIFE IS registering the listener, but something else is wrong.
# Like the button element has some CSS issue (pointer-events, z-index, etc.)

# Check the button's CSS
btn_idx = content.find('<button id="btn-open-settings"')
if btn_idx >= 0:
    btn_html = content[btn_idx:btn_idx+200]
    print(f"Button HTML: {btn_html}")

# Check if there's a CSS rule that hides or blocks the button
# Look for CSS rules related to the button
import re
css_rules = list(re.finditer(r'[.#][a-zA-Z][^{}]*\{[^}]*\}', content))
for m in css_rules:
    rule = m.group()
    if 'btn-open' in rule or 'gear' in rule.lower():
        print(f"CSS rule: {rule[:100]}")

# Check if the button is inside a container that might be blocking clicks
# Check the surrounding HTML
surround = content[max(0,btn_idx-100):btn_idx+200]
print(f"\nSurrounding HTML:\n{surround}")

# Maybe the issue is that the correct IIFE's addEventListener throws too?
# Check: is the button element actually in the DOM when the correct IIFE runs?
# The correct IIFE is in a <script> tag right after the button HTML
# So yes, the button should exist

# Let me check if there's a duplicate button element
all_buttons = list(re.finditer(r'<button[^>]*id="btn-open-settings"[^>]*>', content))
print(f"\nButton elements: {len(all_buttons)}")
for i, m in enumerate(all_buttons):
    print(f"  Button {i} at {m.start()}: {m.group()}")

# Also check: is there a CSS class that might hide the button?
# Check if btn-open-settings has any CSS that sets pointer-events: none or display: none
for m in re.finditer(r'#btn-open-settings[^{]*\{[^}]*\}', content):
    print(f"Button CSS: {m.group()}")
