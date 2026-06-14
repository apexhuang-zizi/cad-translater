import sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the big script that contains the settings IIFE
script_start = c.find('// Settings panel management')
script_tag_start = c.rfind('<script>', 0, script_start)
settings_iife = script_start

print(f'<script> tag starts at: {script_tag_start}')
print(f'Settings IIFE starts at: {settings_iife}')
print(f'Between script tag and IIFE: {settings_iife - script_tag_start - 8} bytes')
print(f'\nContent between <script> and settings IIFE:')
print(repr(c[script_tag_start:script_start]))

# Also check: is there a <script> before this one that could have errors?
# Find ALL <script> tags and check order
all_scripts = list(re.finditer(r'<script\b[^>]*>', c))
print(f'\n\nTotal <script> tags: {len(all_scripts)}')
for i, s in enumerate(all_scripts):
    end = c.find('</script>', s.end())
    content_len = end - s.end() if end > 0 else 0
    # Show first 100 chars of content
    content_start = c[s.end():min(s.end()+100, end) if end > 0 else s.end()+100]
    print(f'  #{i}: {s.start()}-{end if end>0 else "?"} ({content_len}B) → {repr(content_start[:80])}')
