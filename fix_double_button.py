# -*- coding: utf-8 -*-
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The new settings panel block ends with our custom style block
# After that there's a duplicate old button
# Find the new button and remove the old one

# Find "Settings gear button in header" - that's the old one
old_block_start = content.find('<!-- Settings gear button in header -->')
# Find "Settings gear button" (without "in header") - that's our new one
new_block_start = content.find('<!-- Settings gear button -->', old_block_start + 100)

if old_block_start >= 0 and new_block_start >= 0:
    print(f'Old block at {old_block_start}')
    print(f'New block at {new_block_start}')
    
    # Find the end of the old button line
    old_btn_end = content.find('title="Translator v2 Settings"', old_block_start)
    if old_btn_end >= 0:
        old_btn_full_end = content.find('">', old_btn_end) + 2  # >" to get past the closing tag
        # Find the closing </button>
        close_btn = content.find('</button>', old_btn_end)
        if close_btn >= 0:
            old_btn_full_end = close_btn + len('</button>')
    
    # Also need to remove any trailing newline/whitespace
    if old_btn_full_end >= 0:
        # Remove from old_block_start to the end of the old button + trailing newlines
        # But stop before the new button
        content = content[:old_block_start] + '\n\n' + content[new_block_start:]
        print(f'Removed old button block from {old_block_start} to {new_block_start}')
    else:
        print(f'Could not find end of old button')
else:
    print(f'old_block_start={old_block_start}, new_block_start={new_block_start}')

# Verify: count btn-open-settings occurrences
count = content.count('btn-open-settings')
print(f'Remaining btn-open-settings references: {count}')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
