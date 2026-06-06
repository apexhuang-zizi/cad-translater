/**
 * CAD Translator - Main Application Logic
 * Hybrid Architecture: Vector | AI Vision | Template | Manual
 */
const App = {
    // State
    fileId: null,
    filename: null,
    pageCount: 0,
    pagesWithText: [],
    currentPageIdx: 0,
    currentPage: 0,
    scanResults: [],
    items: [],
    engine: "google",
    apiKey: "",
    step: 0,
    manualMode: false,
    manualItems: [],

    async init() {
        this.bindEvents();
        this.showStep(0);
        await this.loadEngineConfig();
    },

    bindEvents() {
        // Upload
        const dropZone = document.getElementById("upload-zone");
        const fileInput = document.getElementById("file-input");

        dropZone.addEventListener("click", () => fileInput.click());
        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("drag-over");
        });
        dropZone.addEventListener("dragleave", () => {
            dropZone.classList.remove("drag-over");
        });
        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("drag-over");
            const file = e.dataTransfer.files[0];
            if (file) this.handleUpload(file);
        });
        fileInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (file) this.handleUpload(file);
        });

        // Review actions
        document.getElementById("btn-prev-page").addEventListener("click", () => this.goToPrevPage());
        document.getElementById("btn-next-page").addEventListener("click", () => this.goToNextPage());
        document.getElementById("btn-confirm-page").addEventListener("click", () => this.confirmCurrentPage());
        document.getElementById("btn-save-all").addEventListener("click", () => this.finalizeAll());
        document.getElementById("btn-translate").addEventListener("click", () => this.translateCurrentPage());
        document.getElementById("btn-overlay").addEventListener("click", () => this.overlayCurrentPage());

        // Manual calibration
        document.getElementById("btn-manual-mode").addEventListener("click", () => this.toggleManualMode());
        document.getElementById("btn-manual-done").addEventListener("click", () => this.toggleManualMode());
        document.getElementById("btn-manual-clear").addEventListener("click", () => this.clearManualItems());

        // Template save
        document.getElementById("btn-template-save").addEventListener("click", () => this.showTemplateDialog());
        document.getElementById("btn-template-save-confirm").addEventListener("click", () => this.saveTemplate());
        document.getElementById("btn-template-cancel").addEventListener("click", () => this.hideTemplateDialog());

        // Engine settings
        document.querySelectorAll(".engine-btn").forEach(btn => {
            btn.addEventListener("click", () => this.selectEngine(btn.dataset.engine));
        });
        document.getElementById("btn-test-key").addEventListener("click", () => this.testApiKey());

        // Maximize / Restore preview
        document.getElementById("btn-maximize").addEventListener("click", () => this.toggleMaximize());
    },

    // === Navigation ===

    showStep(n) {
        this.step = n;
        document.querySelectorAll(".phase").forEach(el => el.classList.add("hidden"));

        const phases = ["phase-upload", "phase-scan", "phase-review", "phase-done"];
        for (let i = 0; i < phases.length; i++) {
            const el = document.getElementById(phases[i]);
            if (el) el.classList.toggle("hidden", i !== n);
        }

        document.querySelectorAll(".step").forEach((el, i) => {
            el.classList.remove("active", "done");
            if (i < n) el.classList.add("done");
            if (i === n) el.classList.add("active");
        });
    },

    // === Upload ===

    async handleUpload(file) {
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            this.toast("请选择PDF文件 / Vui lòng chọn file PDF", "error");
            return;
        }

        this.filename = file.name;
        document.getElementById("upload-filename").textContent = `上传中… / Đang tải lên: ${file.name}...`;
        document.getElementById("upload-zone").classList.add("hidden");
        document.getElementById("upload-status").classList.remove("hidden");

        const formData = new FormData();
        formData.append("file", file);

        try {
            const result = await API.upload(formData);
            this.fileId = result.file_id;
            this.pageCount = result.page_count;
            this.filename = result.filename;
            this.toast(`已上传 / Uploaded: ${result.filename} (${result.page_count}页/trang)`, "success");
            await this.startScan();
        } catch (err) {
            this.toast(err.message, "error");
            document.getElementById("upload-zone").classList.remove("hidden");
            document.getElementById("upload-status").classList.add("hidden");
        }
    },

    // === Scan ===

    async startScan() {
        document.getElementById("scan-status").textContent = "Đang quét trang...";
        this.showStep(1);

        try {
            const result = await API.scan(this.fileId);
            this.scanResults = result.scan_results;
            this.pagesWithText = result.page_list;

            document.getElementById("scan-total-pages").textContent = result.total_pages;
            document.getElementById("scan-text-pages").textContent = result.pages_with_text;
            document.getElementById("scan-status").textContent =
                `找到 ${result.pages_with_text} 页有注释需翻译 / Tìm thấy ${result.pages_with_text} trang có chú thích`;

            this.renderPageThumbs();

            document.getElementById("btn-scan-next").classList.toggle(
                "hidden", result.pages_with_text === 0
            );

            if (result.pages_with_text === 0) {
                document.getElementById("scan-result-msg").textContent =
                    "没有找到可翻译的注释 / Không tìm thấy chú thích để dịch.";
                document.getElementById("scan-result-msg").classList.remove("hidden");
            }
        } catch (err) {
            this.toast(err.message, "error");
        }
    },

    renderPageThumbs() {
        const grid = document.getElementById("page-thumb-grid");
        grid.innerHTML = "";

        for (let i = 0; i < this.pageCount; i++) {
            const div = document.createElement("div");
            div.className = "page-thumb";
            if (this.pagesWithText.includes(i)) div.classList.add("has-text");
            
            const scanResult = this.scanResults[i] || {};
            const typeLabel = scanResult.type === "vector" ? "矢量 / Vector" : 
                              scanResult.has_template ? "有模板 / Có mẫu" : "栅格 / Raster";
            
            div.innerHTML = `
                <div style="font-weight:600">${i + 1}</div>
                <div style="font-size:0.7rem;color:var(--text-muted)">
                    ${this.pagesWithText.includes(i) ? "有字 / có chữ" : "空白 / trống"}
                </div>
                <div style="font-size:0.6rem;color:var(--primary)">${typeLabel}</div>
            `;
            if (this.pagesWithText.includes(i)) {
                div.addEventListener("click", () => this.startReview(i));
            }
            grid.appendChild(div);
        }
    },

    // === Review ===

    async startReview(pageNum) {
        this.currentPage = pageNum;
        this.currentPageIdx = this.pagesWithText.indexOf(pageNum);

        this.showStep(2);
        document.getElementById("review-filename").textContent = this.filename;
        this.updatePageIndicator();

        // Hide fallback notice
        document.getElementById("fallback-notice").classList.add("hidden");

        // Load page preview
        const previewUrl = API.getPagePreviewUrl(this.fileId, pageNum);
        await Viewer.loadPage(previewUrl);

        // Extract text items
        try {
            const data = await API.extractPage(this.fileId, pageNum);

            if (data.type === "raster" && data.needs_ocr) {
                this.toast("栅格页面 - 正在运行智能提取… / Đang trích xuất thông minh…", "info");
                const ocrData = await API.ocrPage(this.fileId, pageNum, { use_ai: true });
                this.handleOcrResult(ocrData);
            } else {
                this.items = data.items.map((item, i) => ({
                    ...item,
                    item_index: i,
                    original: item.text,
                    translated: "",
                    status: "pending",
                }));
                this.renderReviewItems();
                Viewer.setItems(this.items, data.frame_zone || null);
                document.getElementById("btn-translate").disabled = this.items.length === 0;
                this.toast(`已提取 ${this.items.length} 条注释 / Đã trích xuất ${this.items.length} mục`, "info");
            }
        } catch (err) {
            this.toast(err.message, "error");
        }

        Viewer.onBoxUpdate = (idx, item) => {
            this.items[idx].placed_bbox = item.placed_bbox;
        };

        this.updateNavButtons();
    },

    handleOcrResult(ocrData) {
        const items = ocrData.items || [];
        
        if (items.length === 0 || ocrData.needs_manual) {
            // Show fallback notice
            const notice = document.getElementById("fallback-notice");
            notice.classList.remove("hidden");
            document.getElementById("fallback-title").textContent = 
                ocrData.warning || "OCR未检测到文字 / OCR không phát hiện được chữ";
            document.getElementById("fallback-msg").textContent = 
                "请使用手动标定模式点击图纸添加注释 / Vui lòng dùng chế độ đánh dấu thủ công";
            
            this.items = [];
            this.toast(
                "自动提取失败。请使用手动标定模式。 / Trích xuất tự động thất bại. Vui lòng dùng chế độ thủ công.",
                "error"
            );
        } else {
            this.items = items.map((item, i) => ({
                ...item,
                item_index: i,
                original: item.text,
                translated: "",
                status: item.status || "pending",
            }));
            
            if (ocrData.warning) {
                this.toast(ocrData.warning, "info");
            }
        }

        this.renderReviewItems();
        Viewer.setItems(this.items, ocrData.frame_zone || null);
        document.getElementById("btn-translate").disabled = this.items.length === 0;
    },

    // === Manual Calibration ===

    toggleManualMode() {
        this.manualMode = !this.manualMode;
        const toolbar = document.getElementById("manual-toolbar");
        const btn = document.getElementById("btn-manual-mode");
        
        if (this.manualMode) {
            toolbar.classList.remove("hidden");
            btn.classList.add("active");
            btn.textContent = "退出手动 / Thoát thủ công";
            this.toast("点击图纸添加注释 / Nhấn vào bản vẽ để thêm chú thích", "info");
            
            // Add click handler to canvas
            Viewer.canvas.addEventListener("click", this.onCanvasClick);
        } else {
            toolbar.classList.add("hidden");
            btn.classList.remove("active");
            btn.textContent = "+ 手动标定 / Đánh dấu thủ công";
            Viewer.canvas.removeEventListener("click", this.onCanvasClick);
        }
    },

    onCanvasClick(e) {
        if (!App.manualMode) return;
        
        const rect = Viewer.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Convert to PDF coordinates
        const pdfPos = Viewer.canvasToPdf(x, y);
        
        // Prompt for text
        const text = prompt("输入注释文字 / Nhập chú thích:", "");
        if (!text || !text.trim()) return;
        
        // Create item
        const newItem = {
            item_index: App.items.length,
            text: text.trim(),
            original: text.trim(),
            bbox: [pdfPos.x, pdfPos.y, pdfPos.x + 100, pdfPos.y + 20],
            translated: "",
            status: "manual",
            needs_review: true,
            confidence: 1.0,
        };
        
        App.items.push(newItem);
        App.renderReviewItems();
        Viewer.setItems(App.items, null);
        
        // Send to backend
        API.manualAdd(App.fileId, App.currentPage, text.trim(), newItem.bbox).catch(err => {
            console.error("Failed to save manual item:", err);
        });
    },

    clearManualItems() {
        if (!confirm("清空所有手动标定? / Xóa hết đánh dấu thủ công?")) return;
        
        this.items = this.items.filter(item => item.status !== "manual");
        this.renderReviewItems();
        Viewer.setItems(this.items, null);
        
        API.manualClear(this.fileId, this.currentPage).catch(err => {
            console.error("Failed to clear manual items:", err);
        });
    },

    // === Template Management ===

    showTemplateDialog() {
        if (this.items.length === 0) {
            this.toast("没有可保存的注释 / Không có chú thích để lưu", "error");
            return;
        }
        document.getElementById("template-dialog").classList.remove("hidden");
    },

    hideTemplateDialog() {
        document.getElementById("template-dialog").classList.add("hidden");
    },

    async saveTemplate() {
        const name = document.getElementById("template-name").value.trim();
        const type = document.getElementById("template-type").value.trim();
        
        if (!name) {
            this.toast("请输入模板名称 / Vui lòng nhập tên mẫu", "error");
            return;
        }
        
        // Get page dimensions
        const previewUrl = API.getPagePreviewUrl(this.fileId, this.currentPage);
        const img = new Image();
        img.src = previewUrl;
        await new Promise(resolve => { img.onload = resolve; });
        
        const pageWidth = img.width / Viewer.scale;
        const pageHeight = img.height / Viewer.scale;
        
        const templateItems = this.items.map(item => ({
            original_text: item.original || item.text,
            bbox: item.bbox,
            font_size: item.font_size || 14,
            placed_bbox: item.placed_bbox,
        }));
        
        try {
            const result = await API.saveTemplate({
                name,
                items: templateItems,
                description: `Template from ${this.filename} page ${this.currentPage + 1}`,
                drawing_type: type || "generic",
                page_width: pageWidth,
                page_height: pageHeight,
            });
            
            this.toast(`模板已保存 / Mẫu đã lưu: ${result.name}`, "success");
            this.hideTemplateDialog();
        } catch (err) {
            this.toast(err.message, "error");
        }
    },

    // === Review Items ===

    renderReviewItems() {
        const container = document.getElementById("review-items");
        container.innerHTML = "";

        if (this.items.length === 0) {
            container.innerHTML = `
                <p style="color:var(--text-muted);text-align:center">
                    此页无注释 / Không có chú thích để dịch<br>
                    <small>使用手动标定模式添加 / Dùng chế độ thủ công để thêm</small>
                </p>`;
            return;
        }

        this.items.forEach((item, idx) => {
            const div = document.createElement("div");
            div.className = "review-item";
            div.id = `review-item-${idx}`;

            const translated = item.confirmed_translation || item.translated || "";
            const text = item.text || item.original || "";
            const fontSize = item.font_size || 14;
            const isManual = item.status === "manual";
            const isTemplate = item.status === "template_applied";

            div.innerHTML = `
                <div class="original">
                    [${idx + 1}] ${text}
                    ${isManual ? '<span class="badge manual">手动 / Thủ công</span>' : ''}
                    ${isTemplate ? '<span class="badge template">模板 / Mẫu</span>' : ''}
                </div>
                <input type="text" class="translation-input" id="input-${idx}"
                       value="${this.escapeHtml(translated)}"
                       placeholder="Translation...">
                <div class="font-size-row">
                    <label>字号 / Cỡ chữ: <input type="range" class="font-size-slider" id="fsize-${idx}"
                           min="8" max="42" value="${fontSize}"
                           oninput="App.updateFontSize(${idx}, this.value)"></label>
                    <span class="font-size-val" id="fsize-val-${idx}">${fontSize}pt</span>
                </div>
                <div class="item-meta">
                    bbox: [${(item.bbox||[]).map(v => Math.round(v)).join(", ")}]
                    ${item.confidence ? `| 置信度 / Độ tin: ${(item.confidence * 100).toFixed(0)}%` : ''}
                </div>
                <div class="item-actions btn-group">
                    <button class="btn btn-sm btn-outline" onclick="App.confirmItem(${idx})">确认 / Xác nhận</button>
                    <button class="btn btn-sm btn-outline" onclick="App.skipItem(${idx})">跳过 / Bỏ qua</button>
                </div>
            `;

            if (item.status === "confirmed") div.classList.add("confirmed");

            div.addEventListener("click", () => {
                document.querySelectorAll(".review-item").forEach(el => el.classList.remove("selected"));
                div.classList.add("selected");
                Viewer.selectBox(idx);
            });

            const input = div.querySelector("input");
            input.addEventListener("input", () => {
                item.confirmed_translation = input.value;
            });
            input.addEventListener("blur", () => {
                item.confirmed_translation = input.value;
                Viewer.updateBoxText(idx, input.value);
            });

            container.appendChild(div);
        });

        const firstItem = container.querySelector(".review-item");
        if (firstItem) firstItem.click();
    },

    escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    },

    confirmItem(idx) {
        if (idx >= 0 && idx < this.items.length) {
            const input = document.getElementById(`input-${idx}`);
            if (input) {
                this.items[idx].confirmed_translation = input.value;
            }
            this.items[idx].status = "confirmed";
            Viewer.markConfirmed(idx);

            const el = document.getElementById(`review-item-${idx}`);
            if (el) el.classList.add("confirmed");

            this.toast(`第 ${idx + 1} 条已确认 / Mục ${idx + 1} đã xác nhận`, "success");
        }
    },

    skipItem(idx) {
        if (idx >= 0 && idx < this.items.length) {
            this.items[idx].status = "skipped";
            const el = document.getElementById(`review-item-${idx}`);
            if (el) el.style.opacity = "0.4";
        }
    },

    updateFontSize(idx, value) {
        if (idx >= 0 && idx < this.items.length) {
            this.items[idx].font_size = parseInt(value);
            const valEl = document.getElementById(`fsize-val-${idx}`);
            if (valEl) valEl.textContent = value + "pt";
        }
    },

    // === Translation ===

    async translateCurrentPage() {
        const engine = this.engine;
        const apiKey = this.getApiKey();
        const texts = this.items.filter(i => i.status !== "skipped").map(i => i.text || i.original);

        if (texts.length === 0) {
            this.toast("无内容可翻译 / Không có mục nào để dịch", "error");
            return;
        }

        document.getElementById("btn-translate").disabled = true;
        document.getElementById("btn-translate").innerHTML = '<span class="spinner"></span> 翻译中… / Đang dịch...';

        try {
            const result = await API.translatePage(
                this.fileId, this.currentPage, engine,
                this.items.filter(i => i.status !== "skipped"),
                apiKey
            );

            result.items.forEach((item, i) => {
                const realIdx = this.items.findIndex(
                    it => (it.text || it.original) === item.original && it.status !== "skipped"
                );
                if (realIdx >= 0) {
                    this.items[realIdx].translated = item.translated;
                    this.items[realIdx].confirmed_translation = item.translated;
                }
            });

            this.renderReviewItems();
            Viewer.setItems(this.items, null);
            Viewer.renderBoxes();

            this.toast(`已用 ${engine} 翻译 ${result.items.length} 条 / Đã dịch`, "success");
        } catch (err) {
            this.toast(err.message, "error");
        } finally {
            document.getElementById("btn-translate").disabled = false;
            document.getElementById("btn-translate").textContent = "翻译 / Dịch";
        }
    },

    async overlayCurrentPage() {
        document.getElementById("btn-overlay").disabled = true;
        document.getElementById("btn-overlay").textContent = "生成中… / Đang tạo...";

        try {
            const result = await API.overlayPage(this.fileId, this.currentPage, this.items);

            const overlayUrl = API.getOverlayPreviewUrl(this.fileId, this.currentPage);
            await Viewer.loadPage(overlayUrl);

            if (result.items) {
                result.items.forEach((item, i) => {
                    if (i < this.items.length && item.placed_bbox) {
                        this.items[i].placed_bbox = item.placed_bbox;
                    }
                });
            }

            this.toast("预览已生成 / Đã tạo bản xem trước", "success");
        } catch (err) {
            this.toast(err.message, "error");
        } finally {
            document.getElementById("btn-overlay").disabled = false;
            document.getElementById("btn-overlay").textContent = "预览 / Xem trước";
        }
    },

    async confirmCurrentPage() {
        const btn = document.getElementById("btn-confirm-page");
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> 应用翻译… / Đang áp dụng...';

        try {
            const result = await API.confirmPage(this.fileId, this.currentPage, this.items);

            if (result.overlay_applied && result.preview_url) {
                const overlayUrl = API.getOverlayPreviewUrl(this.fileId, this.currentPage);
                await Viewer.loadPage(overlayUrl);
                Viewer.setItems(this.items, null);
                Viewer.renderBoxes();

                this.toast(
                    `第 ${this.currentPage + 1} 页已确认 — ${result.items_saved} 条译文已插入 / Trang ${this.currentPage + 1} đã xác nhận — ${result.items_saved} bản dịch đã chèn`,
                    "success"
                );
            } else {
                this.toast(`第 ${this.currentPage + 1} 页已确认 / Trang ${this.currentPage + 1} đã xác nhận`, "success");
            }

            await new Promise(r => setTimeout(r, 1200));
            this.goToNextPage();
        } catch (err) {
            this.toast(err.message, "error");
        } finally {
            btn.disabled = false;
            btn.textContent = "确认&继续 / Xác nhận & Tiếp";
        }
    },

    // === Page Navigation ===

    goToPrevPage() {
        if (this.currentPageIdx > 0) {
            this.currentPageIdx--;
            this.currentPage = this.pagesWithText[this.currentPageIdx];
            this.startReview(this.currentPage);
        }
    },

    goToNextPage() {
        if (this.currentPageIdx < this.pagesWithText.length - 1) {
            this.currentPageIdx++;
            this.currentPage = this.pagesWithText[this.currentPageIdx];
            this.startReview(this.currentPage);
        }
    },

    updateNavButtons() {
        document.getElementById("btn-prev-page").disabled = this.currentPageIdx <= 0;
        document.getElementById("btn-next-page").disabled =
            this.currentPageIdx >= this.pagesWithText.length - 1;
        document.getElementById("btn-save-all").classList.remove("hidden");
    },

    updatePageIndicator() {
        document.getElementById("page-indicator").textContent =
            `第 ${this.currentPage + 1}/${this.pageCount} 页 (含注释 ${this.currentPageIdx + 1}/${this.pagesWithText.length}) | Trang ${this.currentPage + 1} / ${this.pageCount} (chú thích ${this.currentPageIdx + 1}/${this.pagesWithText.length})`;
    },

    // === Finalize ===

    async finalizeAll() {
        document.getElementById("btn-save-all").disabled = true;
        document.getElementById("btn-save-all").innerHTML = '<span class="spinner"></span> 生成中… / Đang tạo...';

        try {
            const result = await API.finalize(this.fileId);

            this.showStep(3);
            document.getElementById("done-filename").textContent = result.output_filename;

            const downloadLink = document.getElementById("done-download");
            downloadLink.href = API.getDownloadUrl(this.fileId);
            downloadLink.download = result.output_filename;

            this.toast(`PDF已保存 / PDF saved: ${result.output_filename}`, "success");
        } catch (err) {
            this.toast(err.message, "error");
        } finally {
            document.getElementById("btn-save-all").disabled = false;
            document.getElementById("btn-save-all").textContent = "全部保存 / Lưu tất cả";
        }
    },

    // === Engine Settings ===

    async loadEngineConfig() {
        try {
            const config = await API.getEngineConfig();
            this.engine = config.current_engine || "google";
            const saved = JSON.parse(localStorage.getItem("cad_translator_keys") || "{}");
            document.getElementById("deepseek-key").value = saved.deepseek || "";
            document.getElementById("gemini-key").value = saved.gemini || "";
            this.updateEngineUI();
        } catch (e) {
            // Backend might not be running yet
        }
    },

    selectEngine(engine) {
        this.engine = engine;
        document.querySelectorAll(".engine-btn").forEach(b => {
            b.classList.toggle("active", b.dataset.engine === engine);
        });
        document.getElementById("api-key-section").classList.toggle(
            "hidden", engine === "google"
        );
        document.getElementById("api-key-label").textContent =
            engine === "deepseek" ? "DeepSeek API Key:" :
            engine === "gemini" ? "Gemini API Key:" : "";
        this.updateEngineUI();
    },

    updateEngineUI() {
        document.querySelectorAll(".engine-btn").forEach(b => {
            b.classList.toggle("active", b.dataset.engine === this.engine);
        });
        document.getElementById("api-key-section").classList.toggle(
            "hidden", this.engine === "google"
        );
    },

    getApiKey() {
        if (this.engine === "deepseek") {
            return document.getElementById("deepseek-key").value.trim();
        } else if (this.engine === "gemini") {
            return document.getElementById("gemini-key").value.trim();
        }
        return "";
    },

    async testApiKey() {
        const engine = this.engine;
        const apiKey = this.getApiKey();

        if (engine === "google") {
            this.toast("Google 翻译始终可用 / Google Translate is always available", "info");
            return;
        }
        if (!apiKey) {
            this.toast(`请输入${engine} API密钥 / Vui lòng nhập khóa API ${engine}`, "error");
            return;
        }

        document.getElementById("btn-test-key").disabled = true;
        document.getElementById("btn-test-key").textContent = "测试中… / Đang kiểm tra...";

        try {
            const result = await API.testEngine(engine, apiKey);
            if (result.valid) {
                this.toast(result.message, "success");
                const saved = JSON.parse(localStorage.getItem("cad_translator_keys") || "{}");
                saved[engine] = apiKey;
                localStorage.setItem("cad_translator_keys", JSON.stringify(saved));
            } else {
                this.toast(result.message, "error");
            }
        } catch (err) {
            this.toast("连接错误 / Lỗi kết nối", "error");
        } finally {
            document.getElementById("btn-test-key").disabled = false;
            document.getElementById("btn-test-key").textContent = "测试 / Kiểm tra";
        }
    },

    // === Utilities ===

    toggleMaximize() {
        const preview = document.getElementById("workspace-preview");
        const btn = document.getElementById("btn-maximize");
        const isMax = preview.classList.toggle("maximized");
        btn.textContent = isMax ? "✕" : "⛶";
        btn.title = isMax ? "还原 / Thu nhỏ" : "最大化 / Phóng to";
        if (Viewer.canvas) {
            setTimeout(() => {
                const c = Viewer.canvas;
                if (isMax) {
                    c.style.maxWidth = "100%";
                    c.style.maxHeight = "calc(100vh - 24px)";
                } else {
                    c.style.maxWidth = "";
                    c.style.maxHeight = "";
                }
            }, 100);
        }
    },

    toast(message, type = "info") {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transition = "opacity 0.3s";
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },
};

// Boot
document.addEventListener("DOMContentLoaded", () => {
    Viewer.init("pdf-viewer");
    App.init();
});
