# -*- coding: utf-8 -*-
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the event listener code block
idx = content.find("getElementById('btn-open-settings').addEventListener")
if idx >= 0:
    block = content[idx:idx+500]
    print("OPEN LISTENER:")
    print(block)
    print()

idx = content.find("getElementById('btn-close-settings').addEventListener")
if idx >= 0:
    block = content[idx:idx+500]
    print("CLOSE LISTENER:")
    print(block)
