"""
布局生成器 - 为PPT页面生成多样化的布局要求

LayoutGenerator

功能：
1. 根据页面特征（类型、图表、图片等）智能选择布局
2. 生成详细的布局指令，嵌入到提示词中
3. 确保同一PPT中布局不重复、有变化
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import random


class LayoutType(Enum):
    """布局类型枚举"""
    # 封面和目录类
    TITLE_PAGE = "title_page"                      # 封面页
    TOC_PAGE = "toc_page"                          # 目录页
    SECTION_PAGE = "section_page"                  # 章节分隔页

    # 内容页布局
    TWO_COLUMN_STANDARD = "two_column_standard"    # 标准两栏：左文右图
    TWO_COLUMN_REVERSED = "two_column_reversed"    # 反向两栏：左图右文
    TWO_COLUMN_BALANCED = "two_column_balanced"    # 均衡两栏：左右等分

    VERTICAL_SPLIT_TOP = "vertical_split_top"      # 上下分割：上图下文
    VERTICAL_SPLIT_BOTTOM = "vertical_split_bottom"# 上下分割：上文下图

    THREE_COLUMN = "three_column"                  # 三栏布局
    CARD_GRID_2X2 = "card_grid_2x2"                # 2x2卡片网格
    CARD_GRID_3X2 = "card_grid_3x2"                # 3x2卡片网格

    FULL_CHART = "full_chart"                      # 全屏图表（带少量说明）
    FOCUS_HIGHLIGHT = "focus_highlight"            # 重点突出布局

    COMPARISON = "comparison"                      # 对比布局（左右对比）
    TIMELINE = "timeline"                          # 时间线布局

    LIST_LAYOUT = "list_layout"                    # 列表布局（垂直列表）


class LayoutTemplate:
    """布局模板类"""

    def __init__(
        self,
        layout_type: LayoutType,
        name: str,
        description: str,
        structure_hint: str,
        applicable_types: List[str],
        require_chart: bool = None,
        require_image: bool = None,
        priority: int = 0
    ):
        """
        Args:
            layout_type: 布局类型
            name: 布局名称
            description: 布局描述（用于提示词）
            structure_hint: 结构提示（具体的HTML结构建议）
            applicable_types: 适用的页面类型列表
            require_chart: 是否必须有图表（None=不限制，True=必须有，False=必须没有）
            require_image: 是否必须有图片（None=不限制，True=必须有，False=必须没有）
            priority: 优先级（数字越大越优先）
        """
        self.layout_type = layout_type
        self.name = name
        self.description = description
        self.structure_hint = structure_hint
        self.applicable_types = applicable_types
        self.require_chart = require_chart
        self.require_image = require_image
        self.priority = priority


class LayoutGenerator:
    """布局生成器"""

    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: 随机种子（用于可复现的布局选择）
        """
        if seed is not None:
            random.seed(seed)

        self.templates = self._init_templates()
        self.used_layouts: Dict[str, List[LayoutType]] = {}  # 记录每个PPT已使用的布局

    def _init_templates(self) -> List[LayoutTemplate]:
        """初始化所有布局模板"""
        return [
            # ========== 封面和目录类 ==========
            LayoutTemplate(
                layout_type=LayoutType.TITLE_PAGE,
                name="封面页布局",
                description="居中的标题布局，大标题居中，副标题和关键信息在下方排列",
                structure_hint="""
<main data-layout="title-page" class="flex-grow flex flex-col items-center justify-center">
    <h1 data-role="title" class="text-6xl font-bold text-center">主标题</h1>
    <div data-role="decoration" class="w-32 h-1 bg-primary mt-6"></div>
    <p data-role="subtitle" class="text-2xl text-center mt-8">副标题或关键信息</p>
    <div data-role="metrics" class="flex gap-8 mt-12">
        <div class="text-center">
            <p class="text-4xl font-bold">数据1</p>
            <p class="text-sm">标签1</p>
        </div>
        <div class="text-center">
            <p class="text-4xl font-bold">数据2</p>
            <p class="text-sm">标签2</p>
        </div>
    </div>
</main>
""",
                applicable_types=["title"],
                require_chart=False,
                require_image=False,
                priority=100
            ),

            LayoutTemplate(
                layout_type=LayoutType.TOC_PAGE,
                name="目录页布局",
                description="两栏目录布局，展示章节列表，每项包含序号、标题和简介",
                structure_hint="""
<main data-layout="toc-page" class="flex-grow flex gap-8">
    <div class="flex-1 flex flex-col gap-6">
        <div data-role="toc-item" class="flex items-start gap-4 p-6 rounded-xl">
            <div data-role="decoration" class="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0">
                <span class="text-white text-xl font-bold">1</span>
            </div>
            <div>
                <h3 data-role="title" class="text-2xl font-bold">章节标题</h3>
                <p data-role="description" class="text-base mt-2">章节简介</p>
            </div>
        </div>
        <!-- 更多章节... -->
    </div>
    <div class="flex-1 flex flex-col gap-6">
        <!-- 右栏章节... -->
    </div>
</main>
""",
                applicable_types=["section", "toc"],
                require_chart=False,
                require_image=False,
                priority=100
            ),

            LayoutTemplate(
                layout_type=LayoutType.SECTION_PAGE,
                name="章节分隔页",
                description="大标题居中，简短的章节介绍，少量关键点",
                structure_hint="""
<main data-layout="section-page" class="flex-grow flex flex-col items-center justify-center">
    <div data-role="decoration" class="w-20 h-20 rounded-2xl flex items-center justify-center mb-8">
        <span class="text-4xl">图标</span>
    </div>
    <h1 data-role="title" class="text-6xl font-bold text-center">章节标题</h1>
    <div data-role="decoration" class="w-48 h-1 bg-primary mt-6"></div>
    <p data-role="description" class="text-xl text-center mt-8 max-w-3xl">章节简介</p>
</main>
""",
                applicable_types=["section"],
                require_chart=False,
                require_image=False,
                priority=90
            ),

            # ========== 标准内容页 ==========
            LayoutTemplate(
                layout_type=LayoutType.TWO_COLUMN_STANDARD,
                name="标准两栏布局（左文右图）",
                description="左侧40%为文字内容区（标题、要点、说明），右侧60%为图表或图片",
                structure_hint="""
<main data-layout="two-column-standard" class="flex-grow flex gap-10">
    <div data-role="text-content" class="flex-1 flex flex-col gap-6">
        <h2 data-role="title" class="text-3xl font-bold">标题</h2>
        <p data-role="description" class="text-lg leading-relaxed">介绍文字</p>
        <div class="flex flex-col gap-4">
            <div class="flex items-start gap-3">
                <div data-role="decoration" class="w-2 h-2 rounded-full mt-2 flex-shrink-0"></div>
                <p>要点1</p>
            </div>
            <!-- 更多要点... -->
        </div>
    </div>
    <div data-role="chart-area" class="flex-1">
        <div class="placeholder h-full">
            <canvas id="chart"></canvas>
        </div>
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=None,
                require_image=None,
                priority=50
            ),

            LayoutTemplate(
                layout_type=LayoutType.TWO_COLUMN_REVERSED,
                name="反向两栏布局（左图右文）",
                description="左侧60%为图表或图片，右侧40%为文字内容区（标题、要点、说明）",
                structure_hint="""
<main data-layout="two-column-reversed" class="flex-grow flex gap-10">
    <div data-role="chart-area" class="flex-1">
        <div class="placeholder h-full">
            <canvas id="chart"></canvas>
        </div>
    </div>
    <div data-role="text-content" class="flex-1 flex flex-col gap-6">
        <h2 data-role="title" class="text-3xl font-bold">标题</h2>
        <p data-role="description" class="text-lg leading-relaxed">介绍文字</p>
        <div class="flex flex-col gap-4">
            <div class="flex items-start gap-3">
                <div data-role="decoration" class="w-2 h-2 rounded-full mt-2 flex-shrink-0"></div>
                <p>要点1</p>
            </div>
        </div>
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=None,
                require_image=None,
                priority=50
            ),

            LayoutTemplate(
                layout_type=LayoutType.TWO_COLUMN_BALANCED,
                name="均衡两栏布局",
                description="左右各50%，左栏放核心内容和图表，右栏放辅助说明和次要信息",
                structure_hint="""
<main data-layout="two-column-balanced" class="flex-grow flex gap-10">
    <div data-role="content-primary" class="flex-1 flex flex-col gap-6">
        <h2 data-role="title" class="text-3xl font-bold">主要内容</h2>
        <div data-role="chart-area" class="flex-1">
            <canvas id="chart"></canvas>
        </div>
    </div>
    <div data-role="content-secondary" class="flex-1 flex flex-col gap-6">
        <h3 data-role="title" class="text-2xl font-bold">补充说明</h3>
        <p data-role="description" class="text-base">详细说明文字</p>
        <div data-role="card" class="bg-gray-50 p-4 rounded-lg">
            <h4 class="font-semibold mb-2">关键数据</h4>
            <p class="text-2xl font-bold">数据值</p>
        </div>
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=None,
                require_image=None,
                priority=45
            ),

            # ========== 上下分割布局 ==========
            LayoutTemplate(
                layout_type=LayoutType.VERTICAL_SPLIT_TOP,
                name="上下分割布局（上图下文）",
                description="上方55%为图表或图片，下方45%为文字说明和要点列表",
                structure_hint="""
<main data-layout="vertical-split-top" class="flex-grow flex flex-col gap-8">
    <div data-role="chart-area" class="flex-1">
        <div class="placeholder h-full">
            <canvas id="chart"></canvas>
        </div>
    </div>
    <div data-role="text-content" class="flex-shrink-0">
        <h2 data-role="title" class="text-3xl font-bold mb-4">数据解读</h2>
        <div class="grid grid-cols-2 gap-4">
            <div data-role="card" class="bg-gray-50 p-4 rounded-lg">
                <h4 class="font-semibold">要点1</h4>
                <p>说明文字</p>
            </div>
        </div>
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=None,
                require_image=None,
                priority=40
            ),

            LayoutTemplate(
                layout_type=LayoutType.VERTICAL_SPLIT_BOTTOM,
                name="上下分割布局（上文下图）",
                description="上方45%为标题和文字说明，下方55%为图表或图片",
                structure_hint="""
<main data-layout="vertical-split-bottom" class="flex-grow flex flex-col gap-8">
    <div data-role="text-content" class="flex-shrink-0">
        <h2 data-role="title" class="text-4xl font-bold mb-4">标题</h2>
        <p data-role="description" class="text-xl leading-relaxed">详细介绍文字</p>
        <div class="flex gap-6 mt-6">
            <div class="flex items-center gap-2">
                <div data-role="decoration" class="w-3 h-3 rounded-full"></div>
                <p>要点1</p>
            </div>
        </div>
    </div>
    <div data-role="chart-area" class="flex-1">
        <div class="placeholder h-full">
            <canvas id="chart"></canvas>
        </div>
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=None,
                require_image=None,
                priority=40
            ),

            # ========== 多栏布局 ==========
            LayoutTemplate(
                layout_type=LayoutType.THREE_COLUMN,
                name="三栏布局",
                description="三栏均分，左栏为要点列表，中栏为图表，右栏为补充信息和数据",
                structure_hint="""
<main data-layout="three-column" class="flex-grow flex gap-6">
    <div data-role="text-content" class="flex-1 flex flex-col gap-4">
        <h3 data-role="title" class="text-xl font-bold">关键要点</h3>
        <div class="flex flex-col gap-3">
            <div data-role="card" class="bg-gray-50 p-3 rounded-lg">
                <p class="font-semibold">要点1</p>
                <p class="text-sm">说明</p>
            </div>
        </div>
    </div>
    <div data-role="chart-area" class="flex-1">
        <div class="placeholder h-full">
            <canvas id="chart"></canvas>
        </div>
    </div>
    <div data-role="content-secondary" class="flex-1 flex flex-col gap-4">
        <h3 data-role="title" class="text-xl font-bold">补充信息</h3>
        <div data-role="card" class="bg-blue-50 p-4 rounded-lg">
            <p class="text-3xl font-bold">85%</p>
            <p class="text-sm">增长率</p>
        </div>
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=None,
                priority=35
            ),

            # ========== 网格布局 ==========
            LayoutTemplate(
                layout_type=LayoutType.CARD_GRID_2X2,
                name="2x2卡片网格",
                description="2x2网格布局，每个卡片包含一个要点、小图标和说明文字",
                structure_hint="""
<main data-layout="card-grid-2x2" class="flex-grow">
    <div class="grid grid-cols-2 gap-6 h-full">
        <div data-role="card" class="bg-gray-50 p-6 rounded-xl">
            <div class="flex items-center gap-3 mb-3">
                <div data-role="decoration" class="w-10 h-10 rounded-lg flex items-center justify-center">
                    <span class="text-xl">图标</span>
                </div>
                <h3 data-role="title" class="text-xl font-bold">要点1</h3>
            </div>
            <p data-role="description">说明文字</p>
        </div>
        <!-- 更多卡片... -->
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=False,
                require_image=False,
                priority=30
            ),

            LayoutTemplate(
                layout_type=LayoutType.CARD_GRID_3X2,
                name="3x2卡片网格",
                description="3列2行网格布局，适合展示6个相关要点或数据卡片",
                structure_hint="""
<main data-layout="card-grid-3x2" class="flex-grow">
    <div class="grid grid-cols-3 gap-4 h-full">
        <div data-role="card" class="bg-gray-50 p-4 rounded-lg">
            <p data-role="title" class="text-2xl font-bold">数据</p>
            <p data-role="description" class="text-sm">说明</p>
        </div>
        <!-- 更多卡片... -->
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=False,
                require_image=False,
                priority=25
            ),

            # ========== 特色布局 ==========
            LayoutTemplate(
                layout_type=LayoutType.FULL_CHART,
                name="全屏图表布局",
                description="图表占据80%空间，顶部仅保留标题，底部有简短的1-2行说明",
                structure_hint="""
<main data-layout="full-chart" class="flex-grow flex flex-col">
    <div data-role="header" class="flex-shrink-0 mb-4">
        <h2 data-role="title" class="text-3xl font-bold">标题</h2>
    </div>
    <div data-role="chart-area" class="flex-1">
        <div class="placeholder h-full">
            <canvas id="chart"></canvas>
        </div>
    </div>
    <div data-role="footer" class="flex-shrink-0 mt-4">
        <p class="text-center text-sm">关键结论说明</p>
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=True,
                priority=60
            ),

            LayoutTemplate(
                layout_type=LayoutType.FOCUS_HIGHLIGHT,
                name="重点突出布局",
                description="左侧大卡片突出核心数据或结论（占60%），右侧为支撑信息列表",
                structure_hint="""
<main data-layout="focus-highlight" class="flex-grow flex gap-8">
    <div data-role="highlight-card" class="flex-1 bg-gradient-to-br from-blue-50 to-white p-8 rounded-2xl">
        <h3 data-role="title" class="text-lg font-semibold mb-4">核心结论</h3>
        <p data-role="metric" class="text-6xl font-bold mb-4">85%</p>
        <p data-role="description" class="text-xl">增长率</p>
        <p data-role="description" class="text-base mt-4">说明文字</p>
    </div>
    <div data-role="text-content" class="flex-1 flex flex-col gap-3">
        <h4 data-role="title" class="font-semibold">支撑数据</h4>
        <div data-role="list-item" class="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
            <div data-role="decoration" class="w-2 h-2 rounded-full"></div>
            <p>数据点1</p>
        </div>
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=False,
                priority=55
            ),

            LayoutTemplate(
                layout_type=LayoutType.COMPARISON,
                name="对比布局",
                description="左右对比布局，中间用分隔线，适合展示对比数据或优缺点分析",
                structure_hint="""
<main data-layout="comparison" class="flex-grow flex gap-8">
    <div data-role="comparison-panel" class="flex-1 p-6 rounded-xl border-2">
        <h3 data-role="title" class="text-2xl font-bold text-center mb-6">方案A</h3>
        <div class="flex flex-col gap-4">
            <div data-role="list-item" class="flex items-start gap-2">
                <span class="text-green-500">✓</span>
                <p>优点1</p>
            </div>
            <div data-role="list-item" class="flex items-start gap-2">
                <span class="text-red-500">✗</span>
                <p>缺点1</p>
            </div>
        </div>
    </div>
    <div data-role="comparison-panel" class="flex-1 p-6 rounded-xl border-2">
        <h3 data-role="title" class="text-2xl font-bold text-center mb-6">方案B</h3>
        <div class="flex flex-col gap-4">
            <!-- 优缺点... -->
        </div>
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=False,
                priority=45
            ),

            LayoutTemplate(
                layout_type=LayoutType.TIMELINE,
                name="时间线布局",
                description="横向或纵向时间线，展示发展阶段或里程碑",
                structure_hint="""
<main data-layout="timeline" class="flex-grow">
    <div class="flex items-center justify-between gap-4">
        <div data-role="timeline-item" class="flex-1 text-center">
            <div data-role="decoration" class="w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center">
                <span class="text-white font-bold">1</span>
            </div>
            <h4 data-role="title" class="font-bold">2020</h4>
            <p data-role="description" class="text-sm">阶段1</p>
        </div>
        <div data-role="timeline-connector" class="flex-shrink-0 w-12 h-0.5 bg-gray-300"></div>
        <div data-role="timeline-item" class="flex-1 text-center">
            <div data-role="decoration" class="w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center">
                <span class="text-white font-bold">2</span>
            </div>
            <h4 data-role="title" class="font-bold">2022</h4>
            <p data-role="description" class="text-sm">阶段2</p>
        </div>
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=False,
                priority=40
            ),

            LayoutTemplate(
                layout_type=LayoutType.LIST_LAYOUT,
                name="列表布局",
                description="垂直列表布局，每个列表项包含序号、标题、图标和说明",
                structure_hint="""
<main data-layout="list-layout" class="flex-grow flex gap-8">
    <div data-role="text-content" class="flex-1">
        <div class="flex flex-col gap-5">
            <div data-role="list-item" class="flex items-start gap-4 p-4 rounded-xl">
                <div data-role="decoration" class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0">
                    <span class="text-white font-bold">1</span>
                </div>
                <div>
                    <h3 data-role="title" class="text-xl font-bold">项目1</h3>
                    <p data-role="description" class="text-base mt-1">说明文字</p>
                </div>
            </div>
        </div>
    </div>
    <div data-role="chart-area" class="flex-1">
        <div class="placeholder h-full">
            <canvas id="chart"></canvas>
        </div>
    </div>
</main>
""",
                applicable_types=["content"],
                require_chart=None,
                priority=35
            ),
        ]

    def get_layout_for_page(
        self,
        page_type: str,
        slide_number: int,
        has_chart: bool = False,
        has_image: bool = False,
        ppt_id: str = "default"
    ) -> LayoutTemplate:
        """
        为指定页面选择合适的布局

        Args:
            page_type: 页面类型（title/content/section/conclusion）
            slide_number: 幻灯片编号（从1开始）
            has_chart: 是否包含图表
            has_image: 是否包含图片
            ppt_id: PPT唯一标识（用于跟踪已使用的布局）

        Returns:
            选择的布局模板
        """
        # 1. 筛选适用的布局
        applicable = []

        for template in self.templates:
            # 检查页面类型
            if page_type not in template.applicable_types:
                continue

            # 检查图表要求
            if template.require_chart is True and not has_chart:
                continue
            if template.require_chart is False and has_chart:
                continue

            # 检查图片要求
            if template.require_image is True and not has_image:
                continue
            if template.require_image is False and has_image:
                continue

            applicable.append(template)

        if not applicable:
            # 如果没有找到适用的布局，使用最通用的布局
            applicable = [t for t in self.templates if "content" in t.applicable_types]

        # 2. 获取该PPT已使用的布局
        if ppt_id not in self.used_layouts:
            self.used_layouts[ppt_id] = []

        used = self.used_layouts[ppt_id]

        # 3. 优先选择未使用的布局
        unused = [t for t in applicable if t.layout_type not in used]

        if unused:
            # 在未使用的布局中，按优先级排序，添加随机性
            unused_sorted = sorted(unused, key=lambda x: (-x.priority, random.random()))
            selected = unused_sorted[0]
        else:
            # 如果所有适用布局都已使用，选择优先级最高的
            applicable_sorted = sorted(applicable, key=lambda x: (-x.priority, random.random()))
            selected = applicable_sorted[0]

        # 4. 记录已使用的布局
        if selected.layout_type not in used:
            used.append(selected.layout_type)

        return selected

    def generate_layout_instruction(
        self,
        page_type: str,
        slide_number: int,
        has_chart: bool = False,
        has_image: bool = False,
        ppt_id: str = "default"
    ) -> str:
        """
        生成布局指令字符串，用于嵌入到提示词中

        Args:
            page_type: 页面类型
            slide_number: 幻灯片编号
            has_chart: 是否包含图表
            has_image: 是否包含图片
            ppt_id: PPT唯一标识

        Returns:
            布局指令字符串
        """
        template = self.get_layout_for_page(
            page_type=page_type,
            slide_number=slide_number,
            has_chart=has_chart,
            has_image=has_image,
            ppt_id=ppt_id
        )

        instruction = f"""
### **🎨 本页布局要求**

**布局类型**: {template.name}

**布局说明**: {template.description}

**实现建议**:
{template.structure_hint}

**注意事项**:
1. 严格按照上述布局结构组织内容
2. 保持各元素之间的合理间距（使用 gap-4/6/8）
3. 确保内容不溢出分配的空间
4. 图表必须设置 `maintainAspectRatio: false` 和 `responsive: true`
"""

        return instruction

    def reset_tracking(self, ppt_id: str = "default"):
        """
        重置指定PPT的布局使用记录

        Args:
            ppt_id: PPT唯一标识
        """
        if ppt_id in self.used_layouts:
            self.used_layouts[ppt_id] = []