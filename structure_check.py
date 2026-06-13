# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Show key position markers
markers = [
    ('</script> (script 0)', content.find('</script>', 0)),
    ('</script> (api.js)', content.find('api.js')),
    ('<!-- Translator v2 Settings Panel -->', content.find('<!-- Translator v2 Settings Panel -->')),
    ('<style> (settings)', content.find('<style>')),
    ('</style> (settings)', content.find('</style>')),
    ('</script> (settings JS)', content.find('Settings panel management')),
    ('</body>', content.find('</body>')),
]

# Actually let's just show the overall structure
import re
# Find major structural elements
for pattern in [
    r'<script[\s>]',
    r'</script>',
    r'<style[\s>]',
    r'</style>',
    r'</body>',
    r'<!-- Translator v2 Settings Panel -->',
    r'<!-- Settings gear button',
]:
    matches = list(re.finditer(pattern, content))
    for m in matches:
        tag = pattern.replace(r'<', '').replace(r'>', '').replace(r'\s', '').replace(r'\>', '').replace(r'\.', '')
        print(f"{tag:30s} at {m.start()}")
