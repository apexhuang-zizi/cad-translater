# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Final structure verification
print(f"Total file size: {len(content)} bytes")

# Script tag positions
import re
scripts = re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>', content)
print(f"Script tags: {len(scripts)}")
for i, s in enumerate(scripts):
    first_line = s.strip()[:80].replace('\n', ' ')
    has_overlay = 'overlay' in s
    has_btn_open = 'btn-open-settings' in s
    has_settings_html = 'settings-overlay"' in content[content.find(s):content.find(s)+5000]
    print(f"  [{i}] overlay={has_overlay} btn_open={has_btn_open} | {first_line}")

# Button position
btn = content.find('<button id="btn-open-settings"')
print(f"\nButton at: {btn}")

# Settings HTML position
settings_html = content.find('settings-overlay"')
print(f"Settings HTML at: {settings_html}")

# Correct IIFE position
overlay_var = content.find("var overlay = document.getElementById('settings-overlay')")
print(f"Correct IIFE var at: {overlay_var}")

# Script tag containing correct IIFE
script_start = content.rfind('<script>', 0, overlay_var)
script_end = content.find('</script>', overlay_var)
print(f"Script tag: {script_start} to {script_end}")

# Body close
body = content.find('</body>')
print(f"</body> at: {body}")

# Order check
print(f"\nOrder:")
print(f"  Button (btn-open-settings): {btn}")
print(f"  Settings HTML: {settings_html}")
print(f"  IIFE var: {overlay_var}")
print(f"  Script start: {script_start}")
print(f"  Script end: {script_end}")
print(f"  </body>: {body}")

# All should be in order: button < settings_html < script_start < overlay_var < script_end < body
ok = btn < settings_html < script_start < overlay_var < script_end < body
print(f"\n{'✅ ORDER CORRECT' if ok else '❌ ORDER WRONG'}")
