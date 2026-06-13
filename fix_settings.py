# -*- coding: utf-8 -*-
"""Rewrite the settings panel in index.html"""

html = """<!-- Translator v2 Settings Panel -->
<div id="settings-overlay" class="hidden">
<div class="settings-modal">
<div class="settings-header">
<h2>翻译设置 / Cài đặt phiên dịch</h2>
<button id="btn-close-settings" class="btn-close-settings">&times;</button>
</div>
<div class="settings-body">
<div class="settings-tabs">
<button class="settings-tab active" data-tab="engines">引擎 / Động cơ</button>
<button class="settings-tab" data-tab="glossary">术语库 / Thuật ngữ</button>
<button class="settings-tab" data-tab="synonyms">同义词 / Đồng nghĩa</button>
<button class="settings-tab" data-tab="tm">翻译记忆 / Bộ nhớ dịch</button>
</div>

<!-- Translation Tab -->
<div id="tab-engines" class="settings-tab-content active">
<div class="section-block">
<h4 class="section-title">🔧 翻译引擎 / Động cơ dịch</h4>
<div class="engine-selector" id="settings-engine-selector">
<div class="engine-btn active" data-engine="google">Google 翻译</div>
<div class="engine-btn" data-engine="deepseek">DeepSeek AI</div>
<div class="engine-btn" data-engine="gemini">Gemini AI</div>
</div>
<div id="settings-api-keys" class="hidden section-block">
<label style="font-size:0.85rem;font-weight:500;display:block;margin-bottom:6px">API 密钥 / Khóa API:</label>
<div style="display:flex;gap:8px">
<input type="password" id="settings-api-key" placeholder="sk-... hoặc AIza..." style="flex:1;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:0.9rem">
<button class="btn btn-sm btn-outline" id="btn-settings-test-key">测试</button>
</div>
</div>
</div>

<div class="section-divider"></div>

<div class="section-block">
<h4 class="section-title">⚙ 处理选项 / Tùy chọn xử lý</h4>
<label style="display:flex;align-items:center;gap:10px;margin:10px 0;padding:8px 0">
<input type="checkbox" id="chk-use-tm" checked>
<span style="font-size:0.9rem">翻译记忆缓存 / Bộ nhớ dịch</span>
</label>
<label style="display:flex;align-items:center;gap:10px;margin:10px 0;padding:8px 0">
<input type="checkbox" id="chk-use-glossary" checked>
<span style="font-size:0.9rem">企业术语库锁定 / Khóa thuật ngữ</span>
</label>
<label style="display:flex;align-items:center;gap:10px;margin:10px 0;padding:8px 0">
<input type="checkbox" id="chk-use-synonyms" checked>
<span style="font-size:0.9rem">同义词归一化 / Chuẩn hóa đồng nghĩa</span>
</label>
</div>

<div class="section-divider"></div>

<div class="section-block">
<button class="btn btn-outline" id="btn-test-pipeline">🧪 测试管线 / Kiểm tra pipeline</button>
<div id="test-pipeline-result" style="margin-top:14px;font-size:0.8rem;max-height:200px;overflow:auto"></div>
<div id="tm-stats-display" style="margin-top:10px;font-size:0.82rem;color:var(--text-muted)"></div>
</div>
</div>

<!-- Glossary Tab -->
<div id="tab-glossary" class="settings-tab-content hidden">
<div class="section-block">
<h4 class="section-title">📖 企业术语库 / Thuật ngữ chuyên ngành</h4>
<p style="font-size:0.82rem;color:var(--text-muted);margin:4px 0 12px">锁定固定翻译，避免同一术语被译成不同版本</p>
<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
<input id="glossary-cn" placeholder="中文术语" style="flex:1;min-width:120px;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:0.9rem">
<input id="glossary-vi" placeholder="越南语翻译" style="flex:1;min-width:160px;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:0.9rem">
<button class="btn btn-sm btn-primary" id="btn-add-glossary">添加</button>
</div>
<div id="glossary-list" style="max-height:320px;overflow:auto"></div>
</div>
</div>

<!-- Synonyms Tab -->
<div id="tab-synonyms" class="settings-tab-content hidden">
<div class="section-block">
<h4 class="section-title">🔄 同义词归一化 / Chuẩn hóa đồng nghĩa</h4>
<p style="font-size:0.82rem;color:var(--text-muted);margin:4px 0 12px">将变体词映射为标准词（如：活动层板 → 层板），减少 API 调用</p>
<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
<input id="synonym-variant" placeholder="变体词（例：活动层板）" style="flex:1;min-width:120px;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:0.9rem">
<input id="synonym-standard" placeholder="标准词（例：层板）" style="flex:1;min-width:120px;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:0.9rem">
<button class="btn btn-sm btn-primary" id="btn-add-synonym">添加</button>
</div>
<div id="synonym-list" style="max-height:320px;overflow:auto"></div>
</div>
</div>

<!-- TM Tab -->
<div id="tab-tm" class="settings-tab-content hidden">
<div class="section-block">
<h4 class="section-title">💾 翻译记忆 / Bộ nhớ dịch</h4>
<div id="tm-stats-detailed" style="margin:10px 0;padding:10px 14px;background:#f0f7ff;border-radius:6px;font-size:0.85rem"></div>
<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
<button class="btn btn-outline btn-sm" id="btn-export-tm">📤 导出 TM</button>
<button class="btn btn-outline btn-sm" id="btn-import-tm">📥 导入 TM</button>
<button class="btn btn-outline btn-sm" id="btn-clear-tm" style="color:var(--danger);border-color:var(--danger)">🗑 清空全部</button>
<input type="file" id="tm-import-file" accept=".json" style="display:none">
</div>
<div id="tm-entries" style="max-height:320px;overflow:auto"></div>
</div>
</div>
</div>
</div>
</div>

<!-- Settings gear button -->
<button id="btn-open-settings" class="btn btn-sm btn-outline" style="position:fixed;top:60px;right:16px;z-index:100;padding:6px 10px;font-size:1rem;" title="翻译设置">⚙</button>

<style>
#settings-overlay {
    position:fixed;top:0;left:0;width:100%;height:100%;
    background:rgba(0,0,0,0.5);z-index:200;
    display:flex;justify-content:center;align-items:center;
}
.settings-modal {
    background:#fff;border-radius:10px;
    width:92%;max-width:720px;max-height:82vh;overflow:hidden;
    display:flex;flex-direction:column;
    box-shadow:0 8px 32px rgba(0,0,0,0.25);
}
.settings-header {
    display:flex;justify-content:space-between;align-items:center;
    padding:18px 24px;
    background:linear-gradient(135deg,#f8fafc,#eff6ff);
    border-bottom:1px solid var(--border);
}
.settings-header h2 { margin:0;font-size:1.15rem;color:var(--text); }
.btn-close-settings {
    background:none;border:none;font-size:1.5rem;cursor:pointer;
    color:var(--text-muted);padding:4px 8px;border-radius:4px;
}
.btn-close-settings:hover { background:#f0f0f0;color:#333; }
.settings-body { display:flex;flex-direction:column;overflow-y:auto; }
.settings-tabs {
    display:flex;border-bottom:2px solid var(--border);
    padding:0 8px;background:#fafbfc;
}
.settings-tab {
    padding:12px 18px;border:none;background:none;cursor:pointer;
    font-size:0.88rem;color:var(--text-muted);border-bottom:2px solid transparent;
    margin-bottom:-2px;transition:all 0.15s;
}
.settings-tab:hover { color:var(--text); }
.settings-tab.active {
    border-bottom-color:var(--primary);color:var(--primary);font-weight:600;
}
.settings-tab-content { padding:20px 24px;flex:1; }
.settings-tab-content.hidden { display:none; }

/* Section blocks with clear visual separation */
.section-block {
    padding:16px 18px;
    background:#fafbfc;border:1px solid #e8ecf0;border-radius:8px;
    margin-bottom:14px;
}
.section-block:last-child { margin-bottom:0; }
.section-title {
    font-size:0.92rem;font-weight:600;color:var(--text);margin:0 0 12px 0;
}
.section-divider {
    height:1px;background:linear-gradient(90deg,transparent,#e2e8f0,transparent);
    margin:16px 0;
}

/* List rows */
.glossary-row, .synonym-row, .tm-row {
    display:flex;justify-content:space-between;align-items:center;
    padding:10px 0;border-bottom:1px solid #f0f0f0;
    gap:10px;
}
.glossary-row:last-child, .synonym-row:last-child, .tm-row:last-child {
    border-bottom:none;
}
.glossary-row .cn, .synonym-row .cn {
    font-weight:600;color:#333;flex:1;min-width:80px;
}
.glossary-row .arrow, .synonym-row .arrow {
    color:#999;font-size:0.85rem;flex-shrink:0;
}
.glossary-row .vi, .synonym-row .vi {
    color:var(--primary);flex:2;min-width:100px;
}
.tm-row .src { color:#333;flex:1.5;font-size:0.82rem;word-break:break-word; }
.tm-row .dest { color:var(--primary);flex:2;font-size:0.82rem;word-break:break-word; }
.delete-btn {
    color:#dc3545;background:none;border:none;cursor:pointer;
    font-size:1.1rem;padding:4px 8px;border-radius:4px;flex-shrink:0;
}
.delete-btn:hover { background:#fef2f2; }

/* Stats */
.tm-stats { padding:10px 14px;background:#f0f7ff;border-radius:6px;font-size:0.82rem;color:var(--text-muted); }

/* Empty state */
.text-muted { color:var(--text-muted); }
</style>"""

import os
filepath = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '<!-- Translator v2 Settings Panel -->'
end_marker = '<!-- Settings gear button in header -->'
start_idx = content.index(start_marker)
end_idx = content.index(end_marker)

new_content = content[:start_idx] + html + content[end_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Settings panel rewritten successfully')
print(f'Length before: {len(content)}, after: {len(new_content)}')
