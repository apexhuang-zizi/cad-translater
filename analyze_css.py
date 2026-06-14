import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find .hidden CSS definition
idx = c.find('.hidden')
if idx >= 0:
    # Find the CSS block containing .hidden
    block_start = c.rfind('{', max(0, idx-500), idx+500)
    if block_start > 0:
        # Find the selector
        selector_start = c.rfind('}', 0, block_start)
        if selector_start < 0:
            selector_start = 0
        else:
            selector_start += 1
        selector = c[selector_start:block_start+1].strip()
        block_end = c.find('}', block_start)
        block = c[block_start:block_end+1]
        print(f'HIDDEN CSS:\n  selector: ...{selector[-200:]}\n  block: {block[:200]}')
        
        # Check if hidden hides via display:none or visibility
        if 'display' in block:
            print(f'  → uses display')
        if 'visibility' in block:
            print(f'  → uses visibility')
        if 'opacity' in block:
            print(f'  → uses opacity')

# Find #settings-overlay CSS
idx = c.find('#settings-overlay')
if idx >= 0:
    block_start = c.find('{', idx)
    block_end = c.find('}', block_start)
    block = c[block_start:block_end+1]
    print(f'\n#settings-overlay CSS:\n  {block[:300]}')

# Check if there's pointer-events anywhere affecting the overlay or button
for search in ['pointer-events', 'user-select']:
    count = c.count(search)
    if count > 0:
        print(f'\n{search}: {count} occurrences')
        positions = [m.start() for m in __import__('re').finditer(__import__('re').escape(search), c)]
        for p in positions[:5]:
            ctx = c[max(0,p-50):p+100]
            print(f'  ...{repr(ctx[:120])}...')
