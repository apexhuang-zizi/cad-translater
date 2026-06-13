# -*- coding: utf-8 -*-
import re
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()
settings = c[c.index('settings-overlay'):c.index('DXF Import Flow')]
# Check for English button text
english_btns = re.findall(r'id="btn-\w[^"]*">([^<]{2,20})</button>', settings)
print('Button text in settings:')
for b in english_btns:
    if b.isascii() and not any(ord(ch) > 127 for ch in b):
        print(f'  ENGLISH: {b}')
    else:
        print(f'  OK (mixed): {b}')
print('\nDone.')
