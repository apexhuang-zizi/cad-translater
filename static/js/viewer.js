/**
 * PDF Viewer with Canvas-based translation box overlay and drag support.
 */
const Viewer = {
    container: null,
    canvas: null,
    overlay: null,
    ctx: null,
    pdfDoc: null,
    currentPage: 0,
    scale: 1.5,
    items: [],
    transBoxes: [],
    frameZone: null,
    onBoxUpdate: null,  // callback when box position changes

    init(containerId) {
        this.container = document.getElementById(containerId);
        this.canvas = this.container.querySelector("canvas");
        this.overlay = this.container.querySelector(".overlay-layer");
        this.ctx = this.canvas.getContext("2d");
    },

    async loadPage(previewUrl) {
        const img = new Image();
        img.src = previewUrl;
        await new Promise((resolve, reject) => {
            img.onload = resolve;
            img.onerror = reject;
        });

        this.canvas.width = img.width;
        this.canvas.height = img.height;
        this.ctx.clearRect(0, 0, img.width, img.height);
        this.ctx.drawImage(img, 0, 0);
        this.overlay.style.width = img.width + "px";
        this.overlay.style.height = img.height + "px";
        this.scale = img.width / 1191;  // approximate scale from PDF points
    },

    setItems(items, frameZone) {
        this.items = items || [];
        this.frameZone = frameZone;
        this.renderBoxes();
    },

    /**
     * Convert PDF point coordinates to canvas pixel coordinates.
     * PDF page is typically ~1191pt wide, canvas is roughly scale * 1191px.
     */
    pdfToCanvas(bbox) {
        const s = this.scale;
        return {
            x: bbox[0] * s,
            y: bbox[1] * s,
            w: (bbox[2] - bbox[0]) * s,
            h: (bbox[3] - bbox[1]) * s,
        };
    },

    canvasToPdf(x, y) {
        const s = this.scale;
        return { x: x / s, y: y / s };
    },

    renderBoxes() {
        // Clear existing boxes
        this.overlay.innerHTML = "";
        this.transBoxes = [];

        // Show frame zone indicator
        if (this.frameZone) {
            const fl = this.frameZone.left * this.scale;
            const fw = (this.frameZone.right - this.frameZone.left) * this.scale;
            const fh = this.overlay.offsetHeight;

            const div = document.createElement("div");
            div.className = "frame-indicator";
            div.style.left = fl + "px";
            div.style.width = fw + "px";
            div.style.height = fh + "px";
            this.overlay.appendChild(div);
        }

        // Create translation boxes
        this.items.forEach((item, idx) => {
            if (item.status === "skipped") return;

            const pos = this.pdfToCanvas(item.bbox);
            // Prefer below placement for initial position
            const defaultY = pos.y + pos.h + 6 * this.scale;
            const placed = item.placed_bbox
                ? this.pdfToCanvas(item.placed_bbox)
                : { x: pos.x, y: defaultY, w: pos.w * 1.8, h: 28 * this.scale };

            const box = this.createBox(idx, pos, placed, item);
            this.overlay.appendChild(box.el);
            this.transBoxes.push(box);

            // Also show source bbox as a light orange dashed rectangle
            const srcEl = document.createElement("div");
            srcEl.style.cssText = `
                position:absolute;
                left:${pos.x}px; top:${pos.y}px;
                width:${pos.w}px; height:${pos.h}px;
                border:1px dashed #E65100;
                pointer-events:none;
                opacity:0.4;
            `;
            this.overlay.appendChild(srcEl);
        });
    },

    createBox(idx, sourcePos, placedPos, item) {
        const el = document.createElement("div");
        const text = item.confirmed_translation || item.translated || "";
        const confirmed = item.status === "confirmed";

        el.className = "trans-box" + (confirmed ? " confirmed" : "");
        el.id = `trans-box-${idx}`;
        el.style.left = placedPos.x + "px";
        el.style.top = placedPos.y + "px";
        el.style.width = placedPos.w + "px";
        el.style.minHeight = "28px";

        // Translation text
        const textSpan = document.createElement("span");
        textSpan.className = "text";
        textSpan.textContent = text;
        el.appendChild(textSpan);

        // Edit indicator icon (pencil)
        const editIcon = document.createElement("span");
        editIcon.className = "edit-icon";
        editIcon.innerHTML = "&#9998;";  // pencil
        editIcon.title = "Double-click to edit / Nhấp đúp để sửa";
        editIcon.style.cssText = `
            position:absolute;
            right:2px; top:2px;
            font-size:12px;
            color:#E65100;
            opacity:0.6;
            pointer-events:none;
        `;
        el.appendChild(editIcon);

        // Resize handle
        const handle = document.createElement("div");
        handle.className = "resize-handle";
        el.appendChild(handle);

        // Drag logic
        this.makeDraggable(el, idx);
        this.makeResizable(el, handle, idx);

        // Double-click to edit text directly on canvas
        el.addEventListener("dblclick", (e) => {
            e.stopPropagation();
            e.preventDefault();
            // Cancel any in-progress drag
            if (el._dragging) {
                el._dragging = false;
                el.classList.remove("highlight");
            }
            this.startInlineEdit(idx, el);
        });

        // Click to select
        el.addEventListener("click", (e) => {
            e.stopPropagation();
            this.selectBox(idx);
        });

        return { el, idx, item };
    },

    startInlineEdit(idx, boxEl) {
        const item = this.items[idx];
        if (!item) return;
        const currentText = item.confirmed_translation || item.translated || "";
        const textSpan = boxEl.querySelector(".text");
        if (!textSpan) return;

        // Save original width to restore later
        const origWidth = boxEl.style.width;
        const origHeight = boxEl.style.height;

        // Replace span with visible input
        const input = document.createElement("input");
        input.type = "text";
        input.value = currentText;
        input.style.cssText = `
            width: 100%;
            min-width: 140px;
            padding: 3px 6px;
            font-size: 14px;
            font-weight: 600;
            color: #E65100;
            background: rgba(255,255,255,0.92);
            border: 2px solid #E65100;
            border-radius: 3px;
            outline: none;
            font-family: inherit;
            pointer-events: auto;
            z-index: 100;
            position: relative;
        `;
        textSpan.replaceWith(input);

        // Expand box width temporarily for editing
        boxEl.style.width = Math.max(parseFloat(origWidth) || 140, 180) + "px";
        boxEl.style.minHeight = "32px";
        boxEl.style.zIndex = "100";

        input.focus();
        input.select();

        const finishEdit = () => {
            const newText = input.value.trim();
            if (newText) {
                item.confirmed_translation = newText;
                this.updateBoxText(idx, newText);
            }
            // Restore original dimensions
            boxEl.style.width = origWidth;
            boxEl.style.minHeight = "28px";
            boxEl.style.zIndex = "";
            // Replace input back with span
            const newSpan = document.createElement("span");
            newSpan.className = "text";
            newSpan.textContent = item.confirmed_translation || item.translated || "";
            if (input.parentNode) input.replaceWith(newSpan);
            // Update review panel input too
            const panelInput = document.getElementById(`input-${idx}`);
            if (panelInput) panelInput.value = item.confirmed_translation || "";
        };

        input.addEventListener("blur", finishEdit);
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                input.blur();
            }
            if (e.key === "Escape") {
                e.preventDefault();
                input.value = currentText;  // revert
                input.blur();
            }
        });
    },

    makeDraggable(el, idx) {
        let startX, startY, origLeft, origTop;

        const onDown = (e) => {
            if (e.target.classList.contains("resize-handle")) return;
            // Don't start drag if target is an input element (inline editing)
            if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
            e.preventDefault();
            el._dragging = true;
            const rect = el.getBoundingClientRect();
            const parentRect = this.overlay.getBoundingClientRect();
            startX = e.clientX;
            startY = e.clientY;
            origLeft = rect.left - parentRect.left;
            origTop = rect.top - parentRect.top;
            el.classList.add("highlight");
        };

        const onMove = (e) => {
            if (!el._dragging) return;
            const parentRect = this.overlay.getBoundingClientRect();
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;

            let newLeft = origLeft + dx;
            let newTop = origTop + dy;

            // Clamp to overlay bounds
            newLeft = Math.max(0, Math.min(newLeft, this.overlay.offsetWidth - el.offsetWidth));
            newTop = Math.max(0, Math.min(newTop, this.overlay.offsetHeight - el.offsetHeight));

            el.style.left = newLeft + "px";
            el.style.top = newTop + "px";
        };

        const onUp = () => {
            if (!el._dragging) return;
            el._dragging = false;
            el.classList.remove("highlight");

            // Convert to PDF coordinates
            const pdfPos = this.canvasToPdf(
                parseFloat(el.style.left),
                parseFloat(el.style.top)
            );
            const boxW = parseFloat(el.style.width) || 100;
            const boxH = el.offsetHeight || 22;
            const pdfWH = this.canvasToPdf(boxW, boxH);

            this.items[idx].placed_bbox = [
                pdfPos.x,
                pdfPos.y,
                pdfPos.x + pdfWH.x,
                pdfPos.y + pdfWH.y,
            ];

            if (this.onBoxUpdate) {
                this.onBoxUpdate(idx, this.items[idx]);
            }
        };

        el.addEventListener("mousedown", onDown);
        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onUp);
    },

    makeResizable(el, handle, idx) {
        let startX, startY, origW, origH;
        let resizing = false;

        handle.addEventListener("mousedown", (e) => {
            e.preventDefault();
            e.stopPropagation();
            resizing = true;
            startX = e.clientX;
            startY = e.clientY;
            origW = el.offsetWidth;
            origH = el.offsetHeight;
        });

        document.addEventListener("mousemove", (e) => {
            if (!resizing) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            el.style.width = Math.max(40, origW + dx) + "px";
            el.style.height = Math.max(20, origH + dy) + "px";
        });

        document.addEventListener("mouseup", () => {
            if (!resizing) return;
            resizing = false;

            const pdfPos = this.canvasToPdf(
                parseFloat(el.style.left),
                parseFloat(el.style.top)
            );
            const pdfWH = this.canvasToPdf(
                parseFloat(el.style.width),
                el.offsetHeight
            );

            this.items[idx].placed_bbox = [
                pdfPos.x,
                pdfPos.y,
                pdfPos.x + pdfWH.x,
                pdfPos.y + pdfWH.y,
            ];

            if (this.onBoxUpdate) {
                this.onBoxUpdate(idx, this.items[idx]);
            }
        });
    },

    selectBox(idx) {
        this.transBoxes.forEach((b) => b.el.classList.remove("highlight"));
        if (idx >= 0 && idx < this.transBoxes.length) {
            this.transBoxes[idx].el.classList.add("highlight");
        }
    },

    updateBoxText(idx, text) {
        if (idx >= 0 && idx < this.transBoxes.length) {
            const span = this.transBoxes[idx].el.querySelector(".text");
            if (span) span.textContent = text;
            this.items[idx].confirmed_translation = text;
        }
    },

    markConfirmed(idx) {
        if (idx >= 0 && idx < this.transBoxes.length) {
            this.transBoxes[idx].el.classList.add("confirmed");
            this.items[idx].status = "confirmed";
        }
    },

    clear() {
        this.overlay.innerHTML = "";
        this.transBoxes = [];
    },
};
