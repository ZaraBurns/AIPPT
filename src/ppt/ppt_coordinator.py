"""
PPT - PPT
"""

import asyncio
import json
import random
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from loguru import logger
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


from ..llm.manager import LLMManager
from ..llm.prompts import PromptManager

from .multi_slide_generator import MultiSlidePPTGenerator, create_slide_data
from .design_coordinator import DesignCoordinator, DesignSpec
from ..tools.image_searcher import ImageSearcher


# ==========  ==========
class SlidePage(BaseModel):
    """PPT页面大纲"""
    slide_number: int = Field(description="幻灯片编号")
    page_type: str = Field(description="页面类型，如 title, content, section, conclusion, chart")
    title: str = Field(description="页面主题")
    key_points: List[str] = Field(description="关键要点列表")
    has_chart: bool = Field(default=False, description="是否包含图表")
    has_image: bool = Field(default=False, description="是否包含图片")
    description: Optional[str] = Field(default=None, description="页面描述")
    chart_config: Optional[Dict[str, Any]] = Field(default=None,description="图表配置")
    image_config: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(
        default=None, description="图片配置: {type: 'photo', query: '相关概念英文关键词'} 或列表"
    )

class PPTOutline(BaseModel):
    """PPT - """
    title: str = Field(description="PPT")
    subtitle: Optional[str] = Field(default=None, description="")
    colors: Dict[str, str] = Field(description="{primary, accent, background, text, secondary}")
    pages: List[SlidePage] = Field(description="幻灯片页面列表")
    # pages: List[Dict[str, Any]] = Field(
    #     description="{slide_number, page_type, title, key_points, has_chart, has_image, image_config}")

    @field_validator("pages", mode="before")
    @classmethod
    def _pages_must_be_list(cls, v: Any):
        # 兜底：模型经常把 list stringify 成 JSON 字符串
        if isinstance(v, str):
            s = v.strip()

            # 兼容 ```json ... ``` 包裹（有些模型会这样输出）
            if s.startswith("```"):
                s = s.strip("`").strip()
                if s.lower().startswith("json"):
                    s = s[4:].strip()

            return json.loads(s)
        return v
# ==========  ==========
class ColorScheme(BaseModel):
    """TODO: Add docstring."""
    primary: str = Field(description="#ff4757")
    accent: str = Field(description="")
    background: str = Field(description="")
    text: str = Field(description="")
    secondary: str = Field(description="")


class SlideDesign(BaseModel):
    """TODO: Add docstring."""
    layout_strategy: str = Field(description=": center_text|left_right_split|grid_cards|big_numbers|top_bottom|custom")
    visual_style: str = Field(description="''''''")
    color_usage: str = Field(description="'+''+'")


class SlideContent(BaseModel):
    """TODO: Add docstring."""
    title: Optional[str] = Field(default=None, description="")
    main_points: List[str] = Field(description="3-5")
    data_items: Optional[List[Dict[str, str]]] = Field(default=None, description="[{'label':'','value':'4850'}]")
    detail_text: Optional[str] = Field(default=None, description="")
    chart: Optional[Dict[str, Any]] = Field(default=None, description="typedata")


class Slide(BaseModel):
    """ - """
    slide_number: int = Field(description="")
    design: SlideDesign = Field(description="")
    content: SlideContent = Field(description="")


class PPTData(BaseModel):
    """PPT"""
    title: str = Field(description="PPT")
    subtitle: Optional[str] = Field(default=None, description="")
    colors: ColorScheme = Field(description="")
    slides: List[Slide] = Field(description="")


