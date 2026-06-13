# -*- coding: utf-8 -*-
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find the second btn-open-settings in the HTML (not JS)
idx = 0
positions = []
while True:
    pos = content.find('btn-open-settings', idx)
    if pos == -1:
        break
    # Get context to figure out if it's HTML or JS
    ctx = content[pos-40:pos+80]
    is_html = '<button' in ctx or 'btn-open' in ctx and 'getElementById' not in ctx
    print(f'#{len(positions)} at char {pos}: HTML={is_html}')
    print(f'  {ctx[:100]}')
    print()
    positions.append(pos)
    idx = pos + 1

# There should be 2 HTML buttons and 1 JS reference
# The old button is the second HTML one (index 1)
if len(positions) >= 2:
    old_btn_start = positions[1]
    # Find the end of this button element
    close_btn = content.find('</button>', old_btn_start)
    if close_btn >= 0:
        end_pos = close_btn + len('</button>')
        # Trim any trailing whitespace/newlines
        after = content[end_pos:end_pos+50]
        print(f'Old button ends at {end_pos}')
        print(f'After: {repr(after)}')
        
        # Remove it
        content = content[:old_btn_start] + content[end_pos:]
        count = content.count('btn-open-settings')
        print(f'Remaining btn-open-settings: {count}')
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Removed old button')
