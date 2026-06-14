import re

base_path = r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\static\js\app.js'
iife_path = r'C:\Users\15364\.qclaw\workspace-ua58rsb93veqtxl7\cad-translator\settings_iife.js'

with open(base_path, encoding='utf8') as f:
    base = f.read()

with open(iife_path, encoding='utf8') as f:
    iife = f.read()

# Find the boot section
boot = base.rfind('// Boot')

# Build settings panel function
settings_func = '\n\n// ============================================================\n' \
    '// Settings Panel + DXF Flow (migrated from index.html inline script)\n' \
    '// ============================================================\n' \
    'function initSettingsPanel() {\n' + iife + '\n}\n'

combined = base[:boot] + settings_func + base[boot:]

# Update boot to call initSettingsPanel
old_boot = 'document.addEventListener("DOMContentLoaded", () => {\n    Viewer.init("pdf-viewer");\n    App.init();\n});'
new_boot = 'document.addEventListener("DOMContentLoaded", () => {\n    Viewer.init("pdf-viewer");\n    App.init();\n    initSettingsPanel();\n});'
combined = combined.replace(old_boot, new_boot)

with open(base_path, 'w', encoding='utf8') as f:
    f.write(combined)

print(f'Done. Old: {len(base)} -> New: {len(combined)} chars')
