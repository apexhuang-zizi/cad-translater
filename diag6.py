# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if settings-overlay is hidden by default
print("=== Settings overlay default state ===")
idx = content.find('settings-overlay"')
if idx >= 0:
    print(content[idx:idx+80])

# Check if there are hidden classes on the overlay
print("\n=== hidden class on overlay ===")
if 'settings-overlay" class="hidden"' in content:
    print("OK - overlay starts hidden")
else:
    print("PROBLEM - overlay might be visible by default!")

# Check for duplicate script blocks
print("\n=== Script tags analysis ===")
import re
# Find ALL script blocks with content
scripts = re.findall(r'<script[^>]*>([\s\S]*?)</script>', content)
print(f"Script count: {len(scripts)}")
for i, s in enumerate(scripts):
    s_stripped = s.strip()
    if s_stripped:
        print(f"\n--- Script {i} ({len(s_stripped)} chars) ---")
        print(f"First 100: {s_stripped[:100]}")

# Check if the engine key toggle script is inside or outside the closure
print("\n=== Engine key toggle script ===")
idx = content.find("Engine key visibility toggle")
if idx >= 0:
    context = content[max(0,idx-200):idx+300]
    print(context)

# Check if the closure is at the end of file
print("\n=== Last script content check ===")
last_script_match = re.search(r'<script[^>]*>([\s\S]*?)</script>', content)
if last_script_match:
    last_script = last_script_match.group(1)
    if last_script.strip().endswith("})();"):
        print("Last script is properly closed")
    else:
        print("Last script NOT properly closed!")
        print(f"Last 100 chars: {repr(last_script[-100:])}")
