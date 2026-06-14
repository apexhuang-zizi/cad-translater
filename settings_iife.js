// Settings panel management
(function() {
    var overlay = document.getElementById('settings-overlay');
    var gearBtn = document.getElementById('btn-open-settings');
    var closeBtn = document.getElementById('btn-close-settings');

    if (!overlay || !gearBtn || !closeBtn) {
        console.error('Settings panel: missing elements', { overlay: !!overlay, gearBtn: !!gearBtn, closeBtn: !!closeBtn });
        return;
    }

    var currentTab = 'engines';
    window.__settingsReady = true;

    gearBtn.addEventListener('click', function() {
        overlay.classList.remove('hidden');
        loadCurrentTab();
    });
    closeBtn.addEventListener('click', function() {
        overlay.classList.add('hidden');
    });
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) overlay.classList.add('hidden');
    });

    // Tab switching
    document.querySelectorAll('.settings-tab').forEach(function(tab) {
        tab.addEventListener('click', function() {
            var target = this.dataset.tab;
            currentTab = target;
            document.querySelectorAll('.settings-tab').forEach(function(t) { t.classList.remove('active'); });
            this.classList.add('active');
            document.querySelectorAll('.settings-tab-content').forEach(function(c) { c.classList.add('hidden'); });
            document.getElementById('tab-' + target).classList.remove('hidden');
            loadCurrentTab();
        });
    });

    // Engine selector in settings
    document.querySelectorAll('#settings-engine-selector .engine-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('#settings-engine-selector .engine-btn').forEach(function(b) { b.classList.remove('active'); });
            this.classList.add('active');
            var engine = this.dataset.engine;
            document.getElementById('settings-api-keys').classList.toggle('hidden', engine === 'google');
        });
    });

    // Test pipeline
    document.getElementById('btn-test-pipeline').addEventListener('click', function() {
        var engine = document.querySelector('#settings-engine-selector .engine-btn.active').dataset.engine;
        var apiKey = document.getElementById('settings-api-key').value;
        var useTM = document.getElementById('chk-use-tm').checked;
        var useGloss = document.getElementById('chk-use-glossary').checked;
        var useSyn = document.getElementById('chk-use-synonyms').checked;
        var resultDiv = document.getElementById('test-pipeline-result');
        resultDiv.innerHTML = '<span class="spinner"></span> Đang kiểm tra...';
        
        fetch('/api/translator/test', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                texts: ['活动层板', '三合一连接件', '侧板钻孔图', '注意安装方向'],
                engine: engine,
                api_key: apiKey,
                use_tm: useTM,
                use_glossary: useGloss,
                use_synonyms: useSyn
            })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.error) { resultDiv.innerHTML = '<span style="color:red">' + data.error + '</span>'; return; }
            var html = '<table style="width:100%;border-collapse:collapse;font-size:0.78rem"><tr><th>原文 / Gốc</th><th>归一化</th><th>译文 / Dịch</th><th>来源</th></tr>';
            data.results.forEach(function(r) {
                var src = r.from_tm ? 'TM' : (r.synonym_applied ? 'Syn+API' : 'API');
                html += '<tr><td>' + r.original + '</td><td>' + (r.normalized || '-') + '</td><td style="color:var(--primary)">' + r.translated + '</td><td>' + src + '</td></tr>';
            });
            html += '</table>';
            html += '<p style="margin-top:8px">引擎: \' + data.engine + \' | TM: \' + data.stats.tm_entries + \'条 | 术语库: \' + data.stats.glossary_terms + \'条 | 同义词: \' + data.stats.synonym_rules + \'条iv.innerHTML = html;
            loadTMStats();
        });
    });

    // Glossary management
    document.getElementById('btn-add-glossary').addEventListener('click', function() {
        var cn = document.getElementById('glossary-cn').value.trim();
        var vi = document.getElementById('glossary-vi').value.trim();
        if (!cn || !vi) return;
        fetch('/api/translator/glossary', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({chinese: cn, vietnamese: vi})
        }).then(function() {
            document.getElementById('glossary-cn').value = '';
            document.getElementById('glossary-vi').value = '';
            loadGlossary();
        });
    });

    function loadGlossary() {
        fetch('/api/translator/glossary').then(function(r) { return r.json(); }).then(function(data) {
            var list = document.getElementById('glossary-list');
            if (!data.glossary || data.glossary.length === 0) {
                list.innerHTML = '<div class="text-muted" style="padding:20px;text-align:center">Chưa có thuật ngữ</div>';
                return;
            }
            list.innerHTML = data.glossary.map(function(item) {
                return '<div class="glossary-row"><span class="cn">' + item.chinese + '</span><span class="arrow">→</span><span class="vi">' + item.vietnamese + '</span><button class="delete-btn" data-cn="' + item.chinese + '">&times;</button></div>';
            }).join('');
            list.querySelectorAll('.delete-btn').forEach(function(btn) {
                btn.addEventListener('click', function() {
                    fetch('/api/translator/glossary/' + encodeURIComponent(this.dataset.cn), {method: 'DELETE'}).then(function() { loadGlossary(); });
                });
            });
        });
    }

    // Synonyms management
    document.getElementById('btn-add-synonym').addEventListener('click', function() {
        var variant = document.getElementById('synonym-variant').value.trim();
        var standard = document.getElementById('synonym-standard').value.trim();
        if (!variant || !standard) return;
        fetch('/api/translator/synonyms', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({variant: variant, standard: standard})
        }).then(function() {
            document.getElementById('synonym-variant').value = '';
            document.getElementById('synonym-standard').value = '';
            loadSynonyms();
        });
    });

    function loadSynonyms() {
        fetch('/api/translator/synonyms').then(function(r) { return r.json(); }).then(function(data) {
            var list = document.getElementById('synonym-list');
            if (!data.synonyms || data.synonyms.length === 0) {
                list.innerHTML = '<div class="text-muted" style="padding:20px;text-align:center">Chưa có quy tắc đồng nghĩa</div>';
                return;
            }
            list.innerHTML = data.synonyms.map(function(item) {
                return '<div class="synonym-row"><span class="cn">' + item.variant + '</span><span class="arrow">→</span><span class="vi">' + item.standard + '</span><button class="delete-btn" data-var="' + item.variant + '">&times;</button></div>';
            }).join('');
            list.querySelectorAll('.delete-btn').forEach(function(btn) {
                btn.addEventListener('click', function() {
                    fetch('/api/translator/synonyms/' + encodeURIComponent(this.dataset.var), {method: 'DELETE'}).then(function() { loadSynonyms(); });
                });
            });
        });
    }

    // TM management
    function loadTMStats() {
        fetch('/api/translator/tm').then(function(r) { return r.json(); }).then(function(data) {
            var s = data.stats;
            document.getElementById('tm-stats-display').innerHTML = '<strong>TM:</strong> ' + s.tm_entries + '条 | <strong>术语库:</strong> ' + s.glossary_terms + '条 | <strong>同义词:</strong> ' + s.synonym_rules + '条';
            document.getElementById('tm-stats-detailed').innerHTML = '<strong>Entries:</strong> ' + s.tm_entries + ' | <strong>Glossary:</strong> ' + s.glossary_terms + ' | <strong>Synonyms:</strong> ' + s.synonym_rules;
            
            var list = document.getElementById('tm-entries');
            if (!data.entries || data.entries.length === 0) {
                list.innerHTML = '<div class="text-muted" style="padding:20px;text-align:center">Chưa có bản dịch nào</div>';
                return;
            }
            list.innerHTML = data.entries.map(function(item) {
                return '<div class="tm-row"><span class="src">' + item.source + '</span><span class="arrow">→</span><span class="dest">' + item.translation + '</span></div>';
            }).join('');
        });
    }

    document.getElementById('btn-export-tm').addEventListener('click', function() {
        window.open('/api/translator/tm/export', '_blank');
    });

    document.getElementById('btn-import-tm').addEventListener('click', function() {
        document.getElementById('tm-import-file').click();
    });

    document.getElementById('tm-import-file').addEventListener('change', function() {
        var file = this.files[0];
        if (!file) return;
        var form = new FormData();
        form.append('file', file);
        fetch('/api/translator/tm/import', {method: 'POST', body: form}).then(function(r) { return r.json(); }).then(function(data) {
            alert('Đã nhập ' + data.imported + ' mục. Tổng cộng: data.total_entries);
            loadTMStats();
        });
    });

    document.getElementById('btn-clear-tm').addEventListener('click', function() {
        if (!confirm('Xóa tất cả bản dịch đã lưu?')) return;
        fetch('/api/translator/tm/clear', {method: 'POST'}).then(function() { loadTMStats(); });
    });

    function loadCurrentTab() {
        if (currentTab === 'glossary') loadGlossary();
        else if (currentTab === 'synonyms') loadSynonyms();
        else if (currentTab === 'tm') loadTMStats();
        else loadTMStats();
    }

    // Init
    loadTMStats();
})();

