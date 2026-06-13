# -*- coding: utf-8 -*-
"""Update JS string literals to Chinese+Vietnamese"""

filepath = 'templates/index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    ('<span class="spinner"></span> Testing...', '<span class="spinner"></span> Đang kiểm tra...'),
    ('No glossary terms</div>', 'Chưa có thuật ngữ</div>'),
    ('No synonym rules</div>', 'Chưa có quy tắc đồng nghĩa</div>'),
    ('No cached translations yet</div>', 'Chưa có bản dịch nào</div>'),
    ('Imported \' + data.imported + \' entries. Total: \' + data.total_entries', 'Đã nhập \' + data.imported + \' mục. Tổng cộng: ' + 'data.total_entries'),
    ('Clear all translation memory entries?', 'Xóa tất cả bản dịch đã lưu?'),
    ('<tr><th>Original</th><th>Normalized</th><th>Translated</th><th>Source</th></tr>', '<tr><th>原文 / Gốc</th><th>归一化</th><th>译文 / Dịch</th><th>来源</th></tr>'),
]

count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        count += 1
        print(f'  Replaced: {old[:50]}...')
    else:
        print(f'  NOT FOUND: {old[:50]}...')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\nDone. {count} replacements applied.')
