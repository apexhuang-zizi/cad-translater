# -*- coding: utf-8 -*-
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

old = "Engine: \\' + data.engine + \\' | TM: \\' + data.stats.tm_entries + \\' entries | Glossary: \\' + data.stats.glossary_terms + \\' terms | Synonyms: \\' + data.stats.synonym_rules + \\' rules"
new = "\\u00e1 \\u00ea引擎: \\' + data.engine + \\' | TM: \\' + data.stats.tm_entries + \\'条 | \u01a1\u1ee5\u1eadu th\u1ee3 c\u1ee5: \\' + data.stats.glossary_terms + \\'条 | \u0111\u1ed3ng ngh\u0129a: \\' + data.stats.synonym_rules + \\'条"

# Use direct string matching without escaping
old_raw = "Engine: \\' + data.engine + \\' | TM: \\' + data.stats.tm_entries + \\' entries | Glossary: \\' + data.stats.glossary_terms + \\' terms | Synonyms: \\' + data.stats.synonym_rules + \\' rules"
new_raw = "引擎: \\' + data.engine + \\' | TM: \\' + data.stats.tm_entries + \\'条 | 术语库: \\' + data.stats.glossary_terms + \\'条 | 同义词: \\' + data.stats.synonym_rules + \\'条"

# The actual file content uses escaped single quotes
# Let's find it
marker = "Engine: "
idx = content.find(marker)
if idx >= 0:
    actual = content[idx:idx+200]
    print('Actual text:')
    print(repr(actual))

    # Now replace
    old_actual = actual
    new_actual = "引擎: \\' + data.engine + \\' | TM: \\' + data.stats.tm_entries + \\'条 | 术语库: \\' + data.stats.glossary_terms + \\'条 | 同义词: \\' + data.stats.synonym_rules + \\'条"
    content = content.replace(old_actual, new_actual)
    print('Replaced!')
else:
    print('Not found')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
