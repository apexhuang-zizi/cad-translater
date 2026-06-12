FROM python:3.11-slim

# Tesseract OCR + system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-vie \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download EasyOCR models at build time (cache-friendly)
RUN python -c "import easyocr; r = easyocr.Reader(['ch_sim','en'], gpu=False); print('EasyOCR ready')"

# Copy app
COPY . .

# Font directory
RUN mkdir -p fonts data uploads

# Render uses $PORT, default 5000
ENV PORT=5000

EXPOSE 5000

CMD ["sh", "-c", "python app.py"]
