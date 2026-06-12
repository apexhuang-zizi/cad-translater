"""DXF Processor smoke test"""
import sys, os
sys.path.insert(0, r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator')

from backend.dxf_processor import (
    extract_text_entities, extract_geometry_bboxes, classify_entities,
    create_annotated_dxf, create_numbered_annotations_dxf, get_dxf_bounds,
)

test_dxf = r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\uploads\test.dxf'

# 1. Extract text
entities = extract_text_entities(test_dxf)
print(f'Text entities: {len(entities)}')
for e in entities:
    print(f'  "{e["text"]}" at ({e["insert"][0]:.0f},{e["insert"][1]:.0f}) h={e["height"]}')

# 2. Extract geometry
bboxes = extract_geometry_bboxes(test_dxf)
print(f'\nGeometry bboxes: {len(bboxes)}')

# 3. Classify
translatable, skipped = classify_entities(entities)
print(f'\nTranslatable: {len(translatable)}, Skipped: {len(skipped)}')
for s in skipped:
    print(f'  SKIP [{s["reason"]}]: "{s["text"]}"')
for t in translatable:
    print(f'  TRANSLATE: "{t["text"]}"')

# 4. Bounds
bounds = get_dxf_bounds(test_dxf)
print(f'\nDrawing bounds: {bounds["x_min"]:.0f},{bounds["y_min"]:.0f} → {bounds["x_max"]:.0f},{bounds["y_max"]:.0f} ({bounds["width"]:.0f}×{bounds["height"]:.0f})')

# 5. Create annotated DXF
mock_translations = [
    {'text': '活动层板 (A02)', 'translated_text': 'Vách ngăn di động (A02)',
     'bbox': [150, 296, 250, 304], 'height': 4.0},
    {'text': '木榫定位孔 Ø8×30', 'translated_text': 'Lỗ định vị mộng gỗ Ø8×30',
     'bbox': [200, 296, 300, 304], 'height': 3.5},
    {'text': '侧板倒角 R3', 'translated_text': 'Vát cạnh bên R3',
     'bbox': [300, 396, 360, 404], 'height': 4.0},
    {'text': '背板开槽 6×6mm', 'translated_text': 'Rãnh tấm sau 6×6mm',
     'bbox': [400, 496, 460, 504], 'height': 4.0},
    {'text': '技术要求：所有尺寸单位mm', 'translated_text': 'Yêu cầu kỹ thuật: Tất cả kích thước đơn vị mm',
     'bbox': [50, 46, 180, 54], 'height': 3.0},
]

out1 = r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\data\output\test_annotated.dxf'
create_annotated_dxf(test_dxf, mock_translations, out1)
print(f'\nAnnotated DXF saved: {out1}')

# 6. Create numbered annotations DXF
out2 = r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\data\output\test_numbered.dxf'
create_numbered_annotations_dxf(test_dxf, mock_translations, out2)
print(f'Numbered DXF saved: {out2}')

# 7. Verify output — re-read annotated DXF
re_entities = extract_text_entities(out1)
vi_texts = [e for e in re_entities if e['layer'] == 'VI_ANNOTATIONS']
print(f'\nVietnamese annotations in output: {len(vi_texts)}')
for vt in vi_texts:
    print(f'  "{vt["text"]}" at ({vt["insert"][0]:.0f},{vt["insert"][1]:.0f})')

print('\n✅ DXF processor smoke test PASSED')
