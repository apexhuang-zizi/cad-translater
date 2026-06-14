import sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Check script #0 content for errors
start0 = 10609
end0 = c.find('</script>', start0)
script0 = c[start0:end0]
print('=== Script #0 (Engine toggle) ===')
print(script0[:600])

# Check scripts 1-3 (possibly external)
for i in range(1, 4):
    s_tag = re.finditer(r'<script\b[^>]*>', c)
    tags = list(s_tag)
    if i < len(tags):
        tag = tags[i]
        tag_text = c[tag.start():tag.end()]
        print(f'\n=== Script #{i}: {tag_text[:120]} ===')
        
        # Check if self-closing or has src
        if '/>' in tag_text or 'src=' in tag_text:
            print('  → self-closing or external src')
