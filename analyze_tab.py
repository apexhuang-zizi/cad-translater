import sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

start = c.find('// Settings panel management')
end = c.find('// DXF Import Flow')
code = c[start:end]

# Find all tab- related code
for i, line in enumerate(code.split('\n')):
    if 'tab-' in line.lower():
        print(f'{i}: {line.strip()[:150]}')

print('\n--- Find exact context around getElementById("tab-") ---')
idx = code.find('getElementById("tab-")')
if idx >= 0:
    surrounding = code[max(0,idx-400):min(len(code),idx+200)]
    print(surrounding)
