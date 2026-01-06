# AIPPT 项目依赖安装说明

## ✅ 已安装依赖

### Python 依赖（使用 uv 包管理器）

项目已成功创建虚拟环境并安装以下依赖包：

| 包名 | 版本 | 用途 |
|------|------|------|
| pydantic | 2.12.4 | 数据验证和解析 |
| pydantic-core | 2.41.5 | Pydantic 核心库 |
| pydantic-settings | 2.12.0 | 配置管理 |
| python-dotenv | 1.2.1 | 环境变量加载 |
| annotated-types | 0.7.0 | 类型注解支持 |
| typing-extensions | 4.15.0 | 类型扩展 |
| typing-inspection | 0.4.2 | 类型检查 |

**Python 版本要求**: >= 3.11
**虚拟环境位置**: `.venv/`

### Node.js 依赖（src/script/）

HTML 转 PPTX 转换工具所需依赖：

| 包名 | 版本 | 用途 |
|------|------|------|
| pptxgenjs | 3.12.0 | 生成 PowerPoint 文件 |
| playwright | 1.57.0 | 浏览器自动化（图表截取） |
| sharp | 0.33.5 | 图片处理 |
| axios | 1.13.2 | HTTP 请求（下载图片） |

## 🚀 使用方法

### Python 开发

```bash
# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 运行 Python 脚本
python src/main.py

# 退出虚拟环境
deactivate
```

### HTML 转 PPTX 工具

```bash
cd src/script

# 转换单个文件
node convert.js --file slides/slide.html --output output.pptx

# 转换整个文件夹
node convert.js --folder slides --output merged.pptx
```

## 📦 依赖管理

### Python 依赖

```bash
# 添加新依赖
uv add <package-name>

# 同步依赖（根据 uv.lock）
uv sync

# 更新依赖
uv lock --upgrade
```

### Node.js 依赖

```bash
cd src/script

# 安装依赖
npm install

# 添加新依赖
npm install <package-name>

# 更新依赖
npm update
```

## ⚠️ 缺失依赖

根据代码分析，项目还缺少以下 Python 模块（需要手动实现）：

1. **LLM 管理模块**
   - `src/llm/manager.py` - LLM 客户端管理器
   - `src/llm/prompts.py` - 提示词模板管理

2. **PPT 生成器模块**
   - `src/agents/ppt/outline_generator.py` - PPT 大纲生成器
   - `src/agents/ppt/slide_content_generator.py` - 幻灯片内容生成器

3. **工具模块**
   - `src/tools/image_searcher.py` - 图片搜索工具
   - `src/tools/web_searcher.py` - 网页搜索工具

4. **其他 Python 依赖**
   - `openai` - OpenAI API 客户端
   - `jinja2` - 模板引擎
   - `loguru` - 日志库
   - `httpx` / `aiohttp` - 异步 HTTP 客户端

## 🔧 配置文件

### 环境变量（.env）

```env
# OpenAI API 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# Unsplash API（图片搜索）
UNSPLASH_ACCESS_KEY=your_access_key_here

# 其他配置
LOG_LEVEL=INFO
```

## 📝 项目结构

```
AIPPT/
├── .venv/                      # Python 虚拟环境
├── src/
│   ├── script/                 # Node.js 转换工具
│   │   ├── node_modules/       # Node.js 依赖
│   │   ├── package.json
│   │   ├── convert.js
│   │   ├── html2pptx.js
│   │   └── auto_fix.js
│   ├── agents/                 # AI 代理
│   │   └── ppt/
│   ├── llm/                    # LLM 模块（缺失）
│   ├── tools/                  # 工具模块（缺失）
│   ├── templates/              # Jinja2 模板
│   └── *.py                    # Python 源代码
├── uv.lock                     # Python 依赖锁定文件
├── pyproject.toml              # Python 项目配置
└── DEPENDENCIES.md             # 本文档
```

## ✨ 已完成

- ✅ Python 依赖安装完成
- ✅ Node.js 依赖安装完成
- ✅ 虚拟环境创建完成
- ⚠️ 核心模块需要补充实现

## 🎯 下一步

1. 实现缺失的 LLM 管理模块
2. 实现 PPT 生成器模块
3. 实现工具模块（图片搜索、网页搜索）
4. 安装额外的 Python 依赖（openai, jinja2, loguru 等）
5. 配置环境变量
6. 测试完整的 PPT 生成流程

---

**最后更新**: 2025-01-06
**Python 版本**: 3.11.13
**Node.js 版本**: (需要 > 16.0.0)