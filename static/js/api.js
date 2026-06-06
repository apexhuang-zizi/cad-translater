/**
 * API module - Communication with Flask backend.
 * Hybrid Architecture: Vector | AI Vision | Template | Manual
 */
const API = {
    base: "",

    async upload(formData) {
        const resp = await fetch(`${this.base}/api/upload`, {
            method: "POST",
            body: formData,
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Upload failed");
        }
        return resp.json();
    },

    async scan(fileId) {
        const resp = await fetch(`${this.base}/api/pdf/${fileId}/scan`, {
            method: "POST",
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Scan failed");
        }
        return resp.json();
    },

    async extractPage(fileId, pageNum) {
        const resp = await fetch(
            `${this.base}/api/pdf/${fileId}/page/${pageNum}/extract`
        );
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Extract failed");
        }
        return resp.json();
    },

    async ocrPage(fileId, pageNum, options = {}) {
        const resp = await fetch(
            `${this.base}/api/pdf/${fileId}/page/${pageNum}/ocr`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(options),
            }
        );
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "OCR failed");
        }
        return resp.json();
    },

    // Manual calibration
    async manualAdd(fileId, pageNum, text, bbox) {
        const resp = await fetch(
            `${this.base}/api/pdf/${fileId}/page/${pageNum}/manual`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text, bbox }),
            }
        );
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Manual add failed");
        }
        return resp.json();
    },

    async manualClear(fileId, pageNum) {
        const resp = await fetch(
            `${this.base}/api/pdf/${fileId}/page/${pageNum}/manual`,
            { method: "DELETE" }
        );
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Manual clear failed");
        }
        return resp.json();
    },

    // Template management
    async listTemplates(drawingType = null) {
        const url = new URL(`${this.base}/api/templates`, window.location.origin);
        if (drawingType) url.searchParams.append("type", drawingType);
        const resp = await fetch(url);
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "List templates failed");
        }
        return resp.json();
    },

    async saveTemplate(data) {
        const resp = await fetch(`${this.base}/api/templates`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Save template failed");
        }
        return resp.json();
    },

    async getTemplate(templateId) {
        const resp = await fetch(`${this.base}/api/templates/${templateId}`);
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Get template failed");
        }
        return resp.json();
    },

    async deleteTemplate(templateId) {
        const resp = await fetch(`${this.base}/api/templates/${templateId}`, {
            method: "DELETE",
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Delete template failed");
        }
        return resp.json();
    },

    async applyTemplate(templateId, pageWidth, pageHeight) {
        const resp = await fetch(`${this.base}/api/templates/${templateId}/apply`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ page_width: pageWidth, page_height: pageHeight }),
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Apply template failed");
        }
        return resp.json();
    },

    async translatePage(fileId, pageNum, engine, items, apiKey) {
        const resp = await fetch(
            `${this.base}/api/pdf/${fileId}/page/${pageNum}/translate`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ engine, items, api_key: apiKey }),
            }
        );
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Translation failed");
        }
        return resp.json();
    },

    async overlayPage(fileId, pageNum, items) {
        const resp = await fetch(
            `${this.base}/api/pdf/${fileId}/page/${pageNum}/overlay`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ items }),
            }
        );
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Overlay failed");
        }
        return resp.json();
    },

    getOverlayPreviewUrl(fileId, pageNum) {
        return `${this.base}/api/pdf/${fileId}/page/${pageNum}/preview/overlay?t=${Date.now()}`;
    },

    getPagePreviewUrl(fileId, pageNum) {
        return `${this.base}/api/pdf/${fileId}/page/${pageNum}/preview?t=${Date.now()}`;
    },

    async confirmPage(fileId, pageNum, items) {
        const resp = await fetch(
            `${this.base}/api/pdf/${fileId}/page/${pageNum}/confirm`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ items }),
            }
        );
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Confirm failed");
        }
        return resp.json();
    },

    async finalize(fileId) {
        const resp = await fetch(
            `${this.base}/api/pdf/${fileId}/finalize`,
            { method: "POST" }
        );
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Finalize failed");
        }
        return resp.json();
    },

    getDownloadUrl(fileId) {
        return `${this.base}/api/pdf/${fileId}/download`;
    },

    async getEngineConfig() {
        const resp = await fetch(`${this.base}/api/engine/config`);
        return resp.json();
    },

    async setEngineConfig(engine, deepseekKey, geminiKey) {
        const resp = await fetch(`${this.base}/api/engine/config`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                engine,
                deepseek_key: deepseekKey,
                gemini_key: geminiKey,
            }),
        });
        return resp.json();
    },

    async testEngine(engine, apiKey) {
        const resp = await fetch(`${this.base}/api/engine/test`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ engine, api_key: apiKey }),
        });
        return resp.json();
    },

    async getProjectStatus(fileId) {
        const resp = await fetch(`${this.base}/api/project/${fileId}/status`);
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Status fetch failed");
        }
        return resp.json();
    },
};
