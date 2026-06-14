import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Search for .hidden CSS definition
# Look for .hidden { or .hidden{
import re
for m in re.finditer(r'\.hidden\s*\{', c):
    start = m.start()
    end = c.find('}', start)
    print(f'.hidden CSS at {start}: {c[start:end+1][:300]}')

# Check if .hidden class is added to overlay initially in HTML
overlay_idx = c.find('id="settings-overlay"')
if overlay_idx >= 0:
    tag_start = c.rfind('<', 0, overlay_idx)
    tag_end = c.find('>', overlay_idx)
    tag = c[tag_start:tag_end+1]
    print(f'\nOverlay HTML tag:\n  {tag[:300]}')

# Also search for any other element with z-index higher than 100
# that is position:fixed
for m in re.finditer(r'z-index\s*:\s*(\d+)', c):
    val = int(m.group(1))
    if val >= 100:
        # Find the selector or inline style
        start = max(0, m.start()-300)
        context = c[start:m.end()+50]
        # Extract the id/class selector
        id_match = re.search(r'id="([^"]+)"', context)
        class_match = re.search(r'#([a-zA-Z0-9_-]+)\s*\{', context)
        print(f'\nz-index:{val} at {m.start()}')
        if id_match: print(f'  element id: {id_match.group(1)}')
        if class_match: print(f'  css selector: #{class_match.group(1)}')
        print(f'  context: ...{repr(c[max(0,m.start()-80):m.end()+50])[:200]}')
