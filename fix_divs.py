# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The settings block goes from <!-- Translator v2 Settings Panel --> to just before <!-- Settings gear button -->
start = content.find('<!-- Translator v2 Settings Panel -->')
end_marker = '<!-- Settings gear button -->'
end = content.find(end_marker)

# Count open divs in settings block (from start to end_marker)
settings_block = content[start:end]
# Count all <div that are NOT in <script or closing
opens = settings_block.count('<div')
closes = settings_block.count('</div>')
print(f"Opens: {opens}, Closes: {closes}, Missing: {opens - closes}")

# Add the missing </div> tags before the settings gear button
missing = '<\/div>' * (opens - closes)
insertion = '\n</div>\n' * (opens - closes)

content = content[:end] + insertion + content[end:]

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Added {opens-closes} closing </div> tags")

# Verify
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content2 = f.read()
settings_block2 = content2[start:end_marker]
opens2 = settings_block2.count('<div')
closes2 = settings_block2.count('</div>')
print(f"After fix: Opens: {opens2}, Closes: {closes2}, Diff: {opens2-closes2}")
