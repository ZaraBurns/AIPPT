"""
PageAgent - PPT

PageAgentPPTHTML
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, field_validator
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class PageSpec(BaseModel):
    """ - """
    slide_number: int = Field(description="")
    page_type: str = Field(description=": title/content/section/conclusion")
    title: Optional[str] = Field(default=None, description="")
    key_points: list[str] = Field(default=[], description="")
    has_chart: bool = Field(default=False, description=""),
    has_image: bool = Field(default=False, description="是否需要配图")  # 新增
    image_config: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(
        default=None, description="图片配置: {type: 'photo', query: '相关概念英文关键词'} 或列表"
    )
    image_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(
        default=None, description="检索到的图片数据: {success: bool, url: str, alt: str, photographer: str, ...} 或列表"
    )
    description: Optional[str] = Field(default=None, description="此页说明")
    chart_config: Optional[Dict[str, Any]] = Field(
        default=None, description="图表配置"
    )

    @field_validator('title', mode='before')
    @classmethod
    def set_title_from_topic(cls, v, info):
        if v is None:
            # 如果title为空，尝试从topic获取
            topic = info.data.get('topic')
            if topic:
                return topic
        return v


class GlobalContext(BaseModel):
    """ - PageAgent"""
    ppt_title: str = Field(description="PPT")
    style: str = Field(description=": ted/business/academic/creative/simple")
    colors: Dict[str, str] = Field(description="")
    total_slides: int = Field(description="")
    speech_scene: Optional[str] = Field(default=None, description="")


class PageAgent:
    """PPT"""

    def __init__(self, llm_client, css_guide: str):
        """
        PageAgent

        Args:
            llm_client: LLM
            css_guide: CSS
        """
        self.llm_client = llm_client
        self.css_guide = css_guide
        # 从样式文件加载 page_agent 风格提示，便于统一管理
        self.style_guides = self._load_style_guides()

    async def generate_page_html(
            self,
            page_spec: PageSpec,
            global_context: GlobalContext,
            content_data: str
    ) -> Dict[str, str]:
        """
        HTML

        Args:
            page_spec: 
            global_context: 
            content_data: 

        Returns:
            
            - html_content: HTMLdiv
            - speech_notes: 
        """
        # 构建prompt（包含图片占位符指令）
        prompt = self._build_prompt(page_spec, global_context, content_data)

        logger.info(f"[PageAgent] {page_spec.slide_number}: {page_spec.title}")

        with open("src/prompt/htmlprompt.txt", "r", encoding="utf-8") as f:
            layout_hints = f.read()
        response = await self.llm_client.chat_completion(
            messages=[
                {"role": "system", "content": layout_hints},
                {"role": "user", "content": prompt}
            ],
            temperature=0, # 结构化输出稳定
            max_tokens=4000,
        )

        # 清理LLM输出：去除描述性文本和代码块标记
        html = response.get("content", "").strip()

        # 1. 查找第一个HTML标签的位置
        import re

        # 查找第一个 < 开始的HTML标签
        first_tag_match = re.search(r'<[a-zA-Z!]', html)
        if first_tag_match:
            # 去除HTML之前的所有描述性文本
            html = html[first_tag_match.start():]

        # 2. 去除markdown代码块标记
        if html.startswith('```html'):
            html = html[7:]
        if html.startswith('```'):
            html = html[3:]
        if html.endswith('```'):
            html = html[:-3]

        # 3. 再次清理可能的前置文本
        html = html.strip()
        first_tag_match = re.search(r'<[a-zA-Z!]', html)
        if first_tag_match and first_tag_match.start() > 0:
            html = html[first_tag_match.start():]

        result = {"html_content": html.strip()}

        # 
        if global_context.speech_scene:
            speech_notes = await self._generate_speech_notes(
                page_spec, global_context, content_data, html
            )
            result["speech_notes"] = speech_notes

        return result

    def _build_prompt(
            self,
            page_spec: PageSpec,
            global_context: GlobalContext,
            content_data: str
    ) -> str:
        """TODO: Add docstring."""

        # page_type

        # 根据风格加载样式提示（从 ppt_styles.json 的 page_agent 部分）
        style_hint = self.style_guides.get(global_context.style, global_context.style)
        return f"""
## **核心任务**

根据用户对幻灯片内容的描述，生成一份符合所有严格约束条件的 HTML 代码。布局均匀，清晰美观，优美专业，符合国际一流咨询公司的视觉设计标准。

### 任务
为PPT第{page_spec.slide_number}页生成完整的HTML代码

### 全局信息
- PPT标题: {global_context.ppt_title}
- 风格: {global_context.style}
- 配色: {global_context.colors}
- 总页数: {global_context.total_slides}
- 语言：简体中文

### 本页信息
{page_spec}

### 风格要求
{style_hint}

