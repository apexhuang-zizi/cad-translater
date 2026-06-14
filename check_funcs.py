import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find settings IIFE end
iife_start = c.find('// Settings panel management')
dxf_start = c.find('// DXF Import Flow')
iife_code = c[iife_start:dxf_start]

# Check all function definitions and calls
import re
funcs = re.findall(r'function\s+(\w+)', iife_code)
calls = re.findall(r'(\w+)\(\)', iife_code)
print('Defined functions:', sorted(set(funcs)))
print('Called functions:', sorted(set(calls)))

# Check if loadCurrentTab and loadTMStats are defined
for f in ['loadCurrentTab', 'loadTMStats']:
    if f in funcs:
        print(f'  {f}: DEFINED ✅')
    else:
        print(f'  {f}: MISSING ⚠️ - called but not defined in this IIFE')
