import fitz, os, sys
sys.path.insert(0, r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\backend')

pdf_path = r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\uploads\040d0975234f.pdf'

pdf = fitz.open(pdf_path)
print(f'Pages: {pdf.page_count}')

# Render first page
page = pdf[0]
pix = page.get_pixmap(dpi=200)
out_img = r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\_test_page0.png'
pix.save(out_img)
print(f'Rendered: {out_img} ({pix.width}x{pix.height})')

# Now test the full OCR pipeline
from surya_ocr import run_raster_ocr
result = run_raster_ocr(out_img)
print(f'\n=== OCR RESULTS ===')
print(f'Detected:  {result["total_detected"]}')
print(f'OCR done:  {result["ocr_results"]}')
print(f'Translatable: {result["translatable"]}')
print(f'\nTranslatable items:')
for item in result.get('items', []):
    print(f'  [{item["idx"]}] "{item["text"]}" @ {item["bbox"]}')

# Also show what was in raw but filtered out (garbled)
raw_texts = {r['idx']: r['text'] for r in result.get('raw_items', [])}
trans_idx = {t['idx'] for t in result.get('items', [])}
filtered_out = [(i, t) for i, t in raw_texts.items() if i not in trans_idx]
if filtered_out:
    print(f'\nFiltered out ({len(filtered_out)} items):')
    for i, t in filtered_out[:15]:
        print(f'  [{i}] "{t}"')
