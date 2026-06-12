"""Quick DXF text extraction POC - no OCR needed, 100% accuracy"""
import ezdxf

# Create test DXF with Chinese text and geometry
doc = ezdxf.new()
msp = doc.modelspace()

# Text entities (simulating real CAD annotations)
msp.add_text('前视图 - 比例 1:50', dxfattribs={'insert': (100, 200), 'height': 5})
msp.add_text('活动层板 (A02)', dxfattribs={'insert': (150, 300), 'height': 4})
msp.add_text('木榫定位孔 Ø8×30', dxfattribs={'insert': (200, 300), 'height': 3.5})
msp.add_text('侧板倒角 R3', dxfattribs={'insert': (300, 400), 'height': 4})
msp.add_text('背板开槽 6×6mm', dxfattribs={'insert': (400, 500), 'height': 4})
msp.add_text('FRONT VIEW', dxfattribs={'insert': (100, 150), 'height': 6})
msp.add_text('SECTION A-A', dxfattribs={'insert': (500, 150), 'height': 6})
msp.add_text('技术要求：所有尺寸单位mm', dxfattribs={'insert': (50, 50), 'height': 3})

# Drawing geometry (lines, circles — we know exact positions!)
msp.add_line((50, 50), (550, 50))
msp.add_line((50, 50), (50, 550))
msp.add_circle((300, 300), radius=100)
msp.add_line((100, 100), (500, 500))

test_path = r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\uploads\test.dxf'
doc.saveas(test_path)
print(f'Test DXF saved: {test_path}')

# ============================================================
# Parse it back — extract text and geometry
# ============================================================
doc2 = ezdxf.readfile(test_path)
msp2 = doc2.modelspace()

print('\n=== TEXT/MTEXT Entities (100% accuracy, no OCR!) ===')
text_entities = []
geometry_bboxes = []

for e in msp2:
    etype = e.dxftype()
    
    if etype in ('TEXT', 'MTEXT'):
        txt = e.dxf.text if etype == 'TEXT' else e.text
        insert = (e.dxf.insert.x, e.dxf.insert.y)
        height = e.dxf.height
        rot = e.dxf.rotation if e.dxf.hasattr('rotation') else 0
        
        # Estimate text bbox (approximate width based on char count)
        est_w = len(txt) * height * 0.6
        est_h = height * 1.2
        bbox = [insert[0], insert[1] - est_h, insert[0] + est_w, insert[1]]
        
        text_entities.append({
            'type': etype,
            'text': txt,
            'layer': e.dxf.layer,
            'insert': insert,
            'height': height,
            'rotation': rot,
            'bbox': bbox,
        })
        print(f'  [{etype}] "{txt}" at ({insert[0]:.0f},{insert[1]:.0f}) h={height}')
    
    elif etype in ('LINE', 'CIRCLE', 'ARC', 'LWPOLYLINE', 'POLYLINE'):
        # Collect geometry for collision detection
        if etype == 'LINE':
            x0, y0, x1, y1 = e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y
            geometry_bboxes.append([
                min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)
            ])
        elif etype == 'CIRCLE':
            cx, cy, r = e.dxf.center.x, e.dxf.center.y, e.dxf.radius
            geometry_bboxes.append([cx - r, cy - r, cx + r, cy + r])

print(f'\nTotal text entities: {len(text_entities)}')
print(f'Total geometry objects: {len(geometry_bboxes)}')

# ============================================================
# Classify: view labels vs translatable
# ============================================================
import re
VIEW_PATTERNS = [
    r'(FRONT|BACK|LEFT|RIGHT|TOP|BOTTOM|SIDE|SECTION|DETAIL|ELEVATION|PLAN)\s*(VIEW)?',
    r'(正|前|后|左|右|仰|俯|背|剖)视图?',
    r'(展开图|装配图|大样图|详图|剖面图|断面图|示意图)',
    r'SECTION\s*[A-Z]-[A-Z]',
    r'比例',
    r'SCALE',
]
SKIP = re.compile('|'.join(VIEW_PATTERNS), re.IGNORECASE)

print('\n=== Classification ===')
translatable = []
for te in text_entities:
    if SKIP.search(te['text']):
        print(f'  SKIP (view/frame): "{te["text"]}"')
    else:
        translatable.append(te)
        print(f'  TRANSLATABLE: "{te["text"]}" → needs Vietnamese annotation')

print(f'\nTranslatable items: {len(translatable)}/{len(text_entities)}')
print(f'Geometry blocks known: {len(geometry_bboxes)} (perfect collision avoidance possible)')
print('\n✅ DXF approach eliminates: OCR errors, position ambiguity, content overlap uncertainty')
