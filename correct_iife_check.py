# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Let me check something critical: the correct IIFE at 39218
# Is it inside the big <script> tag or a separate one?
# The big script ends at 30679. The button is at 35913.
# The settings CSS <style> is at 36041.
# The correct script <script> should be at ~39180.

# So the flow is:
# </script> at 30679
# Settings HTML starts
# Button at 35913
# <style> at 36041
# </style> at 39124
# <script> at 39180  ← correct IIFE starts here
# </script> at 49123
# </body> at 49087  ← wait, this is BEFORE </script>?

body_close = content.find('</body>', 39000)
print(f"</body> at {body_close}")
print(f"</script> at {49123}")
print(f"</html> at {content.find('</html>')}")

# If </body> is at 49087 and </script> is at 49123, then the script is INSIDE </body>
# That's unusual but valid HTML5. The script will execute and the DOM is ready.

# But wait - the </body> at 49087 vs </script> at 49123
# Let me check the exact sequence
print(f"\nAround </body>:")
print(repr(content[49070:49140]))

# Also check: is the correct IIFE's addEventListener actually finding the button?
# The button is at 35913, the script starts at 39180
# By the time the script runs, the button element exists in the DOM
# So getElementById('btn-open-settings') should return the button element

# Let me check: does the correct IIFE have ANY errors?
correct_iife = content[39218:49149]
# Check for null checks or try/catch
if 'try' in correct_iife:
    print("Correct IIFE has try/catch")
else:
    print("Correct IIFE has NO try/catch")

# Check the order of operations in the correct IIFE
lines = correct_iife.split('\n')
for i, line in enumerate(lines[:20]):
    stripped = line.strip()
    if stripped and not stripped.startswith('//'):
        print(f"  Line {i}: {stripped[:80]}")
