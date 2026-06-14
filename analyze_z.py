import sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find all z-index declarations
zidx_pattern = re.compile(r'z-index\s*:\s*(\d+)')
matches = list(zidx_pattern.finditer(c))
print(f'Total z-index declarations: {len(matches)}')
for m in matches:
    start = max(0, m.start()-200)
    end = min(len(c), m.end()+200)
    context = c[start:end]
    # Extract the selector/rules around it
    lines = context.split('\n')
    compact = ' '.join(l.strip() for l in lines)
    # Try to find what element this is
    # Look for id or class near this
    sel_match = re.search(r'(#[a-zA-Z0-9_-]+|\.[a-zA-Z0-9_-]+)\s*\{[^}]*z-index\s*:\s*\d+', compact)
    if not sel_match:
        sel_match = re.search(r'(?:^|})([^}]*?)z-index\s*:\s*\d+', compact)
    
    val = int(m.group(1))
    if val >= 100:
        print(f'  z-index: {val} at pos {m.start()}')
        # Show selector context
        selector_start = c.rfind('{', max(0, m.start()-500), m.start())
        selector_end = c.rfind('}', max(0, m.start()-500), m.start())
        if selector_start > selector_end:
            block_start = max(0, selector_start-300)
            block_text = c[block_start:selector_start].strip()
            # Get the last meaningful part
            last_part = block_text[-200:]
            print(f'    near: ...{repr(last_part)[:200]}')
        else:
            print(f'    inline style context: {repr(c[max(0,m.start()-80):m.end()+80])[:200]}')

# Also check for position:fixed|absolute at top:0|right:0 that might cover button
print('\n\nChecking for covering elements at top-right:')
# Simple approach: find all elements with position:fixed and check their style
for pat in ['position:fixed', 'position:fixed;top:0', 'position:fixed;top:0;right:0']:
    count = c.count(pat)
    print(f'  "{pat}" count: {count}')
