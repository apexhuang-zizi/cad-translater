# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Final structure check
print(f"File size: {len(content)}")
print(f"</body> at {content.find('</body>')}")
print(f"</html> at {content.find('</html>')}")

# Check for any duplicate content or leftover strings
# Count key elements
imports = content.count('src="/static/')
print(f"Static imports: {imports}")

# Check for getOverlay remnants
getOverlays = content.count('getOverlay')
print(f"getOverlay references: {getOverlays}")

# Count IIFEs
import re
iifes = re.findall(r'\(function\s*\(\s*\)\s*\{', content)
print(f"IIFE count: {len(iifes)}")

# Check for engine-btn click listeners in script 0 that might conflict
script0_end = content.find('</script>', 0)
script0 = content[0:script0_end]
if 'engine-btn' in script0:
    # Check if this listener might interfere with settings panel
    idx = script0.find('engine-btn')
    print(f"\nScript 0 engine-btn context:")
    print(repr(script0[max(0,idx-20):idx+100]))

# Also check if engine-btn click listener in script 0 might capture
# clicks inside the settings modal
# The settings panel has engine-btn elements inside it
# If script 0's listener uses event delegation without checking target,
# it might interfere
