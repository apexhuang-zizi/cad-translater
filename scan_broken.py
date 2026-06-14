import re

with open(r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\static\js\app.js', encoding='utf8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    stripped = line.rstrip()
    # Skip comments
    if stripped.lstrip().startswith('//'):
        continue
    # Find any line where a variable reference (data.X, .innerHTML, etc.)
    # appears immediately after Chinese/Vietnamese chars with no clear string boundary
    # The key corruption pattern: Chinese/Vietnamese chars followed by JS without ' + 
    m = re.search(r"[\u4e00-\u9fff\u00C0-\u1EF9\u0102\u0103\u0110\u0111\u01A0\u01A1\u01AF\u01B0\u1EA0-\u1EF9]\s*data\.", stripped)
    if m:
        print(f'Line {i}: DATA-REF: {stripped[:200]}')
    m = re.search(r"[\u4e00-\u9fff\u00C0-\u1EF9]\s*\.innerHTML", stripped)
    if m:
        print(f'Line {i}: INNER-HTML: {stripped[:200]}')
    m = re.search(r"[\u4e00-\u9fff\u00C0-\u1EF9]\s*loadTM", stripped)
    if m:
        print(f'Line {i}: LOAD-TM: {stripped[:200]}')
    # Another pattern: variable name immediately follows Chinese text in a single-quoted string
    m = re.search(r"[\u4e00-\u9fff\u00C0-\u1EF9][a-z_]+\(", stripped)
    if m:
        # Check if this is inside a quoted string context
        if "'" in stripped.split(m.group())[0]:
            print(f'Line {i}: FUNC-CALL: {stripped[:200]}')

print('DONE')
