# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all <style> tags
import re
style_matches = list(re.finditer(r'<style[^>]*>', content))
print(f"Found {len(style_matches)} <style> tags")
for i, m in enumerate(style_matches):
    print(f"\n--- Style tag {i} at char {m.start()} ---")
    # Find matching </style>
    close = content.find('</style>', m.end())
    if close >= 0:
        style_content = content[m.end():close]
        print(f"Closes at {close}, length: {len(style_content)}")
        print(f"First 80: {style_content[:80]}")
        print(f"Last 80: {style_content[-80:]}")
    else:
        print("NO CLOSING </style> FOUND!")

# Also find the settings gear button HTML
idx = content.find('btn-open-settings')
if idx >= 0:
    print(f"\n=== Gear button at {idx} ===")
    print(repr(content[idx:idx+200]))

# Check if there's a duplicate style block that leaks
# The issue might be that the settings CSS is placed AFTER the </body> or in wrong place
# Let's find the position of settings CSS vs body/script tags

body_idx = content.find('</body>')
script_idx = content.find('<script>')
settings_css_idx = content.find('#settings-overlay {')

print(f"\n=== Position map ===")
print(f"<script> at {script_idx}")
print(f"#settings-overlay CSS at {settings_css_idx}")
print(f"</body> at {body_idx}")

if settings_css_idx > body_idx:
    print("ERROR: Settings CSS is AFTER </body>!")
elif settings_css_idx > script_idx:
    print("Settings CSS is AFTER <script> - this is the problem!")
    # Show what's between script start and settings CSS
    between = content[script_idx:settings_css_idx]
    print(f"Between script start and settings CSS: {len(between)} chars")
    # Check if there's a </script> before settings CSS
    close_script = content.find('</script>', script_idx)
    if close_script >= 0:
        print(f"</script> at {close_script}")
        print(f"Content between </script> and settings CSS:")
        print(repr(content[close_script:settings_css_idx]))
