import sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find ALL CSS that might match btn-open-settings
# Look in both style blocks and inline
for pattern in ['#btn-open', '.btn-sm', '.btn-outline', 'button.btn', 'button[class*="btn"]']:
    for m in re.finditer(re.escape(pattern) + r'[^a-zA-Z]', c):
        # Find the surrounding CSS block
        block_start = c.rfind('{', max(0, m.start()-500), m.start()+100)
        if block_start < 0: continue
        # Find selector
        sel_start = c.rfind('}', 0, block_start)
        if sel_start < 0: sel_start = 0
        else: sel_start += 1
        selector = c[sel_start:block_start].strip()[-200:]
        block_end = c.find('}', block_start)
        block = c[block_start:block_end+1][:300]
        print(f'\n--- {pattern} at {m.start()} ---')
        print(f'  selector: ...{repr(selector)}')
        print(f'  block: {repr(block[:200])}')

# Also check for .btn class
print('\n\n=== .btn CSS rules ===')
for m in re.finditer(r'\.btn\s*\{', c):
    end = c.find('}', m.start())
    print(f'  at {m.start()}: {c[m.start():end+1][:300]}')
