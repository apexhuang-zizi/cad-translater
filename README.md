# CAD Translator (PDF图纸翻译)

CAD工程图纸中文/英文注释 → 越南语自动翻译工具。
支持矢量PDF直接提取 + 栅格PDF智能OCR，译文原地叠加。

## 架构

```
上传PDF → 类型检测 → 矢量提取/Surya OCR → 翻译 → V11叠加 → 逐页审核 → 导出
```

### 核心技术矩阵

| PDF类型 | 提取方式 | 准确度 |
|---------|---------|--------|
| 矢量CAD PDF | PyMuPDF 直接提取文本+坐标 | ★★★★★ |
| 栅格CAD PDF | Surya检测 + Tesseract逐区域OCR | ★★★★☆ |
| AI视觉 | Gemini Vision API（需密钥） | ★★★★☆ |
| 模板复用 | 人工标定 → 模板匹配 | ★★★★☆ |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 安装 Tesseract OCR（Windows）
# 下载：https://github.com/UB-Mannheim/tesseract/wiki
# 安装时勾选 chi_sim (简体中文) 和 eng (英文) 语言包

# 3. 启动服务
python app.py

# 4. 打开浏览器
# http://localhost:5000
```

## 使用流程

1. **上传PDF** — 拖放或选择CAD图纸PDF文件
2. **自动扫描** — 检测矢量/栅格类型，运行对应OCR
3. **逐页审核** — 确认/修改/手动标定译文，Canvas拖拽微调
4. **导出** — 生成带越南语注释的PDF

## 翻译引擎

- **Google Translate** — 免费，无需API密钥
- **DeepSeek AI** — 需API密钥，工程术语更准确
- **Gemini AI** — 需API密钥，支持视觉OCR

## 项目结构

```
cad-translator/
├── app.py                 # Flask 主应用
├── requirements.txt       # Python 依赖
├── templates/
│   └── index.html         # SPA 前端
├── static/
│   ├── css/style.css
│   └── js/
│       ├── api.js         # API 通信
│       ├── app.js         # 主逻辑
│       └── viewer.js      # Canvas 查看器
└── backend/
    ├── pdf_processor.py   # PDF 文本提取 + V11 叠加
    ├── surya_ocr.py       # Surya检测 + Tesseract 栅格OCR
    ├── ocr_engine.py      # Tesseract 回退 OCR
    ├── ai_vision_engine.py # Gemini Vision OCR
    ├── translator.py      # 翻译引擎
    ├── frame_detector.py  # 图框检测
    ├── template_manager.py # 标定模板管理
    └── storage.py         # SQLite 持久化
```

## 外部依赖

- **Tesseract OCR 5.x** — 栅格PDF文字识别
  - 语言包：chi_sim (简体中文) + eng (英文)
  - 默认安装路径：`C:\Program Files\Tesseract-OCR\`
- **Surya** — 文字区域检测模型（首次运行自动下载 ~200MB）

## 许可

MIT
