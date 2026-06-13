# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The problem: JS closure (11180-21084) runs BEFORE HTML elements (30737+)
# The JS is inside a <script> tag starting at 11142 and ending at 30690
# But the HTML content (settings panel) starts at 30737

# We need to split the last <script> tag into two:
# 1. Keep settings JS at the end (after HTML elements)
# 2. The script tag currently spans from ~11142 to ~30690 and contains the closure

# Let me find the exact boundaries
script_start = 11142  # <script> tag start
script_end = content.find('</script>', script_start)  # should be ~30690
closure_start = content.find('(function() {', script_start)
closure_end = content.find('})();', closure_start)

print(f"Script tag: {script_start} to {script_end}")
print(f"Closure: {closure_start} to {closure_end + 4}")

# Check what's BEFORE the closure in this script tag
before_closure = content[script_start + 8:closure_start]
print(f"\nBefore closure ({len(before_closure)} chars):")
print(repr(before_closure[:200]))
print(f"...")
print(repr(before_closure[-200:]))

# What's BETWEEN closure end and </script>?
between = content[closure_end + 4:script_end]
print(f"\nBetween closure and </script> ({len(between)} chars):")
print(repr(between[:200]))

# The issue: the entire script tag starts at 11142 and goes to 30690
# The settings HTML (30737+) is AFTER </script>
# But the closure IIFE runs immediately when the script is parsed (at 11142)
# So we need to either:
# A. Move the closure to after the HTML, OR
# B. Wrap it in DOMContentLoaded

# Simplest fix: wrap the closure in DOMContentLoaded or at least check overlay is not null
# But better fix: move the entire script block to after </style> of settings

# Let me check: what's between the end of closure and the rest of the page?
# The closure is at 11180-21084
# Then there's 21084 to 30690 (</script>) of... what?
mid_content = content[closure_end + 4:script_end]
print(f"\nContent after closure, before </script> ({len(mid_content)} chars)")
print(repr(mid_content[:500]))