class PPTCoordinator:
    """PPT - PPT"""

    def __init__(
            self,
            llm_manager: LLMManager,
            prompt_manager: PromptManager
    ):
        self.llm_manager = llm_manager
        self.prompt_manager = prompt_manager
        self.name = "PPT"


        self.multi_slide_generator = MultiSlidePPTGenerator(llm_manager, prompt_manager)

        # 设计协调器 - 生成全局设计规范
        llm_client = llm_manager.get_client("design_coordinator")
        self.design_coordinator = DesignCoordinator(llm_client)

        # 图片搜索器 - 处理图片占位符
        self.image_searcher = ImageSearcher()

    async def generate_ppt_v2(
            self,
            topic: str,
            search_results: List[Dict[str, Any]],
            ppt_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PPT ()

        Phase 1: OutlineAgent
        Phase 2: NPageAgentHTML
        Phase 3: AssemblerAgentPPT
        """
        logger.info(f"[{self.name}] PPT: {topic}")

        try:
            style = ppt_config.get('style', 'business')
            slides = ppt_config.get('slides', 10)
            speech_notes = ppt_config.get('speech_notes') if ppt_config.get('speech_notes') else None  # 布尔值转换为None 

            # Phase 1: 
            logger.info(f"[{self.name}] Phase 1: PPT")
            outline = await self._generate_outline_v2(topic, search_results, style, slides)

            # Phase 2: HTML
            logger.info(f"[{self.name}] Phase 2: {len(outline['pages'])}")
            page_results = await self._parallel_generate_pages(
                outline=outline,
                search_results=search_results,
                style=style,
                speech_scene=speech_notes  #
            )

            # Phase 3: PPT
            logger.info(f"[{self.name}] Phase 3: PPT")
            html_content = self._assemble_ppt_v2(outline, page_results)

            # 
            speech_notes_data = None
            if speech_notes:
                speech_notes_data = []
                for page in page_results:
                    if "speech_notes" in page:
                        speech_notes_data.append({
                            "slide_number": page["slide_number"],
                            "speech_notes": page["speech_notes"]
                        })

            result = {
                "status": "success",
                "ppt": {
                    "title": outline['title'],
                    "subtitle": outline.get('subtitle', ''),
                    "colors": outline['colors'],
                    "slides": page_results,  # html_contentspeech_notes
                    "metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "style": style,
                        "slide_count": len(page_results),
                        "has_speech_notes": bool(speech_notes)
                    }
                },
                "html_content": html_content
            }

            # 
            if speech_notes_data:
                result["speech_notes"] = speech_notes_data

            return result

        except Exception as e:
            logger.error(f"[{self.name}] PPT: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }

    async def generate_ppt_v3(
            self,
            topic: str,
            search_results: List[Dict[str, Any]],
            ppt_config: Dict[str, Any],
            output_dir: Path,
            custom_content_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成多页HTML PPT (新架构 V3)

        使用多页HTML架构，每张幻灯片是独立的HTML文件
        复用V2的PageAgent来生成详细内容

        Args:
            topic: PPT主题
            search_results: 搜索结果
            ppt_config: PPT配置
                {
                    'style': 'ted/business/academic/creative/simple',
                    'slides': 10,
                    'theme': 'default/blue/red/green/purple'
                }
            output_dir: 输出目录
            custom_content_summary: 自定义内容摘要（联网数据），如果提供则使用此数据而非search_results

        Returns:
            {
                "status": "success/error",
                "ppt_dir": "PPT目录路径",
                "total_slides": 10,
                "slide_files": [...],
                "index_page": "导航页路径",
                "presenter_page": "演示模式页路径"
            }
        """
        logger.info(f"[{self.name}] 生成多页HTML PPT (V3): {topic}")
        logger.info(f"[{self.name}] PPT配置: {ppt_config}")

        try:
            style = ppt_config.get('style', 'business')
            slides_count = ppt_config.get('slides', 10)
            theme = ppt_config.get('theme', 'default')

            # Phase 1: 生成大纲
            logger.info(f"[{self.name}] Phase 1: 生成PPT大纲 (目标{slides_count}页)")
            print(f"\n📋 正在生成PPT大纲... (目标: {slides_count}页)")
            outline = await self._generate_outline_v2(
                topic,
                search_results,
                style,
                slides_count,
                custom_content_summary=custom_content_summary
            )
            print(f"✅ 大纲生成完成！实际生成 {len(outline['pages'])} 页")

            # Phase 1.2: 基于大纲搜索图片并将URL嵌入到大纲中 (NEW - 修改策略)
            logger.info(f"[{self.name}] Phase 1.2: 搜索图片并将URL嵌入到大纲")
            print(f"\n🔍 正在搜索图片并嵌入到大纲...")
            image_count = await self._search_and_record_images(outline)
            print(f"✅ 图片搜索完成！成功嵌入 {image_count} 张图片URL到大纲")

            # Phase 1.5: 生成全局设计规范 (NEW)
            logger.info(f"[{self.name}] Phase 1.5: 生成全局设计规范")
            print(f"\n🎨 正在生成全局设计规范...")
            design_spec = await self.design_coordinator.generate_design_spec(
                topic=topic,
                outline=outline,
                style=style
            )
            logger.info(f"[{self.name}] 设计规范: {design_spec.layout_style}风格, 主色{design_spec.primary_color}")
            print(f"✅ 设计规范生成完成！风格: {design_spec.layout_style}, 主色: {design_spec.primary_color}")

            # Phase 2: 使用PageAgent生成每页的详细HTML内容 (复用V2逻辑)
            total_pages = len(outline['pages'])
            logger.info(f"[{self.name}] Phase 2: 生成每页详细内容 ({total_pages} 页)")
            print(f"\n📄 正在并行生成 {total_pages} 页内容...")
            print(f"   提示: 大模型正在思考中，这可能需要几分钟时间...")
            page_results = await self._parallel_generate_pages(
                outline=outline,
                search_results=search_results,
                style=style,
                speech_scene=None,  # V3不需要演讲稿
                design_spec=design_spec,  # 传递全局设计规范
                custom_content_summary=custom_content_summary  # 传递自定义联网数据
            )
            # 过滤掉page_results中没有生成内容的页面
            # success_count = sum(1 for r in page_results if r.get('html_content'))
            # print(f"✅ 页面内容生成完成！成功: {success_count}/{total_pages} 页")

            # Phase 3: 将页面内容转换为幻灯片数据结构
            logger.info(f"[{self.name}] Phase 3: 构建幻灯片数据")
            print(f"\n🔧 正在构建幻灯片数据结构...")
            slides_data = self._convert_pages_to_slides_data(outline, page_results)
            print(f"✅ 数据结构构建完成！")

            # Phase 4: 使用MultiSlidePPTGenerator生成多页HTML PPT文件
            logger.info(f"[{self.name}] Phase 4: 生成多页HTML文件")
            print(f"\n📦 正在生成多页HTML文件和导航页面...")
            result = await self.multi_slide_generator.generate_ppt(
                slides_data=slides_data,
                ppt_config={
                    'ppt_title': outline['title'],
                    'subtitle': outline.get('subtitle', ''),
                    'colors': outline['colors'],
                    'style': style,
                    'theme': design_spec.primary_color,
                    'author': 'XunLong AI',
                    'date': datetime.now().strftime('%Y-%m-%d')
                },
                output_dir=output_dir,
                outline=outline  # 保存大纲
            )
            # 添加outline和图片搜索记录
            result['ppt_outline'] = outline

            # 统计成功嵌入的图片数量
            embedded_image_count = sum(1 for page in outline.get('pages', [])
                                       for img in
                                       (page.get('image_data', []) if isinstance(page.get('image_data'), list) else [])
                                       if img.get('success', False))
            logger.info(f"[{self.name}] 多页HTML PPT生成完成")
            print(f"✅ PPT生成完成！")
            print(f"\n🎉 生成成功！")
            print(f"   📁 PPT目录: {result.get('ppt_dir')}")
            print(f"   📄 总页数: {result.get('total_slides')}")
            print(f"   🖼️ 嵌入图片: {embedded_image_count} 张")
            print(f"   🏠 导航页: {result.get('index_page')}")
            print(f"   🎬 演示页: {result.get('presenter_page')}")
            return result

        except Exception as e:
            logger.error(f"[{self.name}] 生成多页HTML PPT失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }

    def _convert_outline_to_slides_data(
            self,
            outline: Dict[str, Any],
            search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        将大纲转换为幻灯片数据

        Args:
            outline: PPT大纲
            search_results: 搜索结果用于填充内容

        Returns:
            幻灯片数据列表
        """
        slides_data = []
        content_summary = self._summarize_search_results(search_results)

        for i, page in enumerate(outline['pages']):
            page_type = page.get('page_type', 'content')

            # 映射page_type到slide_type
            type_mapping = {
                'title': 'cover',
                'content': 'content',
                'section': 'content',
                'conclusion': 'summary',
                'chart': 'chart'
            }

            slide_type = type_mapping.get(page_type, 'content')

            # 构建幻灯片数据
            slide_data = {
                'slide_number': page['slide_number'],
                'type': slide_type,
                'title': page.get('title', ''),
                'template': self._get_template_for_type(slide_type)
            }

            # 根据类型添加内容
            if slide_type == 'cover':
                slide_data['content'] = {
                    'title': outline['title'],
                    'subtitle': outline.get('subtitle', ''),
                    'author': 'XunLong AI',
                    'date': datetime.now().strftime('%Y-%m-%d')
                }

            elif slide_type == 'toc':
                # 生成目录
                sections = []
                content_pages = [p for p in outline['pages'] if p.get('page_type') in ['section', 'content']]
                for idx, p in enumerate(content_pages[:6], 1):  # 最多6个章节
                    sections.append({
                        'number': idx,
                        'title': p.get('title', ''),
                        'subtitle': ', '.join(p.get('key_points', [])[:2]) if p.get('key_points') else ''
                    })
                slide_data['content'] = {'sections': sections}

            elif slide_type == 'content':
                # 内容页
                key_points = page.get('key_points', [])
                slide_data['content'] = {
                    'title': page.get('title', ''),
                    'layout': 'bullets' if len(key_points) > 0 else 'paragraph',
                    'points': key_points,
                    'details': content_summary[:500] if content_summary else ''
                }

            elif slide_type == 'chart':
                # 图表页
                slide_data['content'] = {
                    'title': page.get('title', ''),
                    'chart_type': 'bar',
                    'categories': ['2022', '2023', '2024', '2025'],
                    'data': [100, 150, 200, 250],
                    'series_name': '数据趋势',
                    'y_axis_name': '数值'
                }

            elif slide_type == 'summary':
                # 总结页
                points = page.get('key_points', [])
                slide_data['content'] = {
                    'title': '总结',
                    'points': [{'text': p, 'icon': 'check'} for p in points] if points else [
                        {'text': '感谢观看', 'icon': 'heart'}
                    ],
                    'closing': '谢谢！'
                }

            slides_data.append(slide_data)

        return slides_data

    def _convert_pages_to_slides_data(
            self,
            outline: Dict[str, Any],
            page_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        将PageAgent生成的页面HTML转换为幻灯片数据

        Args:
            outline: PPT大纲
            page_results: PageAgent生成的页面列表，每页包含html_content

        Returns:
            幻灯片数据列表
        """
        slides_data = []

        for i, page in enumerate(page_results):
            slide_number = page.get('slide_number', i + 1)
            html_content = page.get('html_content', '')

            # 从outline获取页面类型和标题
            outline_page = outline['pages'][i] if i < len(outline['pages']) else {}
            page_type = outline_page.get('page_type', 'content')
            topic = outline_page.get('title', f'Slide {slide_number}')

            # 映射page_type到slide_type
            type_mapping = {
                'title': 'cover',
                'content': 'content',
                'section': 'content',
                'conclusion': 'summary',
                'chart': 'chart'
            }
            slide_type = type_mapping.get(page_type, 'content')

            # 构建幻灯片数据
            slide_data = {
                'slide_number': slide_number,
                'type': slide_type,
                'title': topic,
                'template': self._get_template_for_type(slide_type),
                # 将PageAgent生成的HTML内容直接存储
                'html_content': html_content
            }

            slides_data.append(slide_data)

        return slides_data

    def _get_template_for_type(self, slide_type: str) -> str:
        """根据幻灯片类型返回模板名称"""
        template_mapping = {
            'cover': 'slide_cover.html',
            'toc': 'slide_toc.html',
            'content': 'slide_content.html',
            'chart': 'slide_chart.html',
            'summary': 'slide_summary.html'
        }
        return template_mapping.get(slide_type, 'slide_content.html')

    async def generate_ppt(
            self,
            topic: str,
            search_results: List[Dict[str, Any]],
            ppt_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PPT

        Args:
            topic: PPT
            search_results: 
            ppt_config: PPT
                {
                    'style': 'ted/business/academic/creative/simple',
                    'slides': 10,
                    'depth': 'surface/medium/deep',
                    'theme': 'default/blue/red/green/purple'
                }

        Returns:
            {
                "status": "success/error",
                "ppt": {
                    "title": "PPT",
                    "subtitle": "",
                    "slides": [...],
                    "metadata": {...}
                },
                "html_content": "HTMLPPT"
            }
        """

        logger.info(f"[{self.name}] PPT: {topic}")
        logger.info(f"[{self.name}] PPT: {ppt_config}")

        try:
            style = ppt_config.get('style', 'business')
            logger.info(f"[{self.name}] : {style}")
            slides = ppt_config.get('slides', 10)
            depth = ppt_config.get('depth', 'medium')
            theme = ppt_config.get('theme', 'default')

            # Phase 1: 
            logger.info(f"[{self.name}] Phase 1: PPT")
            template_info = self._load_template_info(style)

            # Phase 2: LLMPPT
            logger.info(f"[{self.name}] Phase 2: PPT")
            ppt_data = await self._generate_ppt_with_template(
                topic=topic,
                style=style,
                slides=slides,
                depth=depth,
                theme=theme,
                template_info=template_info,
                search_results=search_results
            )

            # Phase 3: HTML
            logger.info(f"[{self.name}] Phase 3: HTML")
            html_content = await self._convert_to_html(ppt_data, style, theme)

            logger.info(f"[{self.name}] PPT")

            return {
                "status": "success",
                "ppt": ppt_data,
                "html_content": html_content
            }

        except Exception as e:
            logger.error(f"[{self.name}] PPT: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _load_template_info(self, style: str) -> Dict[str, Any]:
        """加载模板信息，包括模板内容和元数据

        Args:
            style: 模板样式名称（如 'business', 'academic', 'red' 等）

        Returns:
            包含模板结构、元数据等信息的字典

        Raises:
            FileNotFoundError: 当指定模板和默认模板都不存在时
        """
        from pathlib import Path
        import re

        template_dir = Path(__file__).parent.parent.parent.parent / 'templates' / 'html' / 'ppt'
        template_file = template_dir / f"{style}.html"

        if not template_file.exists():
            logger.warning(f"模板 {style}.html 不存在于 {template_dir}，回退到默认模板 business.html")
            template_file = template_dir / "business.html"

            if not template_file.exists():
                raise FileNotFoundError(
                    f"默认模板 business.html 也不存在: {template_dir}\n"
                    f"请确保模板目录包含至少一个有效的 HTML 模板文件"
                )

        logger.info(f"加载模板: {template_file.name}")
        # 读取模板内容
        template_content = template_file.read_text(encoding='utf-8')

        # 
        metadata_match = re.search(r'<!-- METADATA: ({.*?}) -->', template_content)
        metadata = {}
        if metadata_match:
            import json
            metadata = json.loads(metadata_match.group(1))

        # 200
        template_lines = template_content.split('\n')[:200]
        template_structure = '\n'.join(template_lines)

        return {
            "style": style,
            "name": metadata.get("name", style),
            "description": metadata.get("description", ""),
            "template_structure": template_structure,
            "metadata": metadata
        }

    async def _generate_ppt_with_template(
            self,
            topic: str,
            style: str,
            slides: int,
            depth: str,
            theme: str,
            template_info: Dict[str, Any],
            search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """PPT"""

        # 
        content_summary = self._summarize_search_results(search_results)

        # 
        system_prompt = self._build_template_aware_system_prompt(template_info, style, depth)
        user_prompt = self._build_template_aware_user_prompt(
            topic, slides, content_summary, template_info
        )

        # 
        from ..llm.client import LLMClient

        # LLM
        llm_client = self.llm_manager.get_client("outline_generator")

        # 
        ppt_result = await llm_client.get_structured_response(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_model=PPTData
        )

        # 
        ppt_data = ppt_result.model_dump()

        # 
        ppt_data["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "style": style,
            "theme": theme,
            "slide_count": len(ppt_data.get("slides", [])),
            "depth": depth
        }

        logger.info(f"[{self.name}] PPT {len(ppt_data['slides'])} ")

        return ppt_data

    def _summarize_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """
        汇总搜索结果为文本格式

        将搜索引擎返回的结果列表转换为格式化的文本摘要，用于后续的PPT内容生成。
        每个搜索结果包含标题、URL和内容摘要，按照统一格式进行组织。

        Args:
            search_results (List[Dict[str, Any]]): 搜索结果列表，每个元素包含:
                - title (str): 搜索结果标题
                - content (str): 搜索结果内容
                - url (str): 搜索结果URL

        Returns:
            str: 格式化后的搜索结果摘要文本，包含编号、标题、URL和内容片段
        """
        # 存储格式化后的搜索结果片段
        summary_parts = []

        # 遍历前15个搜索结果（限制数量以控制输出长度）
        for i, result in enumerate(search_results[:15], 1):  # 最多处理15个结果
            # 提取搜索结果的基本信息
            title = result.get("title", "")  # 获取标题，默认为空字符串
            content = result.get("content", "")[:800]  # 获取内容前800字符，避免过长
            url = result.get("url", "")  # 获取URL链接，
            # 按照统一格式组织每个搜索结果
            # 格式：序号+标题 -> URL -> 内容摘要 -> 分隔线
            summary_parts.append(f"""{i}. {title}
            链接: {url}
            内容: {content}...
            ---""")

        # 将所有格式化的结果用双换行符连接，形成最终的摘要文本
        return "\n\n".join(summary_parts)

    def _build_template_aware_system_prompt(
            self,
            template_info: Dict[str, Any],
            style: str,
            depth: str
    ) -> str:
        """TODO: Add docstring."""

        style_guides = {
            "red": """REDPPT

RED
- ****1-3
- ****3-8
- ****
- ****
- ****minimal - 

****
- ****#ff4757, #ee5a6f, #e84118
- #2d3436, #1e272e, #c23616
- 

****
1. **main_points**3-8
2. **detail_text**20
3. 3
4. 5-12


- title: "AI"
- main_points: ["", "90%", ""]
- detail_text: "GPT-3GPT-5"
""",
            "business": """PPT


- ****3-5
- ****
- ****
- ****
- ****detailed - 

****
- ****#1e3a8a, #2563eb, #3b82f6
- #60a5fa, #93c5fd
- #ffffff

****
1. **main_points**15-25
2. **detail_text******50-150
   - "50""35%"
   - "2025Q3""20258"
   - /"OpenAIGPT-4""MetaLlama"
   - "20233"
3. ****data_itemsmain_points + detail_text
4. data_items

****
```json
{{
  "title": "AI",
  "main_points": [
    "35.2%",
    "20231809",
    ""
  ],
  "detail_text": "Precedence ResearchAI2025562030361OpenAIGoogleAnthropic70%OpenAIChatGPT220221342.83288%"
}}
```

****
```json
{{
  "title": "",
  "main_points": [],  //  Businessmain_points
  "data_items": [{{"label": "", "value": "50"}}],  //  
  "detail_text": null  //  detail_text
}}
```
""",
            "academic": """PPT

- ****
- ****
- ****
- ****detailed - 


- ""
- 
""",
            "creative": """PPT

- ****
- ****
- ****
- ****medium - 
""",
            "simple": """PPT

- ****idea
- ****
- ****minimal - 
"""
        }

        template_desc = template_info.get("description", "")
        style_guide = style_guides.get(style, style_guides["business"])

        # 
        color_guides = {
            "red": """
RED- ****
- primary****#ff4757, #ee5a6f, #e84118, #c23616
- accent#2d3436, #1e272e, #c23616
- background#ffffff#f8f9fa
- text#2d3436
- secondary#636e72

****RED
""",
            "business": """
- ****
- primary****#1e3a8a, #2563eb, #3b82f6, #1d4ed8
- accent#60a5fa, #93c5fd
- background#ffffff
- text#1f2937
- secondary#6b7280

****PPT
- /AI#3b82f6, #6366f1
- +#1e3a8a, #f59e0b
- /****#f97316, #dc2626
- #0ea5e9, #14b8a6
- #3b82f6, #fb923c
""",
            "academic": """

- primary#0f172a, #065f46, #1e3a8a
- accent#f59e0b, #ea580c
- background#ffffff
- text#000000
- secondary#4b5563
""",
            "creative": """

- primary#a855f7, #ec4899, #f43f5e
- accent#06b6d4, #10b981
- background#fafafa
- text#18181b
- secondary#71717a
""",
            "simple": """

- primary#18181b, #0f172a
- accent#52525b, #64748b
- background#ffffff
- text#000000
- secondary#a1a1aa
"""
        }

        color_guide = color_guides.get(style, color_guides["business"])

        return f"""{style_guide}

# 
- {template_info.get("name")}
- {template_desc}

# 
{color_guide}

****PPT
- 
- 
- /
- 
- 
- 

# 

PPT********HTML

JSONPPT
- title: PPT
- subtitle: 
- colors:  {{
    "primary": "#hex",
    "accent": "#hex",
    "background": "#hex",
    "text": "#hex",
    "secondary": "#hex"
  }}
- slides: slide
  - slide_number: 
  - design:  {{
      "layout_strategy": "center_text|left_right_split|grid_cards|big_numbers|top_bottom|title_page|bullets|custom",
      "visual_style": "''/''/''/''/''",
      "color_usage": "'+''+'''"
    }}
  - content:  {{
      "title": "",
      "main_points": ["1", "2", "3"],
      "data_items": [
        {{"label": "", "value": ""}},  // 
        ...
      ],
      "detail_text": "",  // 
      "chart": {{  // 
        "type": "bar/line/pie/area",
        "data": {{
          "labels": ["2022", "2023", "2025"],
          "datasets": [
            {{"label": "", "data": [141, 294, 495]}}
          ]
        }},
        "title": ""
      }}
    }}

****
1. ****design""content""
2. ****
   - title_page: 
   - center_text: 
   - left_right_split: 
   - grid_cards: 
   - big_numbers: 
   - top_bottom: +
   - bullets: 
   - custom: visual_style
3. ****"3"
4. ****
5. ****data_items[{{"label":"","value":"4850"}}]
6. REDBusinessCreative
"""

    def _build_template_aware_user_prompt(
            self,
            topic: str,
            slides: int,
            content_summary: str,
            template_info: Dict[str, Any]
    ) -> str:
        """TODO: Add docstring."""

        return f"""{template_info.get('name')}PPT

# 
{topic}

# 
{slides}

# 
{content_summary}

# 
1. **{template_info.get('name')}**
2. 1layout_strategy: title_page
3. 1
4. layout_strategy: center_text

5. ****
   - RED****primary#ff4757
   - Business
     * /AI#3b82f6, #6366f1
     * /#f97316, #dc2626
     * +#1e3a8a, #f59e0b
     * #0ea5e9, #14b8a6
   - Creative#a855f7, #ec4899

6. ****
   - Business/Academic
   - evidence
   - RED/Simple

7. ****
   - RED/Simple:
     * 1-3main_points
     * 3-8
     * detail_text20
   - Business:
     * **3-5main_points**
     * **detail_text**50-150
     * data_itemsmain_points + detail_text
   - Academic:
     * 3-4main_points
     * detail_text80-150

****

JSON

**RED**
```json
{{
  "title": "AI",
  "subtitle": "",
  "colors": {{
    "primary": "#ff4757",  // 
    "accent": "#2d3436",
    "background": "#ffffff",
    "text": "#2d3436",
    "secondary": "#636e72"
  }},
  "slides": [
    {{
      "slide_number": 1,
      "design": {{"layout_strategy": "title_page", "visual_style": "", "color_usage": "+"}},
      "content": {{"title": "AI", "main_points": [], "detail_text": ""}}
    }},
    {{
      "slide_number": 2,
      "design": {{"layout_strategy": "bullets", "visual_style": "", "color_usage": "+"}},
      "content": {{"title": "", "main_points": ["", "90%", ""], "detail_text": "GPT-3GPT-5"}}
    }}
  ]
}}
```

**Business**
```json
{{
  "title": "2025",
  "subtitle": "",
  "colors": {{
    "primary": "#f97316",  // 
    "accent": "#fb923c",
    "background": "#ffffff",
    "text": "#1f2937",
    "secondary": "#6b7280"
  }},
  "slides": [
    {{
      "slide_number": 1,
      "design": {{"layout_strategy": "title_page", "visual_style": "", "color_usage": "+"}},
      "content": {{"title": "2025", "main_points": [], "detail_text": ""}}
    }},
    {{
      "slide_number": 2,
      "design": {{"layout_strategy": "bullets", "visual_style": "", "color_usage": "+"}},
      "content": {{
        "title": "",
        "main_points": [
          "2025485033.8%",
          "202630%+",
          "B65%C45%",
          "C40%"
        ],
        "detail_text": "2025"
      }}
    }},
    {{
      "slide_number": 3,
      "design": {{"layout_strategy": "bullets", "visual_style": "", "color_usage": "+"}},
      "content": {{
        "title": "",
        "main_points": [
          "2022-2025",
          "30%",
          "2026"
        ],
        "chart": {{
          "type": "bar",
          "data": {{
            "labels": ["2022", "2023", "2025", "2025E", "2026E"],
            "datasets": [
              {{"label": "", "data": [3200, 4100, 4850, 6500, 10000]}}
            ]
          }},
          "title": ""
        }},
        "detail_text": ""
      }}
    }}
  ]
}}
```

****
- ****RED
- **Businessmain_points**3-5detail_text
- **REDmain_points**3-8detail_text
- **visual_style**"+"
  * 2
  * 3
  * 4
  * 5
  * 6
  * 
- ****
  *   line
  *   bar
  *   pie
  * 2-3
"""

    async def _parallel_generate_slides(
            self,
            slide_outlines: List[Dict[str, Any]],
            style: str,
            available_content: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """TODO: Add docstring."""

        logger.info(f"[{self.name}]  {len(slide_outlines)} ")

        tasks = []
        for i, slide_outline in enumerate(slide_outlines):
            # 
            context = {}
            if i > 0:
                context["previous_slide"] = slide_outlines[i - 1]

            task = self.slide_content_generator.generate_slide_content(
                slide_outline=slide_outline,
                style=style,
                available_content=available_content,
                context=context
            )
            tasks.append(task)

        # 
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 
        slides_content = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[{self.name}]  {i + 1} : {result}")
                # fallback
                slides_content.append({
                    "slide_number": i + 1,
                    "type": slide_outlines[i].get("type", "content"),
                    "title": slide_outlines[i].get("title", ""),
                    "subtitle": "",
                    "content": {
                        "points": [""],
                        "details": {},
                        "visuals": []
                    }
                })
            else:
                slides_content.append(result)

        logger.info(f"[{self.name}] ")
        return slides_content

    def _assemble_ppt(
            self,
            outline: Dict[str, Any],
            slides_content: List[Dict[str, Any]],
            topic: str,
            style: str,
            theme: str
    ) -> Dict[str, Any]:
        """PPT"""

        logger.info(f"[{self.name}] PPT")

        # 
        slides_sorted = sorted(slides_content, key=lambda x: x.get("slide_number", 0))

        ppt_data = {
            "title": outline.get("title", topic),
            "subtitle": outline.get("subtitle", ""),
            "slides": slides_sorted,
            "metadata": {
                "topic": topic,
                "style": style,
                "theme": theme,
                "slide_count": len(slides_sorted),
                "generated_at": datetime.now().isoformat(),
                "generator": "XunLong PPT Generator"
            }
        }

        logger.info(f"[{self.name}] PPT {len(slides_sorted)} ")

        return ppt_data



    def _get_css_component_guide(self) -> str:
        """CSS"""
        return """# 可用CSS工具类
- 文本: .text-xs/.text-xl/.text-5xl/.text-9xl, .font-bold/.font-black, .text-center
- 颜色: .text-primary/.text-white, .bg-primary/.bg-white/.gradient-primary
- 布局: .flex/.flex-col/.flex-1, .items-center/.justify-center, .grid/.grid-cols-2/.grid-cols-3
- 间距: .gap-4/.gap-8/.gap-16, .p-8/.p-16, .mt-4/.mb-8
- 装饰: .rounded-xl, .shadow-lg, .border-l-4, .card
- 动画: .animate-fadeIn/.animate-slideUp
- 尺寸: .w-full/.w-1\\/2, .h-full/.h-64/.h-80/.h-96"""

    async def _generate_slide_html(
            self,
            slide_data: Dict[str, Any],
            colors: Dict[str, str],
            css_guide: str,
            style: str
    ) -> str:
        """LLMHTML"""

        design = slide_data.get('design', {})
        content = slide_data.get('content', {})

        prompt = f"""HTML

# 
- : {design.get('layout_strategy', 'bullets')}
- : {design.get('visual_style', '')}
- : {design.get('color_usage', '')}

# 
- : {content.get('title', '')}
- : {content.get('main_points', [])}
- : {content.get('data_items', [])}
- : {content.get('detail_text', '')}

# 
{colors}

{css_guide}

****
1. visual_styleHTML
2. FlexGridCSS
3. PPT{style}
4. HTMLdiv<html>/<body>
5. ****

HTML
"""

        # LLMHTML
        llm_client = self.llm_manager.get_client("outline_generator")

        response = await llm_client.get_completion(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.8  # 
        )

        # HTML
        html = response.strip()
        # markdown
        if html.startswith('```html'):
            html = html[7:]
        if html.startswith('```'):
            html = html[3:]
        if html.endswith('```'):
            html = html[:-3]

        return html.strip()

    def _build_html_from_slides(
            self,
            ppt_data: Dict[str, Any],
            rendered_slides: List[Dict[str, str]]
    ) -> str:
        """flexible.htmlHTML"""
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path

        # 
        template_dir = Path(__file__).parent.parent.parent.parent / 'templates' / 'html' / 'ppt'
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template('flexible.html')

        # 
        render_data = {
            'title': ppt_data.get('title', ''),
            'subtitle': ppt_data.get('subtitle', ''),
            'colors': ppt_data.get('colors', {}),
            'slides': rendered_slides,
            'metadata': ppt_data.get('metadata', {}),
            'generated_at': ppt_data.get('metadata', {}).get('generated_at', ''),
            'generator': 'XunLong PPT Generator'
        }

        # HTML
        html = template.render(**render_data)
        return html

    def _get_fallback_html(self, ppt_data: Dict[str, Any]) -> str:
        """fallback HTML"""
        slides_html = []
        for slide in ppt_data.get("slides", []):
            slides_html.append(f"""
<div class="slide">
    <h2>{slide.get('title', '')}</h2>
    <ul>
        {''.join(f'<li>{p}</li>' for p in slide.get('content', {}).get('points', []))}
    </ul>
</div>
""")

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{ppt_data.get('title', '')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        .slide {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; }}
        h2 {{ color: #333; }}
    </style>
</head>
<body>
    <h1>{ppt_data.get('title', '')}</h1>
    {''.join(slides_html)}
</body>
</html>
"""

    async def _generate_outline_v2(
            self,
            topic: str,
            search_results: List[Dict[str, Any]],
            style: str,
            slides: int,
            custom_content_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Phase 1: 生成PPT大纲

        Args:
            topic: PPT主题
            search_results: 搜索结果列表
            style: PPT风格
            slides: 幻灯片数量
            custom_content_summary: 自定义内容摘要（联网数据），如果提供则使用此数据而非search_results

        Returns:
            PPT大纲字典
        """
        # 如果提供了custom_content_summary，直接使用；否则从search_results生成
        if custom_content_summary is not None:
            content_summary = custom_content_summary
            from loguru import logger
            logger.info(f"📊 使用自定义联网数据 ({len(content_summary)} 字符)")
        else:
            content_summary = self._summarize_search_results(search_results)
        with open("src/prompt/outline_prompt.txt", "r", encoding="utf-8") as f:
            outline_prompt = f.read()

        outline_prompt = outline_prompt.replace("{slides}", str(slides))

        prompt = f"""作为ppt大纲撰写专家，根据用户需求，生成一个**结构清晰、内容创意、专业严谨、格式规范的JSON格式PPT大纲，并根据指定的 JSON 模式格式化它们。

        # 主题：{topic}
        # 风格：{style}
        # 目标页数slides：**{slides}**
        # 可用资料：
        {content_summary}
        
        ### 📋【PPT大纲生成规则】：
        {outline_prompt}
"""

        llm_client = self.llm_manager.get_client("outline_generator")

        # 
        outline_result = await llm_client.get_structured_response(
            prompt=prompt,
            response_model=PPTOutline
        )

        outline = outline_result.model_dump()
        # 过滤掉None的pages，确保数据完整性
        outline['pages'] = [page for page in outline['pages'] if page is not None]
        return outline

    async def _parallel_generate_pages(
            self,
            outline: Dict[str, Any],
            search_results: List[Dict[str, Any]],
            style: str,
            speech_scene: Optional[str] = None,
            design_spec: Optional[DesignSpec] = None,  # 新增: 全局设计规范
            custom_content_summary: Optional[str] = None  # 新增: 自定义联网数据
    ) -> List[Dict[str, Any]]:
        """
        Phase 2: HTML页面并行生成

        使用PageAgent并行生成每页的HTML内容

        Args:
            outline: PPT大纲
            search_results: 搜索结果列表
            style: PPT风格
            speech_scene: 演讲场景
            design_spec: 全局设计规范
            custom_content_summary: 自定义内容摘要（联网数据），如果提供则使用此数据而非search_results

        Returns:
            页面生成结果列表
        """
        from .page_agent import PageAgent, PageSpec, GlobalContext

        # 构建全局上下文 - 如果有design_spec则使用它，否则使用outline的colors
        colors_to_use = outline['colors']
        if design_spec:
            # 使用设计规范的配色方案
            colors_to_use = {
                'primary': design_spec.primary_color,
                'secondary': design_spec.secondary_color,
                'accent': design_spec.accent_color,
                'background': design_spec.background_color,
                'text': design_spec.text_color,
                'text_secondary': design_spec.text_secondary_color
            }

        global_context = GlobalContext(
            ppt_title=outline['title'],
            style=style,
            colors=colors_to_use,
            total_slides=len(outline['pages']),
            speech_scene=speech_scene  #
        )

        # 如果提供了custom_content_summary，直接使用；否则从search_results生成
        if custom_content_summary is not None:
            content_summary = custom_content_summary
            logger.info(f"📊 使用自定义联网数据生成HTML内容 ({len(content_summary)} 字符)")
        else:
            content_summary = self._summarize_search_results(search_results)

        # 构建CSS指南 - 如果有design_spec，则包含设计规范信息
        css_guide = self._get_css_component_guide()
        if design_spec:
            css_guide += f"""

# 全局设计规范 (IMPORTANT - 必须严格遵守!)
**配色方案:**
- 主色: {design_spec.primary_color}
- 次色: {design_spec.secondary_color}
- 强调色: {design_spec.accent_color}
- 背景色: {design_spec.background_color}
- 文字色: {design_spec.text_color}
- 次要文字色: {design_spec.text_secondary_color}

**字体规范:**
- 字体: {design_spec.font_family}
- 标题字号: {design_spec.title_font_size}
- 正文字号: {design_spec.content_font_size}

**视觉风格:**
- 布局风格: {design_spec.layout_style}
- 间距: {design_spec.spacing}
- 圆角: {design_spec.border_radius}
- 阴影: {'启用' if design_spec.use_shadows else '禁用'}
- 渐变: {'启用' if design_spec.use_gradients else '禁用'}
- 动画: {design_spec.animation_style}

**图表配色 (Chart.js使用):**
{design_spec.chart_colors}

**重要提示:**
所有页面必须使用以上统一的设计规范！不得自行更改颜色、字体或风格！
"""

        # PageAgent
        llm_client = self.llm_manager.get_client("content_generator")
        page_agent = PageAgent(llm_client, css_guide)

        # 添加信号量限制并发
        semaphore = asyncio.Semaphore(3)

        async def generate_with_limit(page_spec):
            async with semaphore:
                # 添加随机延迟（0.5-2秒）
                await asyncio.sleep(random.uniform(0.5, 2.0))

                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        return await page_agent.generate_page_html(
                            page_spec=page_spec,
                            global_context=global_context,
                            content_data=content_summary
                        )
                    except Exception as e:
                        if "429" in str(e) or "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                            wait_time = (2 ** attempt) + random.uniform(0, 1)  # 指数退避 + 随机
                            logger.warning(f"限流错误，重试 {attempt + 1}/{max_retries}，等待 {wait_time:.2f} 秒")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise  # 非限流错误，直接抛出

        # 修改任务创建
        tasks = [generate_with_limit(PageSpec(**page_outline)) for page_outline in outline['pages']]

        #
        logger.info(f"[{self.name}] 并行生成{len(tasks)}个页面...")

        # 使用进度显示的方式并行生成
        total = len(tasks)
        print(f"   [0/{total}] 开始生成...")

        page_results = await asyncio.gather(*tasks, return_exceptions=True)

        #
        results = []
        success = 0
        failed = 0

        for i, result in enumerate(page_results):
            if isinstance(result, Exception) or result is None:
                failed += 1
                logger.error(f"[{self.name}] {i + 1}: {result}")
                print(f"   ❌ 第{i + 1}页生成失败: {str(result)[:50]}")
                # fallback
                results.append({
                    "slide_number": i + 1,
                    "html_content": f"<div class='flex items-center justify-center h-full'><p class='text-2xl'></p></div>",
                    "speech_notes": None
                })
            else:
                success += 1
                results.append(result)

                # 每完成一页就输出进度
                print(f"   ✓ [{success}/{total}] 第{i + 1}页生成完成")

        print(f"\n   📊 生成统计: 成功 {success} 页, 失败 {failed} 页")
        return results

    def _assemble_ppt_v2(
            self,
            outline: Dict[str, Any],
            page_htmls: List[Dict[str, Any]]
    ) -> str:
        """
        Phase 3: PPT

        HTMLflexible.html
        """
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path

        # 
        template_dir = Path(__file__).parent.parent.parent.parent / 'templates' / 'html' / 'ppt'
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template('flexible.html')

        # slidesflexible.html
        slides = []
        for page in page_htmls:
            slides.append({
                'slide_number': page['slide_number'],
                'html_content': page['html_content'],
                'custom_style': ''  # 
            })

        # HTML
        html = template.render(
            title=outline['title'],
            subtitle=outline.get('subtitle', ''),
            colors=outline['colors'],
            slides=slides,
            metadata={'generated_at': datetime.now().isoformat()}
        )

        return html

    def get_status(self) -> Dict[str, Any]:
        """TODO: Add docstring."""
        return {
            "name": self.name,
            "agents": {
                "outline_generator": self.outline_generator.name,
                "slide_content_generator": self.slide_content_generator.name
            }
        }

    async def _search_and_record_images(self, outline: Dict[str, Any]) -> int:
        """
        基于大纲中的图片配置搜索图片，并将图片URL直接嵌入到大纲的对应页面中

        Args:
            outline: PPT大纲，包含每页的image_config配置
                    该函数会直接修改outline，在每个需要图片的page中添加 image_data 字段

        Returns:
            成功搜索到图片的数量

        修改策略：
        - 将搜索到的图片信息直接添加到 outline['pages'][i]['image_data'] 中
        - image_data 包含: url, alt, source, photographer, width, height, color 等
        - LLM生成HTML时可以直接使用这些图片URL，无需占位符
        """
        try:
            logger.info(f"[{self.name}] 开始基于大纲搜索图片并嵌入URL")

            # 检查图片搜索器是否可用
            if not self.image_searcher.is_available():
                logger.warning(f"[{self.name}] 图片搜索器不可用，跳过图片搜索")
                return 0

            # 提取需要图片的页面配置（同时保留页面在大纲中的索引）
            pages_with_images = []
            for idx, page in enumerate(outline.get('pages', [])):
                if page.get('has_image') and 'image_config' in page:
                    image_config = page['image_config']
                    # 支持 image_config 为列表或字典
                    if isinstance(image_config, list):
                        image_configs = image_config
                    elif isinstance(image_config, dict):
                        image_configs = [image_config]
                    else:
                        logger.warning(f"[{self.name}] 第 {page.get('slide_number')} 页 image_config 格式无效")
                        continue
                    pages_with_images.append({
                        'page_index': idx,  # 保存页面索引，用于后续更新大纲
                        'slide_number': page.get('slide_number'),
                        'image_configs': image_configs,
                        'title': page.get('title', ''),
                    })

            logger.info(f"[{self.name}] 找到 {len(pages_with_images)} 页需要搜索图片")

            if not pages_with_images:
                return 0

            # 并行搜索所有页面的图片
            search_tasks = []
            for page_info in pages_with_images:
                task = self._search_images_for_page(page_info)
                search_tasks.append(task)

            # 等待所有搜索完成
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # 将搜索结果嵌入到大纲中
            success_count = 0
            for i, result in enumerate(search_results):
                page_index = pages_with_images[i]['page_index']
                slide_number = pages_with_images[i]['slide_number']

                if isinstance(result, Exception):
                    logger.error(f"[{self.name}] 第 {slide_number} 页图片搜索出错: {result}")
                    # 标记图片搜索失败
                    outline['pages'][page_index]['image_data'] = [{
                        'success': False,
                        'error': str(result),
                        'search_timestamp': datetime.now().isoformat()
                    }]
                elif isinstance(result, list):
                    # 将图片数据列表嵌入到大纲中
                    outline['pages'][page_index]['image_data'] = result
                    success_count += sum(1 for r in result if r.get('success'))
                    logger.info(f"[{self.name}] 第 {slide_number} 页嵌入 {len(result)} 张图片")
                else:
                    logger.error(f"[{self.name}] 第 {slide_number} 页搜索结果格式错误")
                    outline['pages'][page_index]['image_data'] = [{
                        'success': False,
                        'error': 'Invalid result format',
                        'search_timestamp': datetime.now().isoformat()
                    }]

            logger.info(f"[{self.name}] 图片搜索完成，成功 {success_count} 张")
            return success_count

        except Exception as e:
            logger.error(f"[{self.name}] 图片搜索过程出错: {e}")
            import traceback
            traceback.print_exc()
            return 0

    async def _search_images_for_page(self, page_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        为单个页面搜索图片

        Args:
            page_info: 页面信息，包含slide_number, image_configs, title

        Returns:
            图片搜索记录列表
        """
        slide_number = page_info['slide_number']
        image_configs = page_info['image_configs']
        search_results = []

        logger.info(f"[{self.name}] 搜索第 {slide_number} 页图片，配置: {image_configs}")

        try:
            # 并行搜索所有图片配置
            search_tasks = []
            for image_config in image_configs:
                query = image_config.get('query', '')
                task = self._search_single_image(slide_number, query, image_config)
                search_tasks.append(task)

            # 等待所有搜索完成
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # 过滤成功的搜索结果
            successful_results = [r for r in search_results if isinstance(r, dict) and r.get('success')]

            if not successful_results:
                raise ValueError(f"第 {slide_number} 页未找到相关图片")

            return successful_results

        except Exception as e:
            logger.error(f"[{self.name}] 第 {slide_number} 页图片搜索失败: {e}")
            return [{
                "slide_number": slide_number,
                "url": None,
                "alt": None,
                "source": None,
                "image_id": None,
                "photographer": None,
                "photographer_url": None,
                "width": None,
                "height": None,
                "color": None,
                "search_timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }]

    async def _search_single_image(self, slide_number: int, query: str, image_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        搜索单个图片

        Args:
            slide_number: 幻灯片编号
            query: 图片搜索关键词
            image_config: 图片配置

        Returns:
            图片搜索记录
        """
        logger.info(f"[{self.name}] 搜索第 {slide_number} 张图片，关键词: {query}")

        try:
            if not query:
                raise ValueError(f"第 {slide_number} 页缺少图片搜索关键词")

            # 搜索图片
            images = await self.image_searcher.search_images(
                query=query,
                count=1,  # 只需要一张图片
                orientation="landscape"  # 横向图片适合PPT
            )

            if not images:
                raise ValueError(f"未找到关键词 '{query}' 的相关图片")

            image = images[0]
            image_url = image.get('url') or image.get('download_url')

            if not image_url:
                raise ValueError("图片URL为空")

            # 构建搜索记录
            record = {
                "slide_number": slide_number,
                "search_query": query,
                "url": image_url,
                "alt": image.get('alt', query),
                "source": image.get('source', 'unknown'),
                "image_id": image.get('id'),
                "photographer": image.get('photographer'),
                "photographer_url": image.get('photographer_url'),
                "width": image.get('width'),
                "height": image.get('height'),
                "color": image.get('color') or image.get('avg_color'),
                "search_timestamp": datetime.now().isoformat(),
                "success": True,
            }

            logger.info(f"[{self.name}] 第 {slide_number} 张图片搜索成功: {image_url}")
            return record

        except Exception as e:
            logger.error(f"[{self.name}] 第 {slide_number} 张图片搜索失败: {e}")
            return {
                "slide_number": slide_number,
                "search_query": query,
                "url": None,
                "alt": None,
                "source": None,
                "image_id": None,
                "photographer": None,
                "photographer_url": None,
                "width": None,
                "height": None,
                "color": None,
                "search_timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }

    async def generate_ppt_from_outline(
        self,
        outline: Dict[str, Any],
        ppt_config: Dict[str, Any],
        output_dir: Path,
        custom_content_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        基于已有大纲生成PPT（跳过大纲生成步骤）

        Args:
            outline: 用户提供的结构化大纲
            ppt_config: PPT配置
            output_dir: 输出目录
            custom_content_summary: 自定义内容摘要（联网数据），用于生成HTML内容

        Returns:
            生成结果字典
        """
        logger.info(f"[{self.name}] 基于已有大纲生成PPT")
        print(f"\n📝 正在基于已有大纲生成PPT...")
        print(f"   标题: {outline.get('title', 'Unknown')}")
        print(f"   页数: {len(outline.get('pages', []))}")

        try:
            style = ppt_config.get('style', 'business')
            speech_notes = ppt_config.get('speech_notes')

            # 转换speech_notes为speech_scene（布尔值转字符串/None）
            speech_scene = None
            if speech_notes is True:
                speech_scene = "speech"  # 或使用其他适当的字符串
            # False 或 None 时保持 None

            # Phase 1: 跳过大纲生成，使用用户提供的大纲
            logger.info(f"[{self.name}] Phase 1: 使用用户提供的大纲")

            # Phase 1.2: 如果大纲中没有图片数据，则搜索图片
            image_count = 0
            if not any('image_data' in page for page in outline.get('pages', [])):
                logger.info(f"[{self.name}] Phase 1.2: 搜索图片并嵌入到大纲")
                print(f"\n🔍 正在搜索图片...")
                image_count = await self._search_and_record_images(outline)
                print(f"✅ 图片搜索完成！嵌入 {image_count} 张图片")
            else:
                # 统计已有的图片
                image_count = sum(
                    1 for page in outline.get('pages', [])
                    for img in (page.get('image_data', []) if isinstance(page.get('image_data'), list) else [])
                    if img.get('success', False)
                )
                print(f"✅ 大纲已包含 {image_count} 张图片")

            # Phase 1.5: 生成全局设计规范
            logger.info(f"[{self.name}] Phase 1.5: 生成全局设计规范")
            print(f"\n🎨 正在生成全局设计规范...")
            design_spec = await self.design_coordinator.generate_design_spec(
                topic=outline.get('title', 'Untitled'),
                outline=outline,
                style=style
            )
            logger.info(f"[{self.name}] 设计规范: {design_spec.layout_style}风格, 主色{design_spec.primary_color}")
            print(f"✅ 设计规范生成完成！风格: {design_spec.layout_style}, 主色: {design_spec.primary_color}")

            # Phase 2: 生成页面HTML
            logger.info(f"[{self.name}] Phase 2: 生成每页详细内容 ({len(outline.get('pages', []))} 页)")
            print(f"\n📄 正在并行生成 {len(outline.get('pages', []))} 页内容...")
            print(f"   提示: 大模型正在思考中，这可能需要几分钟时间...")

            page_results = await self._parallel_generate_pages(
                outline=outline,
                search_results=[],  # 从大纲生成时不需要搜索结果
                style=style,
                speech_scene=speech_scene,  # 使用转换后的speech_scene
                design_spec=design_spec,
                custom_content_summary=custom_content_summary  # 传递自定义联网数据
            )

            success_count = sum(1 for r in page_results if r.get('html_content'))
            print(f"✅ 页面内容生成完成！成功: {success_count}/{len(outline.get('pages', []))} 页")

            # Phase 3: 将页面内容转换为幻灯片数据结构
            logger.info(f"[{self.name}] Phase 3: 构建幻灯片数据")
            print(f"\n🔧 正在构建幻灯片数据结构...")
            slides_data = self._convert_pages_to_slides_data(outline, page_results)
            print(f"✅ 数据结构构建完成！")

            # Phase 4: 使用MultiSlidePPTGenerator生成多页HTML PPT文件
            logger.info(f"[{self.name}] Phase 4: 生成多页HTML文件")
            print(f"\n📦 正在生成多页HTML文件和导航页面...")
            result = await self.multi_slide_generator.generate_ppt(
                slides_data=slides_data,
                ppt_config={
                    'ppt_title': outline['title'],
                    'subtitle': outline.get('subtitle', ''),
                    'colors': outline['colors'],
                    'style': style,
                    'theme': design_spec.primary_color,
                    'author': 'XunLong AI',
                    'date': datetime.now().strftime('%Y-%m-%d')
                },
                output_dir=output_dir,
                outline=outline  # 保存大纲
            )

            # 添加outline和图片搜索记录
            result['ppt_outline'] = outline

            logger.info(f"[{self.name}] PPT生成完成")
            print(f"\n🎉 生成成功！")
            print(f"   📁 PPT目录: {result.get('ppt_dir')}")
            print(f"   📄 总页数: {result.get('total_slides')}")
            print(f"   🖼️ 嵌入图片: {image_count} 张")
            print(f"   🏠 导航页: {result.get('index_page')}")
            print(f"   🎬 演示页: {result.get('presenter_page')}")

            return result

        except Exception as e:
            logger.error(f"[{self.name}] 基于大纲生成PPT失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }

    def _convert_pages_to_slides_data(
        self,
        outline: Dict[str, Any],
        page_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        将页面结果转换为幻灯片数据

        Args:
            outline: PPT大纲
            page_results: 页面生成结果

        Returns:
            幻灯片数据列表
        """
        slides_data = []

        for i, (page_outline, page_result) in enumerate(zip(outline.get('pages', []), page_results)):
            slide_data = {
                'slide_number': page_outline.get('slide_number', i + 1),
                'page_type': page_outline.get('page_type', 'content'),
                'title': page_outline.get('title', ''),
                'html_content': page_result.get('html_content', ''),
                'key_points': page_outline.get('key_points', []),
                'has_chart': page_outline.get('has_chart', False),
                'chart_config': page_outline.get('chart_config'),
                'has_image': page_outline.get('has_image', False),
                'image_config': page_outline.get('image_config'),
                'image_data': page_outline.get('image_data', []),
                'description': page_outline.get('description', '')
            }
            slides_data.append(slide_data)

        return slides_data
