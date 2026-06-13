# -*- coding: utf-8 -*-
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for event listeners
listeners = [
    'btn-open-settings',
    'btn-close-settings',
    'settings-tab',
    'settings-overlay',
]
for l in listeners:
    idx = 0
    while True:
        pos = content.find(l, idx)
        if pos == -1:
            break
        ctx = content[max(0,pos-10):pos+120]
        print(f'{l}: {ctx[:100]}')
        print()
        idx = pos + 1
