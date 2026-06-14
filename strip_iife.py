import re

path = r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\templates\index.html'
with open(path, encoding='utf8') as f:
    t = f.read()

si = t.find("console.log('SETTINGS-IIFE-START'")
start = t.rfind('<script>', 0, si)
ei = t.find('</body>', si)

print(f'start={start}, si={si}, ei={ei}')
print(f'Before script tag: ...{t[start-30:start]}...')
print(f'At start: ...{t[start:start+80]}...')
print(f'At body end: ...{t[ei-30:ei+20]}...')

result = t[:start] + t[ei:]
with open(path, 'w', encoding='utf8') as f:
    f.write(result)

print(f'Done. Old length: {len(t)}, New length: {len(result)}')