// ============================================================
// DXF Import Flow
// ============================================================
(function() {
    var currentType = 'pdf';
    var dxfFileId = null;
    var dxfTranslations = [];

    // File type toggle
    document.getElementById('btn-type-pdf').addEventListener('click', function() {
        switchType('pdf');
    });
    document.getElementById('btn-type-dxf').addEventListener('click', function() {
        switchType('dxf');
    });

    function switchType(type) {
        currentType = type;
        document.querySelectorAll('.file-type-btn').forEach(function(b) { b.classList.remove('active'); });
        document.getElementById('btn-type-' + type).classList.add('active');
        document.getElementById('file-input').accept = type === 'dxf' ? '.dxf' : '.pdf';
        document.getElementById('upload-icon').textContent = type === 'dxf' ? 'DXF' : 'PDF';

        if (type === 'dxf') {
            document.getElementById('upload-hint').textContent = '拖放DXF CAD文件或点击选择 / Kéo thả file DXF CAD vào đây';
            document.getElementById('upload-sub').textContent = '点击选择 / Nhấn để chọn | DXF原生提取，无需OCR，100%准确';
        } else {
            document.getElementById('upload-hint').textContent = '拖放PDF图纸或点击选择 / Kéo thả bản vẽ PDF vào đây';
            document.getElementById('upload-sub').textContent = '点击选择 / Nhấn để chọn | 支持CAD矢量&栅格PDF';
        }
    }

    // Intercept file selection for DXF
    document.getElementById('file-input').addEventListener('change', function(e) {
        if (currentType !== 'dxf') return;
        var file = e.target.files[0];
        if (!file) return;

        // Hide PDF flow, show DXF results
        var uploadZone = document.getElementById('upload-zone');
        var uploadStatus = document.getElementById('upload-status');
        var resultsZone = document.getElementById('dxf-results-zone');

        uploadZone.classList.add('hidden');
        uploadStatus.classList.remove('hidden');
        document.getElementById('upload-filename').textContent = '正在提取DXF文字… / Đang trích xuất chữ từ DXF...';

        var form = new FormData();
        form.append('file', file);

        fetch('/api/dxf/upload', { method: 'POST', body: form })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                uploadStatus.classList.add('hidden');
                resultsZone.classList.remove('hidden');

                if (data.error) {
                    document.getElementById('dxf-result-title').textContent = '错误 / Lỗi: ' + data.error;
                    uploadZone.classList.remove('hidden');
                    return;
                }

                dxfFileId = data.file_id;
                document.getElementById('dxf-result-title').textContent =
                    'DXF 提取结果 / Kết quả trích xuất: ' + file.name;

                // Stats
                var stats = document.getElementById('dxf-stats');
                stats.innerHTML =
                    '<div><strong>' + data.total_entities + '</strong><br/><small>文本实体 / Thực thể text</small></div>' +
                    '<div><strong style="color:var(--primary)">' + data.translatable_count + '</strong><br/><small>可翻译 / Có thể dịch</small></div>' +
                    '<div><strong style="color:var(--text-muted)">' + data.skipped_count + '</strong><br/><small>已过滤 / Đã lọc</small></div>' +
                    '<div><strong>' + data.geometry_objects + '</strong><br/><small>几何元素 / Hình học</small></div>' +
                    '<div><small>尺寸 / Kích thước: ' + Math.round(data.bounds.width) + '×' + Math.round(data.bounds.height) + '</small></div>';

                // Entities table
                var ents = document.getElementById('dxf-entities');
                var html = '<table style="width:100%;border-collapse:collapse">';
                html += '<tr><th style="text-align:left;padding:4px">原文 / Gốc</th><th style="text-align:right;padding:4px">位置 / Vị trí</th><th style="text-align:right;padding:4px">字号</th></tr>';
                data.entities.forEach(function(item) {
                    html += '<tr style="border-bottom:1px solid #f0f0f0">';
                    html += '<td style="padding:4px">' + item.text + '</td>';
                    html += '<td style="text-align:right;padding:4px;font-size:0.75rem;color:var(--text-muted)">(' + Math.round(item.insert[0]) + ',' + Math.round(item.insert[1]) + ')</td>';
                    html += '<td style="text-align:right;padding:4px;font-size:0.75rem;color:var(--text-muted)">' + item.height.toFixed(1) + '</td>';
                    html += '</tr>';
                });
                html += '</table>';

                if (data.skipped && data.skipped.length > 0) {
                    html += '<p style="margin-top:8px;font-size:0.75rem;color:var(--text-muted)">已过滤 / Đã lọc: ';
                    html += data.skipped.map(function(s) { return s.text + ' (' + s.reason + ')'; }).join(', ');
                    html += '</p>';
                }
                ents.innerHTML = html;

                // Show translate button
                document.getElementById('btn-dxf-translate').classList.remove('hidden');

                uploadZone.classList.remove('hidden');
            })
            .catch(function(err) {
                uploadStatus.classList.add('hidden');
                uploadZone.classList.remove('hidden');
                alert('DXF upload failed: ' + err.message);
            });
    });

    // DXF Translate button
    document.getElementById('btn-dxf-translate').addEventListener('click', function() {
        if (!dxfFileId) return;
        var engine = document.querySelector('#settings-engine-selector .engine-btn.active');
        var engineName = engine ? engine.dataset.engine : 'google';
        var apiKey = document.getElementById('settings-api-key').value;

        var btn = document.getElementById('btn-dxf-translate');
        btn.textContent = '翻译中… / Đang dịch...';
        btn.disabled = true;

        fetch('/api/dxf/' + dxfFileId + '/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                engine: engineName,
                api_key: apiKey,
                use_tm: document.getElementById('chk-use-tm').checked,
                use_glossary: document.getElementById('chk-use-glossary').checked,
                use_synonyms: document.getElementById('chk-use-synonyms').checked
            })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            btn.textContent = '翻译 / Dịch';
            btn.disabled = false;
            if (data.error) { alert(data.error); return; }

            dxfTranslations = data.items;

            // Show translated results
            var ents = document.getElementById('dxf-entities');
            var html = '<table style="width:100%;border-collapse:collapse">';
            html += '<tr><th style="text-align:left;padding:4px">原文 / Gốc</th><th style="text-align:left;padding:4px;color:var(--primary)">译文 / Dịch</th><th style="text-align:right;padding:4px">来源</th></tr>';
            data.items.forEach(function(item) {
                var src = item.from_tm ? 'TM' : 'API';
                html += '<tr style="border-bottom:1px solid #f0f0f0">';
                html += '<td style="padding:4px">' + item.text + '</td>';
                html += '<td style="padding:4px;color:var(--primary);font-weight:600">' + item.translated + '</td>';
                html += '<td style="text-align:right;padding:4px;font-size:0.7rem;color:var(--text-muted)">' + src + '</td>';
                html += '</tr>';
            });
            html += '</table>';
            html += '<p style="margin-top:8px;font-size:0.78rem">';
            html += '引擎 / Engine: ' + data.engine;
            html += ' | TM命中 / Trúng TM: ' + data.stats.from_tm + '/' + data.stats.total;
            html += '</p>';
            ents.innerHTML = html;

            // Show export button
            document.getElementById('btn-dxf-export').classList.remove('hidden');
        })
        .catch(function(err) {
            btn.textContent = '翻译 / Dịch';
            btn.disabled = false;
            alert('Translation failed: ' + err.message);
        });
    });

    // DXF Export button
    document.getElementById('btn-dxf-export').addEventListener('click', function() {
        if (!dxfFileId || dxfTranslations.length === 0) return;
        var mode = confirm('使用编号标注模式？/ Dùng chế độ đánh số?\n\nOK = 编号标记+对照表 / Đánh số + bảng\nCancel = 直接注释在原文旁 / Chú thích bên cạnh') ? 'numbered' : 'annotated';

        var btn = document.getElementById('btn-dxf-export');
        btn.textContent = '导出中… / Đang xuất...';
        btn.disabled = true;

        fetch('/api/dxf/' + dxfFileId + '/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: mode, translations: dxfTranslations })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            btn.textContent = '导出DXF / Xuất DXF';
            btn.disabled = false;
            if (data.error) { alert(data.error); return; }
            // Trigger download
            window.location.href = data.download_url;
        })
        .catch(function(err) {
            btn.textContent = '导出DXF / Xuất DXF';
            btn.disabled = false;
            alert('Export failed: ' + err.message);
        });
    });
})();
