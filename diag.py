# -*- coding: utf-8 -*-
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Check if the overlay variable is defined correctly
idx = content.find("getElementById('btn-open-settings').addEventListener")
if idx >= 0:
    block = content[max(0,idx-200):idx+100]
    print("Context around btn-open-settings listener:")
    print(block)
    print()

# 2. Check if overlay variable is defined
idx = content.find("var overlay = document.getElementById('settings-overlay')")
if idx >= 0:
    print("Overlay var found")
    print(content[idx:idx+100])
else:
    print("OVERLAY VAR NOT FOUND!")

# 3. Check the end of the file for garbage
print("\n--- Last 2000 chars of file ---")
print(repr(content[-2000:]))
