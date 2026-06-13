# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Strategy: 
# 1. Extract the settings panel JS closure from the big script tag
# 2. Remove it from the big script
# 3. Place it after </body> before </body>

# Find the big script tag
big_script_start = 11142
big_script_end = content.find('</script>', big_script_start)

# Find the settings closure inside it
settings_closure_start = content.find('(function() {\n    var overlay = document.getElementById', big_script_start)
settings_closure_end = content.find('})();', settings_closure_start) + 4

# Extract the settings closure block (including its comment)
settings_js_comment_start = content.find('// Settings panel management', settings_closure_start - 100)
settings_js_block = content[settings_js_comment_start:settings_closure_end]

print(f"Settings JS block ({len(settings_js_block)} chars):")
print(f"Starts: {settings_js_block[:80]}")
print(f"Ends: {settings_js_block[-80:]}")

# Extract the DXF import closure (comes after settings closure)
dxf_comment_start = content.find('// DXF Import Flow', settings_closure_end)
dxf_block = content[dxf_comment_start:big_script_end]

print(f"\nDXF block ({len(dxf_block)} chars):")
print(f"Ends: {dxf_block[-50:]}")

# Reconstruct: big script tag WITHOUT settings closure, WITH DXF
# The big script starts with settings, then has other content, then DXF
# Let's check what's between settings comment and DXF comment
between = content[settings_closure_end:dxf_comment_start]
print(f"\nBetween settings closure end and DXF comment ({len(between)} chars):")
print(repr(between[:200]))

# Actually, the script tag has:
# 1. Settings panel management comment + closure
# 2. DXF Import Flow comment + closure
# 
# We need to extract just the settings JS and move it to before </body>
# Keep everything else in the big script

# Build new content
new_script = content[settings_closure_end:dxf_comment_start + len(dxf_block)]
# But we also need the closing </script> tag
new_script_with_closing = new_script + '\n' + content[big_script_end:big_script_end+9]  # include </script>

# Remove settings JS from big script and put DXF at end
before_settings = content[big_script_start + 8:settings_js_comment_start]
after_settings_to_dxf = content[settings_closure_end:dxf_comment_start]

# New big script: just DXF import and closing
new_big_script = content[big_script_start + 8:dxf_comment_start] + content[big_script_end:big_script_end+9]

# Find </body>
body_close = content.find('</body>')

# New structure:
# [original content up to big script start]
# [new big script (DXF only)]
# [original content between old big script end and body close (settings HTML)]
# [settings JS closure]
# </body>

settings_html = content[dxf_comment_start:body_close]  # DXF flow HTML + settings panel HTML
print(f"\nSettings HTML area ({len(settings_html)} chars)")
print(f"Starts: {settings_html[:80]}")
print(f"Ends: {settings_html[-50:]}")

# Build final content
new_content = (content[:big_script_start] + 
               new_big_script + 
               settings_html + 
               '\n<script>\n' + settings_js_block + '\n</script>\n' +
               content[body_close:])

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("\n=== Verification ===")
# Check script tags
import re
scripts = re.findall(r'<script[\s\S]*?</script>', new_content)
print(f"Script tags: {len(scripts)}")
for i, s in enumerate(scripts):
    short = s.strip()[:60].replace('\n', ' ')
    print(f"  {i}: {short}")

# Check body close position
bc = new_content.find('</body>')
ls = new_content.rfind('<script>')
print(f"Last script before body: {ls}")
print(f"</body> at: {bc}")

# Check overlay var position vs element position
overlay_js = new_content.find("var overlay = document.getElementById")
overlay_html = new_content.find("settings-overlay\"")
print(f"Overlay JS at: {overlay_js}, HTML at: {overlay_html}")
if overlay_js > overlay_html:
    print("OK: JS after HTML")
else:
    print("STILL PROBLEM: JS before HTML")
