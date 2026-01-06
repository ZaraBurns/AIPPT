# AIPPT - 快速开始指南

## ✅ 已完成的模块补充

### 1. **配置文件** ✓
- `config/llm_config.yaml` - LLM 配置（支持 Qwen、DeepSeek、OpenAI 等多提供商）
- `.env` - 环境变量（API 密钥）
- `.env.example` - 环境变量模板

### 2. **主入口文件** ✓
- `src/main.py` - 完整的 CLI 命令行工具
  - 支持多种参数配置
  - 自动错误处理
  - 进度输出

### 3. **模板路径修复** ✓
- `src/ppt/multi_slide_generator.py` - 已修复模板路径指向 `src/templates/`

### 4. **Python 依赖** ✓
- 已安装所有必需的包（pydantic, openai, jinja2, loguru, httpx, pytz 等）

---

## 🚀 快速开始

### 步骤 1: 配置 API 密钥

编辑 `.env` 文件，添加你的 API 密钥：

```env
# 选择一个 LLM 提供商（推荐使用通义千问）
DASHSCOPE_API_KEY=your_qwen_api_key_here
# 或
DEEPSEEK_API_KEY=your_deepseek_api_key_here
# 或
OPENAI_API_KEY=your_openai_api_key_here

# 图片搜索（可选）
UNSPLASH_ACCESS_KEY=your_unsplash_key_here
```

### 步骤 2: 生成 PPT

```bash
# 基本用法
cd D:\Users\chenmengyue\res3\AIPPT
uv run python src/main.py "人工智能的发展趋势"

# 指定风格和页数
uv run python src/main.py "气候变化的影响" --style academic --slides 15

# 包含演讲稿
uv run python src/main.py "机器学习基础" --speech-notes

# 详细输出（调试用）
uv run python src/main.py "Python编程" --verbose
```

### 支持的风格

- `business` - 商务风格（默认）
- `academic` - 学术风格
- `creative` - 创意风格
- `simple` - 简约风格
- `educational` - 教育风格
- `tech` - 科技风格
- `nature` - 自然风格
- `magazine` - 杂志风格
- `ted` - TED 演讲风格

---

## 📂 项目结构

```
AIPPT/
├── config/
│   └── llm_config.yaml          # LLM 配置
├── src/
│   ├── llm/                     # LLM 模块 ✓
│   │   ├── manager.py           # 多提供商管理器
│   │   ├── client.py            # LLM 客户端
│   │   ├── config.py            # 配置模型
│   │   └── prompts.py           # 提示词管理
│   ├── ppt/                     # PPT 核心模块 ✓
│   │   ├── ppt_coordinator.py   # 主协调器
│   │   ├── design_coordinator.py # 设计协调器
│   │   ├── page_agent.py        # 页面生成代理
│   │   └── multi_slide_generator.py # 多页生成器
│   ├── tools/                   # 工具模块 ✓
│   │   ├── image_searcher.py    # 图片搜索
│   │   ├── web_searcher.py      # 网页搜索
│   │   └── ...
│   ├── templates/               # Jinja2 模板 ✓
│   │   ├── slide_*.html         # 幻灯片模板
│   │   ├── index.html           # 导航页
│   │   └── presenter.html       # 演示页
│   ├── script/                  # Node.js 转换工具 ✓
│   │   ├── convert.js           # HTML → PPTX
│   │   ├── html2pptx.js         # 转换核心
│   │   └── package.json
│   └── main.py                  # 主入口 ✓
├── output/                      # 输出目录
├── .env                         # 环境变量
├── pyproject.toml              # Python 配置
└── QUICKSTART.md               # 本文档
```

---

## 🔧 故障排除

### 问题 1: 模块导入错误

**错误**: `attempted relative import beyond top-level package`

**解决**:
```bash
# 确保使用 uv run 运行
uv run python src/main.py "主题"
```

### 问题 2: API 密钥未设置

**错误**: `API Key not found`

**解决**:
- 检查 `.env` 文件是否存在
- 确认 API 密钥已正确填写
- 确保 `.env` 在项目根目录

### 问题 3: 模板文件未找到

**错误**: `TemplateNotFound`

**解决**:
```bash
# 检查模板目录
ls src/templates/

# 应该看到：
# slide_cover.html, slide_content.html, index.html 等
```

---

## 📊 输出说明

生成的 PPT 会保存在 `output/` 目录，包含：

1. **HTML 文件** - 完整的幻灯片演示
2. **JSON 文件** - 结构化数据
3. **演讲稿** - 如果启用 `--speech-notes`

---

## ⚙️ 高级配置

### 自定义 LLM 配置

编辑 `config/llm_config.yaml`：

```yaml
default:
  provider: "deepseek"  # 切换提供商
  model_name: "deepseek-chat"
  temperature: 0.7
  max_tokens: 4000

agents:
  outline_generator:
    provider: "qwen"
    model_name: "qwen-plus"  # 使用更强的模型
```

### HTML 转 PPTX

生成 HTML 后，可以使用 Node.js 工具转换为 PPTX：

```bash
cd src/script
node convert.js --folder ../../output/ppt/slides --output ../../output/presentation.pptx
```

---

## 🎯 下一步

### 可选功能扩展

1. **搜索集成** - 集成网页搜索获取实时信息
2. **图片优化** - 配置 Unsplash/Pexels API 获取高质量图片
3. **自定义模板** - 修改 `src/templates/` 中的模板
4. **批处理** - 编写脚本批量生成多个 PPT

### 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交 Pull Request

---

**最后更新**: 2025-01-06
**Python 版本**: >= 3.11
**Node.js 版本**: >= 16.0.0
