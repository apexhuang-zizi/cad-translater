# -*- coding: utf-8 -*-
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find("tm-stats-display").innerHTML
if idx >= 0:
    print('Found tm-stats-display innerHTML')
    block = content[idx:idx+300]
    print(repr(block))

# Also find the second one
idx2 = content.find("tm-stats-detailed").innerHTML
if idx2 >= 0:
    print('Found tm-stats-detailed innerHTML')
    block2 = content[idx2:idx2+300]
    print(repr(block2))
