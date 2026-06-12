# CAD PDF Translator v2.0 — Furniture Edition

CAD工程图纸中文/英文注释 → 越南语自动翻译工具。
支持矢量PDF直接提取 + 栅格PDF智能OCR，译文原地叠加。

## v2.0 新特性

| 特性 | 说明 |
|------|------|
| **EasyOCR 替换 Surya** | 解决 Windows Surya 模型加载问题，121 MB模型，CPU可用 |
| **JSON 格式翻译** | 结构化返回，替换旧版 `---` 分隔符 |
| **同义词归一化** | 36条家具行业规则（活动层板→层板） |
| **企业术语库** | 29条默认家具术语（中文→越南语），管道占位符保护 |
| **翻译记忆 (TM)** | dict+JSON文件缓存，重复项零API调用 |
| **自更新检查** | `/api/version/check` 自动核对云端版本号 |

## 架构

```
上传PDF → 类型检测 → 矢量提取/EasyOCR+Tesseract
                    → 同义词归一化 → 术语占位符 → TM查找
                    → AI/Google翻译 → 还原术语 → TM缓存
                    → V11智能叠加 → 逐页审核 → 导出
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 安装 Tesseract OCR（Windows）
# 下载：https://github.com/UB-Mannheim/tesseract/wiki
# 安装时勾选 chi_sim + eng 语言包

# 3. 启动服务
start.bat
# 或: python app.py

# 4. 打开浏览器
# http://localhost:5000
```

## 翻译管道 (v2)

```
text → normalize(同义词) → glossary_placeholder(术语占位符)
     → TM_lookup(缓存命中则跳过API) → AI/Google(仅未命中)
     → restore(还原术语) → TM_cache(保存结果)
```

### 支持引擎

| 引擎 | 需要 API Key | 成本 | 推荐场景 |
|------|-------------|------|---------|
| Google | 否 | 免费 | 日常使用 |
| DeepSeek | 是 | $0.14/M tokens | 专业术语 |
| Gemini | 是 | 免费额度 | 混合中英 |

## API 端点

### 翻译
- `POST /api/translate` — 批量翻译
- `POST /api/translator/test` — 管道测试

### 术语管理
- `GET/POST /api/translator/glossary` — 术语库 CRUD
- `DELETE /api/translator/glossary/<term>`
- `GET/POST /api/translator/synonyms` — 同义词 CRUD
- `DELETE /api/translator/synonyms/<variant>`

### 翻译记忆
- `GET /api/translator/tm` — 查看 TM
- `GET /api/translator/tm/export` — 导出 JSON
- `POST /api/translator/tm/import` — 导入 JSON
- `POST /api/translator/tm/clear` — 清空

### 版本
- `GET /api/version` — 本地版本
- `GET /api/version/check` — 检查更新

## 项目结构

```
cad-translator/
├── app.py                  # Flask 主应用
├── updater.py              # 自更新模块
├── build_installer.py      # 打包脚本
├── version.json            # 版本信息
├── start.bat               # 启动脚本
├── requirements.txt
├── templates/
│   └── index.html          # SPA 前端 + v2 设置面板
├── static/
│   ├── css/style.css
│   └── js/
│       ├── api.js
│       ├── app.js
│       └── viewer.js
├── backend/
│   ├── pdf_processor.py    # 矢量提取 + V11 叠加
│   ├── surya_ocr.py        # EasyOCR检测 + Tesseract识别
│   ├── ocr_engine.py       # Tesseract 回退
│   ├── ai_vision_engine.py  # Gemini Vision
│   ├── translator.py       # v2 翻译管道
│   ├── frame_detector.py   # 图框检测
│   ├── template_manager.py  # 模板匹配
│   └── storage.py          # SQLite 持久化
└── data/
    ├── glossary.json        # 企业术语库
    ├── synonym_map.json     # 同义词映射
    └── translation_memory.json  # TM 缓存
```

## 外部依赖

- **Tesseract OCR 5.x** — 栅格文字识别（chi_sim + eng 语言包）
- **EasyOCR** — 文本区域检测（自动安装，121 MB）

## 打包发布

```bash
# 生成 ZIP + Inno Setup 脚本
python build_installer.py

# 仅 ZIP
python build_installer.py --zip

# 更新版本号：编辑 version.json
```

## 许可

MIT
