# AIPPT API 使用指南

> AI驱动的PowerPoint生成系统 - RESTful API接口文档

**版本**: 1.1.0
**更新时间**: 2025-01-07
**Base URL**: `http://localhost:8000`

---

## 📋 目录

- [快速开始](#快速开始)
- [API概述](#api概述)
- [接口详情](#接口详情)
  - [PPT生成接口](#ppt生成接口)
  - [PPTX转换接口](#pptx转换接口)
  - [文件下载接口](#文件下载接口)
  - [文件管理接口](#文件管理接口)
- [数据模型](#数据模型)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)

---

## 🚀 快速开始

### 1. 启动服务

```bash
# 进入项目目录
cd AIPPT

# 同步 Python 依赖（首次运行或依赖更新时）
uv sync

# 安装 Node.js 依赖（用于 PPTX 转换功能）
npm install

# 启动API服务器
python start.py
```

或使用 `uv run`:

```bash
uv run start.py
```

> **注意**：项目依赖说明
> - `uv sync` - 安装 Python 依赖（FastAPI、uvicorn、LLM SDK 等）
> - `npm install` - 安装 Node.js 依赖（html2pptx、playwright、pptxgenjs 等转换工具）

### 2. 访问API文档

启动服务后，访问以下地址查看交互式API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. 快速测试

```bash
# 生成PPT（含自动PPTX转换）
curl -X POST "http://localhost:8000/api/v1/ppt/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "人工智能的发展趋势",
    "style": "business",
    "slides": 10
  }'
```

---

## 📊 API概述

### API版本

当前版本：`v1`

所有接口路径前缀：`/api/v1/`

### 响应格式

所有接口返回统一的JSON格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-07T14:30:00"
}
```

**状态码说明：**
- `200` - 成功
- `400` - 请求参数错误
- `404` - 资源不存在
- `500` - 服务器内部错误

---

## 🔌 接口详情

### 1. PPT生成接口

#### 1.1 生成PPT大纲

**接口地址：** `POST /api/v1/ppt/outline`

**功能说明：** 生成PPT的结构化大纲，不生成完整内容。适合快速预览PPT结构。

**请求参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| topic | string | ✅ | - | PPT主题（1-200字符） |
| style | string | ❌ | business | PPT风格 |
| slides | integer | ❌ | 10 | 幻灯片数量（1-50） |
| custom_materials | string | ❌ | null | 自定义参考资料，支持文档解析、用户整理的资料、联网搜索结果等（最大10000字符） |

**PPT风格选项：**
- `business` - 商务风格
- `academic` - 学术风格
- `creative` - 创意风格
- `simple` - 简约风格
- `educational` - 教育风格
- `tech` - 科技风格
- `nature` - 自然风格
- `magazine` - 杂志风格
- `ted` - TED演讲风格

**请求示例：**

```bash
# 基础示例
curl -X POST "http://localhost:8000/api/v1/ppt/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "人工智能的发展趋势",
    "style": "business",
    "slides": 10
  }'
```

**使用自定义参考资料示例：**

```bash
# 传入自定义参考资料（文档解析结果、用户整理的资料、联网搜索结果等）
curl -X POST "http://localhost:8000/api/v1/ppt/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "量子计算的技术突破",
    "style": "tech",
    "slides": 8,
    "custom_materials": "最新研究表明，量子计算机在2024年实现了重要突破：1. IBM推出了1000+量子比特处理器；2. Google实现了量子纠错新方法；3. 中国在量子通信领域取得领先优势。"
  }'
```

```python
# Python示例：使用自定义参考资料
import requests

url = "http://localhost:8000/api/v1/ppt/outline"
materials = """
根据最新研究，人工智能技术在2024年取得重大突破：
1. 大语言模型性能提升显著
2. 多模态AI应用广泛落地
3. AI在医疗、教育等领域深度融合
"""

payload = {
    "topic": "人工智能的发展趋势",
    "style": "business",
    "slides": 10,
    "custom_materials": materials
}

response = requests.post(url, json=payload)
result = response.json()

if result['code'] == 200:
    print(f"大纲生成成功！共 {result['data']['estimated_slides']} 页")
```

**响应示例：**

```json
{
  "code": 200,
  "message": "大纲生成成功",
  "data": {
    "outline": {
      "title": "人工智能的发展趋势",
      "pages": [
        {
          "type": "cover",
          "title": "人工智能的发展趋势",
          "subtitle": "探索未来技术革命"
        },
        {
          "type": "content",
          "title": "AI技术概述",
          "key_points": ["机器学习", "深度学习", "自然语言处理"]
        }
      ]
    },
    "estimated_slides": 10,
    "estimated_time": "3-5分钟"
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-07T14:30:00"
}
```

---

#### 1.2 生成完整PPT

**接口地址：** `POST /api/v1/ppt/generate`

**功能说明：** 从主题生成完整的演示文稿，包括HTML版本和可选的PPTX版本。

**请求参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| topic | string | ✅ | - | PPT主题 |
| style | string | ❌ | business | PPT风格 |
| slides | integer | ❌ | 10 | 幻灯片数量 |
| include_speech_notes | boolean | ❌ | false | 是否包含演讲稿 |
| custom_materials | string | ❌ | null | 自定义参考资料，支持文档解析、用户整理的资料、联网搜索结果等（最大10000字符） |
| convert_to_pptx | boolean | ❌ | true | 是否转换为PPTX |

**请求示例：**

```bash
# 基础示例
curl -X POST "http://localhost:8000/api/v1/ppt/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "人工智能的发展趋势",
    "style": "business",
    "slides": 10,
    "include_speech_notes": false,
    "convert_to_pptx": true
  }'
```

**使用自定义参考资料示例：**

```bash
# 传入文档解析后的资料
curl -X POST "http://localhost:8000/api/v1/ppt/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "2024年新能源汽车市场分析",
    "style": "business",
    "slides": 12,
    "custom_materials": "根据中国汽车工业协会数据：1. 2024年新能源汽车销量达到950万辆，同比增长40%；2. 比亚迪、特斯拉、蔚来占据市场份额前三；3. 动力电池成本下降至100元/kWh以下；4. 充电桩数量突破300万台；5. 出口量突破500万辆。",
    "convert_to_pptx": true
  }'
```

```python
# Python示例：使用文档解析资料生成PPT
import requests

url = "http://localhost:8000/api/v1/ppt/generate"

# 从文档解析得到的资料
document_materials = """
【公司年度报告摘要】
财务数据：
- 2024年营业收入：50亿元，同比增长25%
- 净利润：8.5亿元，同比增长30%
- 研发投入：5亿元，占营收10%

业务亮点：
1. 云计算业务增长60%，用户数突破500万
2. 人工智能产品线收入达到15亿元
3. 国际市场拓展顺利，海外收入占比35%

未来规划：
- 加大AI研发投入，推出更多智能产品
- 深化云服务布局，目标3年内用户破千万
- 拓展欧洲、东南亚市场
"""

payload = {
    "topic": "科技公司年度业绩报告",
    "style": "business",
    "slides": 15,
    "include_speech_notes": True,
    "custom_materials": document_materials,
    "convert_to_pptx": True
}

response = requests.post(url, json=payload, timeout=300)
result = response.json()

if result['code'] == 200:
    print(f"✅ PPT生成成功！")
    print(f"   项目ID: {result['data']['project_id']}")
    print(f"   总页数: {result['data']['total_slides']}")
    print(f"   PPTX文件: {result['data']['pptx_file']}")
else:
    print(f"❌ 生成失败: {result['message']}")
```

**响应示例：**

```json
{
  "code": 200,
  "message": "PPT生成成功",
  "data": {
    "project_id": "20250107_143052_人工智能的发展趋势",
    "ppt_dir": "storage/20250107_143052_人工智能的发展趋势/reports/ppt/slides",
    "total_slides": 10,
    "index_page": "storage/20250107_143052_人工智能的发展趋势/reports/ppt/index.html",
    "presenter_page": "storage/20250107_143052_人工智能的发展趋势/reports/ppt/presenter.html",
    "pptx_file": "storage/20250107_143052_人工智能的发展趋势/reports/ppt/output.pptx",
    "conversion_stats": {
      "total": 10,
      "success": 10,
      "failed": 0,
      "elapsed_time": 45.2,
      "total_tokens": 1500
    },
    "status": "completed"
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-07T14:30:00"
}
```

**Python示例：**

```python
import requests
import json

url = "http://localhost:8000/api/v1/ppt/generate"
payload = {
    "topic": "人工智能的发展趋势",
    "style": "business",
    "slides": 10,
    "convert_to_pptx": True
}

response = requests.post(url, json=payload)
result = response.json()

if result['code'] == 200:
    print(f"项目ID: {result['data']['project_id']}")
    print(f"PPTX文件: {result['data']['pptx_file']}")
else:
    print(f"错误: {result['message']}")
```

---

#### 1.3 从大纲生成PPT ⭐ NEW

**接口地址：** `POST /api/v1/ppt/generate-from-outline`

**功能说明：** 接受结构化大纲数据（outline.json），生成HTML和PPTX格式的演示文稿。适合用户先编辑大纲，再生成PPT的场景。

**请求参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| outline | object | ✅ | - | PPT大纲数据（JSON格式） |
| style | string | ❌ | business | PPT风格 |
| include_speech_notes | boolean | ❌ | false | 是否包含演讲稿 |
| convert_to_pptx | boolean | ❌ | true | 是否转换为PPTX |
| custom_materials | string | ❌ | null | 自定义参考资料，支持文档解析、用户整理的资料、联网搜索结果等（最大10000字符） |

**outline 数据结构：**

```json
{
  "title": "PPT标题",
  "subtitle": "副标题（可选）",
  "colors": {
    "primary": "#1e3a8a",
    "accent": "#3b82f6",
    "background": "#ffffff",
    "text": "#1f2937",
    "secondary": "#6b7280"
  },
  "pages": [
    {
      "slide_number": 1,
      "page_type": "title",
      "title": "封面标题",
      "key_points": [],
      "has_image": true,
      "image_config": [{"type": "photo", "query": "关键词"}],
      "description": "页面描述"
    }
  ]
}
```

**page_type 选项：**
- `title` - 封面页
- `content` - 内容页
- `section` - 章节页
- `conclusion` - 总结页
- `chart` - 图表页

**请求示例：**

```bash
# 传入联网搜索结果或文档解析资料
curl -X POST "http://localhost:8000/api/v1/ppt/generate-from-outline" \
  -H "Content-Type: application/json" \
  -d '{
    "outline": {
      "title": "2024年全球气候变化报告",
      "subtitle": "数据分析与趋势预测",
      "colors": {
        "primary": "#2d6a4f",
        "accent": "#52b788",
        "background": "#ffffff",
        "text": "#1b4332",
        "secondary": "#74c69d"
      },
      "pages": [
        {
          "slide_number": 1,
          "page_type": "title",
          "title": "2024年全球气候变化报告",
          "key_points": [],
          "has_image": true,
          "image_config": [{"type": "photo", "query": "climate change earth"}],
          "description": "封面页"
        },
        {
          "slide_number": 2,
          "page_type": "content",
          "title": "全球气温上升趋势",
          "key_points": ["2024年平均气温", "温室气体排放", "极端天气事件"],
          "has_chart": true,
          "has_image": false,
          "description": "展示气温数据和趋势"
        }
      ]
    },
    "style": "academic",
    "custom_materials": "根据NASA和NOAA数据：2024年全球平均气温比工业化前水平上升1.3°C，接近《巴黎协定》1.5°C警戒线。极端天气事件增加20%，包括热浪、干旱和洪水。温室气体浓度达历史新高，CO2浓度突破420ppm。",
    "convert_to_pptx": true
  }'
```

```python
# Python示例：结合outline和自定义资料生成PPT
import requests
import json

url = "http://localhost:8000/api/v1/ppt/generate-from-outline"

# 准备大纲
outline = {
    "title": "产品技术白皮书",
    "subtitle": "创新架构设计",
    "colors": {
        "primary": "#4a90e2",
        "accent": "#50c878",
        "background": "#ffffff",
        "text": "#333333",
        "secondary": "#666666"
    },
    "pages": [
        {
            "slide_number": 1,
            "page_type": "title",
            "title": "产品技术白皮书",
            "key_points": [],
            "has_image": True,
            "image_config": [{"type": "photo", "query": "technology architecture"}],
            "description": "封面"
        },
        {
            "slide_number": 2,
            "page_type": "content",
            "title": "核心技术架构",
            "key_points": [
                "分布式系统设计",
                "微服务架构",
                "高可用性保障"
            ],
            "has_image": False,
            "description": "介绍核心架构"
        },
        {
            "slide_number": 3,
            "page_type": "content",
            "title": "性能优化方案",
            "key_points": [
                "缓存策略",
                "数据库优化",
                "CDN加速"
            ],
            "has_chart": True,
            "has_image": False,
            "description": "性能提升数据"
        }
    ]
}

# 从技术文档提取的详细资料
technical_materials = """
【性能测试结果】
1. 响应时间：平均50ms，比上一代提升60%
2. 吞吐量：支持10万QPS，峰值达15万QPS
3. 可用性：99.99% SLA保障，全年停机时间<53分钟
4. 扩展性：支持弹性伸缩，5分钟内从10节点扩展到100节点

【技术创新点】
- 自研分布式数据库，支持强一致性和最终一致性两种模式
- 智能负载均衡算法，根据实时流量自动调整路由策略
- 深度学习模型，实现智能预测和自动扩容
"""

payload = {
    "outline": outline,
    "style": "tech",
    "include_speech_notes": True,
    "custom_materials": technical_materials,
    "convert_to_pptx": True
}

response = requests.post(url, json=payload, timeout=300)
result = response.json()

if result['code'] == 200:
    print(f"✅ PPT生成成功！")
    print(f"   项目ID: {result['data']['project_id']}")
    print(f"   总页数: {result['data']['total_slides']}")
    print(f"   PPTX文件: {result['data']['pptx_file']}")
    print(f"   导航页: {result['data']['index_page']}")
else:
    print(f"❌ 生成失败: {result['message']}")
```

**响应示例：**

```json
{
  "code": 200,
  "message": "PPT生成成功",
  "data": {
    "project_id": "20250107_180000_人工智能的发展趋势",
    "ppt_dir": "storage/20250107_180000_人工智能的发展趋势/reports/ppt",
    "total_slides": 2,
    "index_page": "storage/20250107_180000_人工智能的发展趋势/reports/ppt/index.html",
    "presenter_page": "storage/20250107_180000_人工智能的发展趋势/reports/ppt/presenter.html",
    "pptx_file": "storage/20250107_180000_人工智能的发展趋势/reports/ppt/output.pptx",
    "status": "completed",
    "conversion_stats": {
      "total": 2,
      "success_count": 2,
      "failed": 0,
      "elapsed_time": 30.5
    }
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-07T18:00:00"
}
```

**使用场景：**

1. **预览后生成**：
   ```bash
   # 步骤1：生成大纲
   curl -X POST "http://localhost:8000/api/v1/ppt/outline" \
     -d '{"topic": "人工智能", "slides": 5}' \
     > outline.json

   # 步骤2：编辑outline.json（手动修改内容）

   # 步骤3：从outline生成PPT
   curl -X POST "http://localhost:8000/api/v1/ppt/generate-from-outline" \
     -d @outline.json
   ```

2. **自定义大纲**：
   ```python
   import requests
   import json

   # 定义自定义大纲
   custom_outline = {
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
               "image_config": [{"type": "photo", "query": "product launch technology"}],
               "description": "封面"
           },
           {
               "slide_number": 2,
               "page_type": "content",
               "title": "核心功能",
               "key_points": [
                   "智能识别",
                   "实时分析",
                   "云端同步"
               ],
               "has_chart": False,
               "has_image": False,
               "description": "产品三大核心功能"
           }
       ]
   }

   # 生成PPT
   url = "http://localhost:8000/api/v1/ppt/generate-from-outline"
   payload = {
       "outline": custom_outline,
       "style": "creative",
       "convert_to_pptx": True
   }

   response = requests.post(url, json=payload)
   result = response.json()

   if result['code'] == 200:
       print(f"项目ID: {result['data']['project_id']}")
       print(f"PPTX文件: {result['data']['pptx_file']}")
   ```

**Python完整示例：**

```python
import requests
import json
from pathlib import Path

def generate_ppt_from_outline(outline_file: str):
    """从outline文件生成PPT"""

    # 读取outline
    with open(outline_file, 'r', encoding='utf-8') as f:
        outline = json.load(f)

    # 调用API
    url = "http://localhost:8000/api/v1/ppt/generate-from-outline"
    payload = {
        "outline": outline,
        "style": "business",
        "include_speech_notes": False,
        "convert_to_pptx": True
    }

    response = requests.post(url, json=payload)
    result = response.json()

    if result['code'] == 200:
        project_id = result['data']['project_id']
        pptx_file = result['data']['pptx_file']

        print(f"✅ PPT生成成功！")
        print(f"   项目ID: {project_id}")
        print(f"   总页数: {result['data']['total_slides']}")
        print(f"   PPTX文件: {pptx_file}")

        # 下载PPTX
        download_url = f"http://localhost:8000/api/v1/ppt/{project_id}/download/pptx"
        download_response = requests.get(download_url)

        if download_response.status_code == 200:
            output_file = f"{project_id}.pptx"
            with open(output_file, 'wb') as f:
                f.write(download_response.content)
            print(f"   ✅ PPTX已下载: {output_file}")

        return project_id
    else:
        print(f"❌ 生成失败: {result['message']}")
        return None

# 使用示例
generate_ppt_from_outline("outline.json")
```

---

#### 1.4 查询项目状态

**接口地址：** `GET /api/v1/ppt/{project_id}/status`

**功能说明：** 查询指定项目的状态和文件列表。

**路径参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | string | ✅ | 项目ID（格式：timestamp_topic） |

**请求示例：**

```bash
curl -X GET "http://localhost:8000/api/v1/ppt/20250107_143052_人工智能的发展趋势/status"
```

**响应示例：**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "project_id": "20250107_143052_人工智能的发展趋势",
    "status": "completed",
    "created_at": "2025-01-07T14:30:00",
    "files": [
      "index.html",
      "presenter.html",
      "output.pptx",
      "slides/slide_01_cover.html"
    ]
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-07T14:30:00"
}
```

---

### 2. PPTX转换接口

#### 2.1 转换为PPTX

**接口地址：** `POST /api/v1/ppt/{project_id}/convert`

**功能说明：** 将已生成的HTML演示文稿转换为PPTX格式。

**路径参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | string | ✅ | 项目ID |

**请求参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| enable_llm_fix | boolean | ❌ | true | 是否启用LLM修复（已由配置管理） |

**请求示例：**

```bash
curl -X POST "http://localhost:8000/api/v1/ppt/20250107_143052_人工智能的发展趋势/convert" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**响应示例：**

```json
{
  "code": 200,
  "message": "PPTX转换成功",
  "data": {
    "status": "completed",
    "pptx_path": "storage/20250107_143052_人工智能的发展趋势/reports/ppt/output.pptx",
    "conversion_stats": {
      "total": 10,
      "success": 10,
      "failed": 0,
      "elapsed_time": 45.2
    }
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-07T14:30:00"
}
```

---

### 3. 文件下载接口

#### 3.1 下载文件

**接口地址：** `GET /api/v1/ppt/{project_id}/download/{file_type}`

**功能说明：** 下载PPT相关文件。

**路径参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | string | ✅ | 项目ID |
| file_type | string | ✅ | 文件类型 |

**file_type 选项：**
- `pptx` - 下载PPTX文件
- `html` - 下载HTML导航页
- `all` - 下载ZIP压缩包（包含所有文件）

**请求示例：**

```bash
# 下载PPTX文件
curl -X GET "http://localhost:8000/api/v1/ppt/20250107_143052_人工智能的发展趋势/download/pptx" \
  --output presentation.pptx

# 下载所有文件（ZIP）
curl -X GET "http://localhost:8000/api/v1/ppt/20250107_143052_人工智能的发展趋势/download/all" \
  --output presentation.zip
```

**响应：**
- `pptx`: 返回 `application/vnd.openxmlformats-officedocument.presentationml.presentation`
- `html`: 返回 `text/html`
- `all`: 返回 `application/zip`

---

### 4. 文件管理接口

#### 4.1 列出所有项目

**接口地址：** `GET /api/v1/files/list`

**功能说明：** 获取所有项目及其基本信息。

**请求示例：**

```bash
curl -X GET "http://localhost:8000/api/v1/files/list"
```

**响应示例：**

```json
{
  "code": 200,
  "message": "共找到 3 个项目",
  "data": {
    "total": 3,
    "projects": [
      {
        "project_id": "20250107_150000_人工智能的发展趋势",
        "path": "storage/20250107_150000_人工智能的发展趋势",
        "created_at": "2025-01-07T15:00:00",
        "status": "completed",
        "topic": "人工智能的发展趋势"
      },
      {
        "project_id": "20250107_140000_机器学习基础",
        "path": "storage/20250107_140000_机器学习基础",
        "created_at": "2025-01-07T14:00:00",
        "status": "completed",
        "topic": "机器学习基础"
      }
    ]
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-07T14:30:00"
}
```

---

#### 4.2 列出项目文件

**接口地址：** `GET /api/v1/files/{project_id}/files`

**功能说明：** 获取指定项目的所有文件列表。

**路径参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | string | ✅ | 项目ID |

**请求示例：**

```bash
curl -X GET "http://localhost:8000/api/v1/files/20250107_143052_人工智能的发展趋势/files"
```

**响应示例：**

```json
{
  "code": 200,
  "message": "共找到 15 个文件",
  "data": {
    "project_id": "20250107_143052_人工智能的发展趋势",
    "total": 15,
    "files": [
      {
        "name": "index.html",
        "path": "reports/ppt/index.html",
        "size": 2048,
        "type": ".html"
      },
      {
        "name": "output.pptx",
        "path": "reports/ppt/output.pptx",
        "size": 1048576,
        "type": ".pptx"
      }
    ]
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-07T14:30:00"
}
```

---

#### 4.3 删除项目

**接口地址：** `DELETE /api/v1/files/{project_id}`

**功能说明：** 删除指定项目及其所有文件（**危险操作，不可逆**）。

**路径参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | string | ✅ | 项目ID |

**请求示例：**

```bash
curl -X DELETE "http://localhost:8000/api/v1/files/20250107_143052_人工智能的发展趋势"
```

**响应示例：**

```json
{
  "code": 200,
  "message": "项目已删除，共删除 15 个文件",
  "data": {
    "project_id": "20250107_143052_人工智能的发展趋势",
    "deleted_files": 15
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-07T14:30:00"
}
```

---

### 5. 系统接口

#### 5.1 健康检查

**接口地址：** `GET /health`

**功能说明：** 检查API服务状态。

**请求示例：**

```bash
curl -X GET "http://localhost:8000/health"
```

**响应示例：**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600.5
}
```

---

## 📦 数据模型

### PPTStyle 枚举

支持的风格选项：

| 值 | 说明 |
|---|------|
| `business` | 商务风格 |
| `academic` | 学术风格 |
| `creative` | 创意风格 |
| `simple` | 简约风格 |
| `educational` | 教育风格 |
| `tech` | 科技风格 |
| `nature` | 自然风格 |
| `magazine` | 杂志风格 |
| `ted` | TED演讲风格 |

### 项目ID格式

项目ID格式：`{timestamp}_{topic}`

示例：`20250107_143052_人工智能的发展趋势`

### 文件存储结构

生成的PPT存储在 `storage/` 目录：

```
storage/
└── {timestamp}_{topic}/
    ├── metadata.json           # 项目元数据
    ├── intermediate/           # 中间处理结果
    ├── reports/
    │   └── ppt/
    │       ├── slides/         # HTML幻灯片
    │       │   ├── slide_01_cover.html
    │       │   ├── slide_02_content.html
    │       │   └── ...
    │       ├── index.html      # 导航页
    │       ├── presenter.html  # 演示模式页
    │       └── output.pptx     # PPTX文件
    └── search_results/         # 搜索结果
```

---

## ⚠️ 错误处理

### 错误响应格式

所有错误都返回统一的格式：

```json
{
  "code": 400,
  "message": "错误描述",
  "data": {
    "detail": "详细错误信息"
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-07T14:30:00"
}
```

### 常见错误

#### 1. 参数验证错误 (400)

```json
{
  "code": 400,
  "message": "参数验证失败",
  "data": {
    "detail": [
      {
        "loc": ["body", "topic"],
        "msg": "field required",
        "type": "value_error.missing"
      }
    ]
  }
}
```

#### 2. 项目不存在 (404)

```json
{
  "code": 404,
  "message": "项目不存在: 20250107_143052_不存在的主题",
  "data": null
}
```

#### 3. 服务器内部错误 (500)

```json
{
  "code": 500,
  "message": "PPT生成失败: LLM API调用超时",
  "data": null
}
```

---

## 📝 更新日志

### v1.1.0 (2025-01-07)
- ⭐ **新增**: 从大纲生成PPT接口 (`POST /api/v1/ppt/generate-from-outline`)
- ✅ 支持接受自定义outline.json生成PPT
- ✅ 支持用户编辑大纲后再生成
- ✅ 完整的Python和JavaScript示例代码
- ✅ 详细的outline数据结构说明

### v1.0.0 (2025-01-07)
- ✅ 初始版本发布
- ✅ 实现PPT生成接口
- ✅ 实现PPTX转换接口
- ✅ 实现文件下载接口
- ✅ 实现文件管理接口
- ✅ 统一响应格式
- ✅ 完整的错误处理

---

**文档维护**: AIPPT开发团队
**最后更新**: 2025-01-07
