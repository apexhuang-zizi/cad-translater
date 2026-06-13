# -*- coding: utf-8 -*-
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check tm-stats-detailed
marker = "tm-stats-detailed"
idx = content.find(marker)
if idx >= 0:
    # This is the HTML element, let's find the JS that populates it
    # Look for the second loadTMStats function
    tm_start = content.find("function loadTMStats")
    if tm_start >= 0:
        block = content[tm_start:tm_start+400]
        print('loadTMStats block:')
        print(repr(block))
