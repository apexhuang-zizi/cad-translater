# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Find the gear button and check its attributes
idx = content.find('btn-open-settings')
print("=== Gear button HTML ===")
print(repr(content[idx:idx+250]))

# 2. Find the JS that handles it
idx2 = content.find("getElementById('btn-open-settings').addEventListener")
print("\n=== JS listener ===")
print(repr(content[idx2:idx2+300]))

# 3. Find where overlay variable is declared
idx3 = content.find("var overlay = document.getElementById")
print("\n=== Overlay var declaration ===")
print(repr(content[idx3:idx3+200]))

# 4. Is the overlay element in the DOM?
idx4 = content.find("settings-overlay\"")
print("\n=== Overlay HTML element ===")
print(repr(content[idx4:idx4+100]))

# 5. Check if the JS closure is AFTER the HTML element
overlay_html_pos = content.find('settings-overlay"')
overlay_js_pos = content.find("var overlay = document.getElementById")
print(f"\nOverlay HTML at: {overlay_html_pos}")
print(f"Overlay JS at: {overlay_js_pos}")
if overlay_js_pos > overlay_html_pos:
    print("OK: JS comes after HTML element")
else:
    print("PROBLEM: JS comes BEFORE HTML element!")
