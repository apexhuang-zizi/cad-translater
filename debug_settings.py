# -*- coding: utf-8 -*-
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find ALL occurrences of settings-overlay
idx = 0
count = 0
while True:
    pos = content.find('settings-overlay', idx)
    if pos == -1:
        break
    # Show surrounding context
    print(f'\n--- occurrence #{count} at char {pos} ---')
    print(content[pos:pos+80])
    count += 1
    idx = pos + 1

# Also find all gear button references
idx = 0
count = 0
while True:
    pos = content.find('btn-open-settings', idx)
    if pos == -1:
        break
    print(f'\n--- btn-open-settings #{count} at char {pos} ---')
    print(content[pos-30:pos+120])
    count += 1
    idx = pos + 1

# Also find btn-close-settings
idx = 0
count = 0
while True:
    pos = content.find('btn-close-settings', idx)
    if pos == -1:
        break
    print(f'\n--- btn-close-settings #{count} at char {pos} ---')
    print(content[pos-30:pos+80])
    count += 1
    idx = pos + 1
