# AIPPT - AI驱动的PowerPoint生成系统

> 利用大语言模型自动生成专业演示文稿的智能系统

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 项目简介

AIPPT 是一个基于大语言模型的智能PPT生成系统，能够根据用户提供的主题自动创建专业的演示文稿。系统支持多种PPT风格，可以生成HTML和PPTX两种格式，并提供完整的RESTful API接口。

### 核心特性

- **智能大纲生成** - 自动生成结构化的PPT大纲
- **多风格支持** - 商务、学术、创意、简约、教育、科技、自然、杂志、TED等多种风格
- **双格式输出** - 同时生成HTML和PPTX格式
- **自定义资料** - 支持输入文档解析结果、用户整理的资料或联网搜索结果
- **图片搜索** - 集成Unsplash/Pexels图片搜索API
- **多模型支持** - 支持OpenAI、通义千问、DeepSeek、智谱AI等多个LLM提供商
- **RESTful API** - 完整的API接口，易于集成

## 目录

- [快速开始](#快速开始)
- [环境要求](#环境要求)
- [安装步骤](#安装步骤)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [API文档](#api文档)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [常见问题](#常见问题)
- [开发指南](#开发指南)
- [更新日志](#更新日志)

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/AIPPT.git
cd AIPPT
```

### 2. 安装依赖

```bash
# 安装Python依赖
uv sync

# 安装Node.js依赖（用于PPTX转换）
npm install
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入API密钥
# 至少需要配置一个大模型API密钥（推荐通义千问）
```

### 4. 启动服务

```bash
python start.py
```

服务启动后访问：
- API文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

### 5. 快速测试

```bash
curl -X POST "http://localhost:8000/api/v1/ppt/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "人工智能的发展趋势",
    "style": "business",
    "slides": 10
  }'
```

## 环境要求

### 必需环境

- **Python**: >= 3.11
- **Node.js**: >= 16.0.0
- **包管理器**: uv (Python) 和 npm (Node.js)

### 可选环境

- **Git**: 用于版本控制
- **Docker**: 用于容器化部署（未来支持）

## 安装步骤

### 方式一：使用 uv（推荐）

```bash
# 安装uv（如果未安装）
pip install uv

# 同步依赖
uv sync
```

### 方式二：使用 pip

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 安装Node.js依赖

```bash
# 进入script目录
cd src/services/script

# 安装依赖
npm install

# 返回项目根目录
cd ../..
```

## 配置说明

### 环境变量配置

在项目根目录创建 `.env` 文件，配置以下参数：

```bash
# ===========================================
# 大模型API配置（至少配置一个）
# ===========================================

# 通义千问（推荐，默认使用）
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 智谱AI
ZHIPU_API_KEY=your_zhipu_api_key_here

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# ===========================================
# 图片搜索API（可选）
# ===========================================

# Unsplash API
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here

# Pexels API
PEXELS_API_KEY=your_pexels_api_key_here

# ===========================================
# 默认LLM配置
# ===========================================
DEFAULT_LLM_PROVIDER=qwen
DEFAULT_LLM_MODEL=qwen-turbo
DEFAULT_LLM_TEMPERATURE=0.7
DEFAULT_LLM_MAX_TOKENS=4000

# ===========================================
# 项目配置
# ===========================================
PROJECT_NAME=AIPPT
PROJECT_VERSION=1.0.0
DEBUG=false
```

### LLM配置文件

在 [config/llm_config.yaml](config/llm_config.yaml) 中可以配置不同Agent使用的模型：

```yaml
providers:
  openai:
    name: "OpenAI"
    base_url: "https://api.openai.com/v1"
    default_model: "gpt-4o-mini"

  qwen:
    name: "Qwen"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    default_model: "qwen-turbo"

  deepseek:
    name: "DeepSeek"
    base_url: "https://api.deepseek.com/v1"
    default_model: "deepseek-chat"

default:
  provider: "qwen"
  model_name: "qwen-turbo"
  temperature: 0.7
  max_tokens: 4000
```

## 使用方法

### 方式一：使用API接口

#### 1. 生成PPT大纲

```python
import requests

url = "http://localhost:8000/api/v1/ppt/outline"
payload = {
    "topic": "人工智能的发展趋势",
    "style": "business",
    "slides": 10
}

response = requests.post(url, json=payload)
result = response.json()

print(f"大纲: {result['data']['outline']}")
```

#### 2. 生成完整PPT

```python
import requests

url = "http://localhost:8000/api/v1/ppt/generate"
payload = {
    "topic": "人工智能的发展趋势",
    "style": "business",
    "slides": 10,
    "include_speech_notes": False,
    "convert_to_pptx": True
}

response = requests.post(url, json=payload, timeout=300)
result = response.json()

if result['code'] == 200:
    print(f"项目ID: {result['data']['project_id']}")
    print(f"PPTX文件: {result['data']['pptx_file']}")
```

#### 3. 使用自定义资料

```python
import requests

url = "http://localhost:8000/api/v1/ppt/generate"

# 从文档解析或联网搜索得到的资料
materials = """
根据最新研究：
1. 2024年AI技术在医疗领域取得重大突破
2. 大语言模型性能提升显著
3. 多模态AI应用广泛落地
"""

payload = {
    "topic": "2024年AI技术总结",
    "style": "tech",
    "slides": 12,
    "custom_materials": materials,
    "convert_to_pptx": True
}

response = requests.post(url, json=payload)
result = response.json()

print(f"生成状态: {result['message']}")
```

#### 4. 从大纲生成PPT

```python
import requests
import json

url = "http://localhost:8000/api/v1/ppt/generate-from-outline"

# 定义自定义大纲
outline = {
    "title": "产品发布会",
    "subtitle": "创新科技，引领未来",
    "colors": {
        "primary": "#ff6b6b",
        "accent": "#ffd93d",
        "background": "#ffffff",
        "text": "#2d3436",
        "secondary": "#636e72"
    },
    "pages": [
        {
            "slide_number": 1,
            "page_type": "title",
            "title": "新产品发布",
            "key_points": [],
            "has_image": True,
            "image_config": [{"type": "photo", "query": "technology"}],
            "description": "封面"
        },
        {
            "slide_number": 2,
            "page_type": "content",
            "title": "核心功能",
            "key_points": ["智能识别", "实时分析", "云端同步"],
            "has_chart": False,
            "has_image": False,
            "description": "产品功能介绍"
        }
    ]
}

payload = {
    "outline": outline,
    "style": "creative",
    "convert_to_pptx": True
}

response = requests.post(url, json=payload)
result = response.json()

print(f"项目ID: {result['data']['project_id']}")
```

### 方式二：命令行工具

```bash
# 生成PPT
python src/main.py --topic "人工智能" --style business --slides 10

# 使用自定义资料
python src/main.py \
  --topic "技术报告" \
  --style tech \
  --custom-materials "data/research.txt" \
  --slides 15
```

### 方式三：Python SDK

```python
from src.services.ppt_service import PPTService

# 初始化服务
service = PPTService()

# 生成PPT
result = service.generate_ppt(
    topic="人工智能的发展趋势",
    style="business",
    slides=10,
    convert_to_pptx=True
)

print(f"生成完成: {result['project_id']}")
```

## API文档

详细的API文档请参考 [API_GUIDE.md](API_GUIDE.md)

### 主要接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/v1/ppt/outline` | POST | 生成PPT大纲 |
| `/api/v1/ppt/generate` | POST | 生成完整PPT |
| `/api/v1/ppt/generate-from-outline` | POST | 从大纲生成PPT |
| `/api/v1/ppt/{project_id}/convert` | POST | 转换为PPTX |
| `/api/v1/ppt/{project_id}/download/pptx` | GET | 下载PPTX文件 |
| `/api/v1/files/list` | GET | 列出所有项目 |
| `/health` | GET | 健康检查 |

### 支持的PPT风格

- `business` - 商务风格
- `academic` - 学术风格
- `creative` - 创意风格
- `simple` - 简约风格
- `educational` - 教育风格
- `tech` - 科技风格
- `nature` - 自然风格
- `magazine` - 杂志风格
- `ted` - TED演讲风格

## 项目结构

```
AIPPT/
├── config/                    # 配置文件
│   └── llm_config.yaml       # LLM配置
├── src/                       # 源代码
│   ├── agents/               # AI代理
│   │   └── ppt/              # PPT生成相关Agent
│   ├── api/                  # API接口
│   │   ├── routes/           # 路由定义
│   │   ├── schemas/          # 数据模型
│   │   ├── main.py           # FastAPI应用
│   │   └── dependencies.py   # 依赖注入
│   ├── llm/                  # LLM模块
│   │   ├── manager.py        # LLM管理器
│   │   ├── client.py         # LLM客户端
│   │   ├── config.py         # 配置加载
│   │   └── prompts.py        # 提示词模板
│   ├── models/               # 数据模型
│   │   ├── api.py            # API模型
│   │   ├── search.py         # 搜索模型
│   │   └── response.py       # 响应模型
│   ├── ppt/                  # PPT生成模块
│   │   ├── ppt_coordinator.py      # PPT协调器
│   │   ├── multi_slide_generator.py # 多页面生成器
│   │   ├── design_coordinator.py    # 设计协调器
│   │   ├── layout_generator.py      # 布局生成器
│   │   └── page_agent.py            # 页面Agent
│   ├── searcher/             # 搜索模块
│   │   ├── base.py           # 基础搜索类
│   │   └── duckduckgo.py     # DuckDuckGo搜索
│   ├── services/             # 服务层
│   │   ├── ppt_service.py    # PPT服务
│   │   ├── html2pptx_service.py  # HTML转PPTX服务
│   │   ├── file_service.py   # 文件服务
│   │   └── script/           # Node.js脚本
│   │       ├── convert.js    # 转换脚本
│   │       ├── auto_fix.js   # 自动修复
│   │       └── normalize_html.py  # HTML规范化
│   ├── templates/            # HTML模板
│   │   ├── slide_*.html      # 各类幻灯片模板
│   │   ├── index.html        # 导航页
│   │   └── presenter.html    # 演示页
│   ├── tools/                # 工具模块
│   │   ├── image_searcher.py # 图片搜索
│   │   ├── web_searcher.py   # 网页搜索
│   │   ├── image_downloader.py  # 图片下载
│   │   ├── content_extractor.py  # 内容提取
│   │   └── time_tool.py      # 时间工具
│   ├── utils/                # 工具函数
│   │   ├── document_loader.py    # 文档加载
│   │   └── image_processor.py    # 图片处理
│   ├── storage/              # 存储模块
│   │   └── search_storage.py # 搜索结果存储
│   ├── prompt/               # 提示词
│   │   ├── htmlprompt.txt    # 中文提示词
│   │   ├── htmlprompt_en.txt # 英文提示词
│   │   └── ppt_styles.json   # PPT风格配置
│   └── main.py               # 主程序入口
├── storage/                  # 存储目录
│   └── {timestamp}_{topic}/  # 项目目录
│       ├── metadata.json     # 项目元数据
│       ├── intermediate/     # 中间结果
│       ├── reports/          # 生成报告
│       │   └── ppt/          # PPT文件
│       │       ├── slides/   # HTML幻灯片
│       │       ├── index.html
│       │       ├── presenter.html
│       │       └── output.pptx
│       └── search_results/   # 搜索结果
├── .env.example              # 环境变量模板
├── .env                      # 环境变量（需自行创建）
├── pyproject.toml            # Python项目配置
├── uv.lock                   # Python依赖锁定
├── start.py                  # 服务启动脚本
├── README.md                 # 项目文档
├── API_GUIDE.md              # API使用指南
└── DEPENDENCIES.md           # 依赖说明
```

## 技术栈

### 后端

- **FastAPI** - 现代化的Web框架
- **Uvicorn** - ASGI服务器
- **Pydantic** - 数据验证
- **Python 3.11+** - 编程语言

### AI/LLM

- **OpenAI SDK** - OpenAI API客户端
- **Instructor** - 结构化输出
- **多模型支持** - OpenAI、通义千问、DeepSeek、智谱AI等

### 数据处理

- **Jinja2** - 模板引擎
- **PyYAML** - YAML配置解析
- **BeautifulSoup4** - HTML解析
- **Pillow** - 图片处理

### HTTP/异步

- **httpx** - 异步HTTP客户端
- **aiohttp** - 异步HTTP框架
- **aiofiles** - 异步文件操作

### 前端转换

- **Node.js** - JavaScript运行环境
- **Playwright** - 浏览器自动化
- **pptxgenjs** - PPTX生成库
- **sharp** - 图片处理

### 日志/监控

- **Loguru** - 日志库
- **Langfuse** - LLM调用监控（可选）

## 常见问题

### 1. 依赖安装失败

**问题**: `uv sync` 失败

**解决方案**:
```bash
# 更新uv到最新版本
pip install --upgrade uv

# 清理缓存后重试
uv cache clean
uv sync
```

### 2. Node.js依赖问题

**问题**: Node.js模块无法加载

**解决方案**:
```bash
# 确保Node.js版本 >= 16.0.0
node --version

# 重新安装依赖
cd src/services/script
rm -rf node_modules package-lock.json
npm install
```

### 3. API调用超时

**问题**: PPT生成时API超时

**解决方案**:
- 检查网络连接
- 增加timeout参数: `timeout=300`
- 检查API密钥是否正确配置
- 查看 [config/llm_config.yaml](config/llm_config.yaml) 中的超时设置

### 4. 图片搜索失败

**问题**: 无法获取图片

**解决方案**:
- 检查Unsplash/Pexels API密钥是否配置
- 确认API密钥有效且有剩余额度
- 可以暂时关闭图片功能: `ENABLE_DOCUMENT_IMAGES=false`

### 5. PPTX转换失败

**问题**: HTML转PPTX失败

**解决方案**:
```bash
# 检查Node.js环境
cd src/services/script
node convert.js --help

# 如果失败，重新安装playwright
npx playwright install
```

### 6. LLM API错误

**问题**: LLM调用返回错误

**解决方案**:
- 检查API密钥是否正确
- 确认账户有足够额度
- 尝试切换到其他LLM提供商
- 查看日志文件获取详细错误信息

## 开发指南

### 添加新的PPT风格

1. 编辑 [src/prompt/ppt_styles.json](src/prompt/ppt_styles.json)
2. 添加新的风格配置
3. 更新 [src/api/schemas/ppt.py](src/api/schemas/ppt.py) 中的枚举

### 添加新的LLM提供商

1. 编辑 [config/llm_config.yaml](config/llm_config.yaml)
2. 在 `.env` 中添加对应的API密钥配置
3. 更新 [src/llm/client.py](src/llm/client.py) 中的客户端代码

### 自定义提示词模板

编辑以下文件：
- [src/prompt/htmlprompt.txt](src/prompt/htmlprompt.txt) - 中文提示词
- [src/prompt/htmlprompt_en.txt](src/prompt/htmlprompt_en.txt) - 英文提示词
- [src/llm/prompts.py](src/llm/prompts.py) - 提示词管理

### 添加新的搜索源

1. 在 [src/searcher/](src/searcher/) 目录创建新的搜索类
2. 继承 `BaseSearcher` 基类
3. 实现 `search()` 方法
4. 在 [src/tools/web_searcher.py](src/tools/web_searcher.py) 中注册

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_ppt_service.py

# 查看覆盖率
pytest --cov=src --cov-report=html
```

### 代码规范

```bash
# 格式化代码
black src/
isort src/

# 检查代码质量
flake8 src/
mypy src/
```

## 更新日志

### v1.1.0 (2025-01-07)
- ⭐ 新增：从大纲生成PPT接口
- ✅ 支持自定义参考资料
- ✅ 完善图片搜索功能
- ✅ 优化PPTX转换流程

### v1.0.0 (2025-01-06)
- ✅ 初始版本发布
- ✅ 实现基础PPT生成功能
- ✅ 支持多种PPT风格
- ✅ 实现HTML和PPTX双格式输出
- ✅ 提供完整的RESTful API

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送分支: `git push origin feature/AmazingFeature`
5. 提交Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目主页: [https://github.com/yourusername/AIPPT](https://github.com/yourusername/AIPPT)
- 问题反馈: [https://github.com/yourusername/AIPPT/issues](https://github.com/yourusername/AIPPT/issues)
- 文档: [API_GUIDE.md](API_GUIDE.md)

## 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenAI](https://openai.com/)
- [pptxgenjs](https://gitbrent.github.io/PptxGenJS/)
- [Playwright](https://playwright.dev/)

---

**Made with ❤️ by AIPPT Team**
