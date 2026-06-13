# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The stale IIFE at 11172:
# 1. var getOverlay = function() { ... }
# 2. var currentTab = 'engines'  
# 3. document.getElementById('btn-open-settings').addEventListener(...)
# 4. document.getElementById('btn-close-settings').addEventListener(...)
# 5. Various tab handlers
# 6. loadTMStats() call at the end

# Step 3 will fail if btn-open-settings doesn't exist yet
# But btn-open-settings is at 35866, AFTER the big script tag ends at 30679
# Wait no - the HTML button is at 35866, and the big script ends at 30679
# So btn-open-settings doesn't exist when the stale IIFE runs!

# Let me verify
btn_open = content.find('btn-open-settings')
print(f"btn-open-settings first at: {btn_open}")

# Check: is the stale IIFE's addEventListener wrapped in try/catch?
stale_iife = content[11172:15668]
if 'try' in stale_iife:
    print("Stale IIFE has try/catch")
else:
    print("Stale IIFE has NO try/catch - will throw Error!")

# The error would prevent subsequent code from running
# But the correct IIFE at 39218 is AFTER </script>, so it runs after DOM is ready
# So the error in stale IIFE should NOT affect the correct one

# Unless... the stale IIFE error prevents the rest of the page from loading?
# No, JS errors don't block parsing. The correct IIFE should still work.

# Let me check: does the correct IIFE actually register the button listener?
correct_iife = content[39218:49149]
if "btn-open-settings" in correct_iife:
    print("Correct IIFE has btn-open-settings listener")
    # Find the exact registration
    idx = correct_iife.find("btn-open-settings")
    print(f"Registration context: {correct_iife[idx-20:idx+100]}")
else:
    print("Correct IIFE MISSING btn-open-settings listener!")

# Check if there's a race condition: maybe the stale IIFE error bubbles up
# and prevents the correct IIFE from running?
# No, they're in separate script blocks. Different parsing contexts.

# Maybe the issue is that the stale IIFE's addEventListener throws,
# but the correct IIFE's listeners ARE working. Let me check if the
# button element itself exists in the DOM at parse time.

# Actually - the stale IIFE is INSIDE the big <script> tag (11142-30679)
# The button HTML is at 35866, which is AFTER the </script> tag
# So when the stale IIFE tries getElementById('btn-open-settings'), it returns null
# Calling addEventListener on null throws TypeError
# This error stops the stale IIFE, but the rest of the big script continues

# The correct IIFE is a SEPARATE <script> tag after the HTML
# So it should work fine

# Unless... there's something else preventing the correct IIFE from working.
# Let me check if the correct IIFE is actually a valid standalone script

correct_script_start = content.find('<script>', 39000)
correct_script_end = content.find('</script>', correct_script_start)
print(f"\nCorrect settings script: {correct_script_start} to {correct_script_end}")
print(f"Content: {content[correct_script_start:correct_script_end+9][:100]}")
