# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Show the structure of the big script tag
big_script_start = content.find('<script>\n// Settings panel management')
big_script_end = content.find('</script>', big_script_start)

if big_script_start < 0:
    # Try to find any standalone script
    scripts = []
    idx = 0
    while True:
        pos = content.find('<script>', idx)
        if pos < 0:
            break
        close = content.find('</script>', pos)
        if close < 0:
            break
        scripts.append((pos, close))
        idx = close + len('</script>')
    
    print("All standalone script tags:")
    for start, end in scripts:
        snippet = content[start:end].strip()[:80]
        print(f"  {start}-{end}: {snippet}")
    print(f"\nTotal: {len(scripts)} script tags")
    
    # Find which one contains the settings closure
    for start, end in scripts:
        block = content[start:end]
        if 'var overlay = document.getElementById' in block:
            print(f"\nSettings closure is in script at {start}-{end} ({end-start} chars)")
            # Show what's in this script
            print(f"\nFirst 200: {block[:200]}")
            print(f"\nLast 200: {block[-200:]}")
