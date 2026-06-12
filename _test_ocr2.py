import fitz, os, sys, json
sys.path.insert(0, r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\backend')

pdf_path = r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\uploads\040d0975234f.pdf'
pdf = fitz.open(pdf_path)
page = pdf[0]
pix = page.get_pixmap(dpi=200)
out_img = r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\_test_page0.png'
pix.save(out_img)

from surya_ocr import run_raster_ocr
result = run_raster_ocr(out_img)

with open(r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\_test_ocr_result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'Done. {result["translatable"]} translatable, {result["total_detected"]} detected')
