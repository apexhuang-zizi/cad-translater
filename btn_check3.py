# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the JS closure that handles settings
closure_start = content.find('(function() {')
if closure_start >= 0:
    # Find the end of the closure
    closure_end = content.find('})();', closure_start)
    if closure_end >= 0:
        closure = content[closure_start:closure_end+4]
        print(f"Closure from {closure_start} to {closure_end+4} ({len(closure)} chars)")
        print(f"First 100: {closure[:100]}")
        print(f"Last 100: {closure[-100:]}")
        
        # Check if it contains the overlay var
        if "var overlay = document.getElementById('settings-overlay')" in closure:
            print("\nOK: closure has overlay var")
        else:
            print("\nERROR: closure missing overlay var!")
            
        # Check if it contains the event listener
        if "btn-open-settings" in closure:
            print("OK: closure has btn-open-settings listener")
        else:
            print("ERROR: closure missing btn-open-settings listener!")
    else:
        print("No closure end found!")
else:
    print("No closure start found!")

# Now find where the script tag containing this closure is
# And check if there's a DOMContentLoaded wrapper
script_tag = content.rfind('<script>')
if script_tag >= 0:
    close_script = content.find('</script>', script_tag)
    if close_script >= 0:
        script_content = content[script_tag:close_script + len('</script>')]
        print(f"\n=== Last script tag ===")
        print(f"Starts at {script_tag}, ends at {close_script + 11}")
        print(f"Content length: {len(script_content)}")
        if 'DOMContentLoaded' in script_content:
            print("Has DOMContentLoaded")
        else:
            print("NO DOMContentLoaded - closure runs immediately")
        # The closure (function(){...})() runs immediately when parsed
        # So if the HTML is after the script, the elements don't exist yet!
        print(f"\nClosure at: {closure_start}")
        print(f"HTML element at: {content.find('settings-overlay\"')}")
        print(f"Button at: {content.find('<button id=\"btn-open-settings\"')}")
