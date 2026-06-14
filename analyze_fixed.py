import sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find ALL position:fixed elements with their display state
for m in re.finditer(r'<([a-zA-Z0-9]+)\s[^>]*position\s*:\s*fixed[^>]*>', c):
    match = m.group(0)
    tag_name = m.group(1)
    # Check for id
    id_match = re.search(r'id="([^"]+)"', match)
    # Check for class
    class_match = re.search(r'class="([^"]*hidden[^"]*)"', match)
    display_match = re.search(r'display\s*:\s*none', match)
    
    print(f'\nFixed element: <{tag_name}>')
    if id_match: print(f'  id: {id_match.group(1)}')
    if class_match: print(f'  class: {class_match.group(1)}')
    if display_match: print(f'  display:none in inline style')
    
    # Find the nearest class attribute
    cls = re.search(r'class="([^"]+)"', match)
    if cls:
        classes = cls.group(1)
        if 'hidden' in classes.split():
            print(f'  → has "hidden" class → display:none')

# Also find all divs with position:fixed
print('\n\n=== ALL position:fixed elements ===')
fixed_pattern = re.compile(r'position\s*:\s*fixed\s*;', re.IGNORECASE)
for m in fixed_pattern.finditer(c):
    # Look backwards for the element tag
    tag_start = c.rfind('<', 0, m.start())
    if tag_start < 0: continue
    tag_end = c.find('>', m.start())
    if tag_end < 0: continue
    tag = c[tag_start:tag_end+1]
    # Only show first 200 chars
    print(repr(tag[:200]))