"""

    def _load_style_guides(self) -> Dict[str, str]:
        """从 `ppt_styles.json` 中加载 page_agent 的风格提示"""
        try:
            style_file = Path(__file__).parent.parent / 'prompt' / 'ppt_styles.json'
            with open(style_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result: Dict[str, str] = {}
                styles_section = data.get("styles", {})
                if isinstance(styles_section, dict):
                    for style_name, cfg in styles_section.items():
                        if isinstance(cfg, dict) and "page_agent" in cfg:
                            result[style_name] = cfg.get("page_agent", "")
                return result
        except Exception as e:
            logger.error(f"[PageAgent] 加载风格指南失败: {e}")
            return {}

    def _format_image_data(self, page_spec: PageSpec) -> str:
        """
        格式化图片数据，生成清晰的图片使用说明

        Args:
            page_spec: 页面规格，包含 image_data

        Returns:
            格式化后的图片信息字符串
        """
        if not page_spec.image_data:
            return "本页无图片素材"

        image_data = page_spec.image_data

        # 检查是否为列表（多图）或字典（单图）
        if isinstance(image_data, list):
            # 多图情况
            if not image_data:
                return "本页无图片素材"

            image_infos = []
            for i, img_data in enumerate(image_data, 1):
                if not img_data.get('success', False):
                    error_msg = img_data.get('error', '未知错误')
                    image_infos.append(f"**图片 {i}**: 搜索失败 - {error_msg}")
                    continue

                url = img_data.get('url', '')
                alt = img_data.get('alt', '')
                photographer = img_data.get('photographer', '未知')
                source = img_data.get('source', 'unknown')
                width = img_data.get('width', 'auto')
                height = img_data.get('height', 'auto')
                color = img_data.get('color', '#000000')

                image_info = f"""
**图片 {i}:**

📷 **图片URL**: {url}

📝 **图片描述**: {alt}

👤 **摄影师**: {photographer}

🔗 **来源**: {source}

📐 **尺寸**: {width} x {height}

🎨 **主色调**: {color}
"""
                image_infos.append(image_info)

            all_images_info = "\n".join(image_infos)

            usage_guide = f"""

**已为本页检索到 {len(image_data)} 张图片素材，请直接在HTML中使用：**

{all_images_info}

**使用方法**:
1. 直接在 `<img>` 标签的 `src` 属性中使用上述 URL
2. 在 `alt` 属性中使用上述描述
3. 根据页面布局设置图片的 width、height 和 object-fit 样式
4. 建议使用 object-fit: cover 保持图片比例

**多图布局示例**:
```html
<div class="images-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
    {"".join([f'<div class="image-item"><img src="{img.get("url", "")}" alt="{img.get("alt", "")}" style="width: 100%; height: 200px; object-fit: cover;" /></div>' for img in image_data if img.get('success')])}
</div>
```

**注意事项**:
- ✅ 直接使用提供的URL，不要修改
- ✅ 图片已经过筛选，符合页面主题
- ✅ 根据页面风格调整图片的展示样式
- ❌ 不要使用占位符，必须使用提供的真实图片URL
"""
            return usage_guide

        else:
            # 单图情况（字典）
            if not image_data.get('success', False):
                error_msg = image_data.get('error', '未知错误')
                return f"图片搜索失败: {error_msg}\n建议: 使用纯文字内容或默认占位符"

            url = image_data.get('url', '')
            alt = image_data.get('alt', '')
            photographer = image_data.get('photographer', '未知')
            source = image_data.get('source', 'unknown')
            width = image_data.get('width', 'auto')
            height = image_data.get('height', 'auto')
            color = image_data.get('color', '#000000')

            image_info = f"""
**已为本页检索到图片素材，请直接在HTML中使用：**

📷 **图片URL**: {url}

📝 **图片描述**: {alt}

👤 **摄影师**: {photographer}

🔗 **来源**: {source}

📐 **尺寸**: {width} x {height}

🎨 **主色调**: {color}

**使用方法**:
1. 直接在 `<img>` 标签的 `src` 属性中使用上述 URL
2. 在 `alt` 属性中使用上述描述
3. 根据页面布局设置图片的 width、height 和 object-fit 样式
4. 建议使用 object-fit: cover 保持图片比例

**示例代码**:
```html
<div class="image-container" style="width: 100%; height: 400px; overflow: hidden; border-radius: 12px;">
    <img src="{url}"
         alt="{alt}"
         style="width: 100%; height: 100%; object-fit: cover; display: block;" />
</div>
```

**注意事项**:
- ✅ 直接使用提供的URL，不要修改
- ✅ 图片已经过筛选，符合页面主题
- ✅ 根据页面风格调整图片的展示样式
- ❌ 不要使用占位符，必须使用提供的真实图片URL
"""
            return image_info

    async def _generate_speech_notes(
            self,
            page_spec: PageSpec,
            global_context: GlobalContext,
            content_data: str,
            html_content: str
    ) -> str:
        """
        

        Args:
            page_spec: 
            global_context: 
            content_data: 
            html_content: HTML

        Returns:
            
        """
        prompt = f"""PPT{page_spec.slide_number}

# 
{global_context.speech_scene}

# PPT
- PPT: {global_context.ppt_title}
- : {page_spec.slide_number}/{global_context.total_slides}
- : {page_spec.page_type}

# 
- : {page_spec.title}
- : {page_spec.key_points}

# 
{html_content[:500]}  # HTML

# 
1. **{global_context.speech_scene}**
2. 
   - title(): 
   - section(): 
   - content(): 
   - conclusion(): 
3. 150-300
4. 
5. 
6. ****


"""

        logger.info(f"[PageAgent] {page_spec.slide_number}")

        response = await self.llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7  # 
        )

        speech_notes = response.get("content", "").strip()

        return speech_notes
