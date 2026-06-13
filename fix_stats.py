# -*- coding: utf-8 -*-
"""Fix remaining English stats strings"""

filepath = 'templates/index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the stats display line
old1 = "' + data.engine + ' | TM: ' + data.stats.tm_entries + ' entries | Glossary: ' + data.stats.glossary_terms + ' terms | Synonyms: ' + data.stats.synonym_rules + ' rules'"
new1 = "' + data.engine + ' | TM: ' + data.stats.tm_entries + '条 | 术语库: ' + data.stats.glossary_terms + '条 | 同义词: ' + data.stats.synonym_rules + '条'"

if old1 in content:
    content = content.replace(old1, new1)
    print('Fixed stats line 1')
else:
    print('NOT FOUND: stats line 1')

# Fix tm-stats-display
old2 = "'<strong>TM:</strong> ' + s.tm_entries + ' entries | <strong>Glossary:</strong> ' + s.glossary_terms + ' terms | <strong>Synonyms:</strong> ' + s.synonym_rules + ' rules'"
new2 = "'<strong>TM:</strong> ' + s.tm_entries + '条 | <strong>术语库:</strong> ' + s.glossary_terms + '条 | <strong>同义词:</strong> ' + s.synonym_rules + '条'"

if old2 in content:
    content = content.replace(old2, new2)
    print('Fixed stats line 2')
else:
    print('NOT FOUND: stats line 2')

# Fix tm-stats-detailed
old3 = "'<strong>Entries:</strong> ' + s.tm_entries + ' | <strong>Glossary:</strong> ' + s.glossary_terms + ' | <strong>Synonyms:</strong> ' + s.synonym_rules'"
new3 = "'<strong>词条:</strong> ' + s.tm_entries + '条 | <strong>术语库:</strong> ' + s.glossary_terms + '条 | <strong>同义词:</strong> ' + s.synonym_rules + '条'"

if old3 in content:
    content = content.replace(old3, new3)
    print('Fixed stats line 3')
else:
    print('NOT FOUND: stats line 3')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('Done.')
