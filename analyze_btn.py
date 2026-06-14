import sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the settings panel IIFE code
start = c.find('// Settings panel management')
end = c.find('// DXF Import Flow')
if start < 0:
    print('Settings IIFE not found!')
    sys.exit(1)

code = c[start:end]
print(f'Settings IIFE: {start} to {end} ({end-start} bytes)')

# Check for addEventListener on btn-open-settings
for line in code.split('\n'):
    if 'btn-open-settings' in line:
        print(f'  BTN REF: {line.strip()[:150]}')

# Check for overlay display toggle
for line in code.split('\n'):
    if 'overlay' in line.lower() and ('display' in line.lower() or 'style' in line.lower()):
        print(f'  OVERLAY: {line.strip()[:150]}')

# Look for potential errors - check if any DOM query could return null
null_queries = re.findall(r'document\.(getElementById|querySelector)\([\'"]([^\'"]+)[\'"]', code)
for method, qid in null_queries:
    in_html = f'id="{qid}"' in c[:start]
    if not in_html:
        print(f'  ⚠️ NULL RISK: document.{method}("{qid}") - NOT in DOM!')
    else:
        # Check if it's guarded
        query_call = f'document.{method}(\'{qid}\')'
        idx = code.find(query_call)
        if idx >= 0:
            surrounding = code[max(0,idx-50):idx+len(query_call)+80]
            has_guard = 'if' in surrounding or '&&' in surrounding or '?' in surrounding
            if not has_guard:
                print(f'  UNGUARDED: document.{method}("{qid}")')

# Check for pointer-events or other disabling CSS
for target in ['pointer-events', 'btn-open-settings', 'visibility', 'opacity:0']:
    count = c.count(target)
    if count > 0:
        idxs = [m.start() for m in re.finditer(re.escape(target), c)]
        for idx in idxs[:5]:
            ctx = c[max(0,idx-100):idx+100]
            print(f'  "{target}" at {idx}: ...{repr(ctx)}...')
