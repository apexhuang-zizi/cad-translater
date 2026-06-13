# -*- coding: utf-8 -*-
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the actual stats display code
idx1 = content.find("data.engine + '")
if idx1 >= 0:
    print('Found engine stats at', idx1)
    print(repr(content[idx1-20:idx1+150]))
idx2 = content.find('tm_entries + ')
if idx2 >= 0:
    print('Found tm_entries at', idx2)
    print(repr(content[idx2-30:idx2+100]))
