import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Show the exact CSS blocks
for m in __import__('re').finditer(r'#settings-overlay\s*\{[^}]*\}', c):
    print(repr(m.group()))

print('\n--- .hidden rules ---')
for m in __import__('re').finditer(r'\.hidden\s*\{[^}]*\}', c):
    print(repr(m.group()))

print('\n--- Specificity: #id = (1,0,0) vs .class = (0,1,0) ---')
print('ID selector WINS → display:flex overrides display:none!')
