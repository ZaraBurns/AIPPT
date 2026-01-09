"""
布局生成器测试脚本

演示布局生成器的功能，展示如何为不同页面生成多样化的布局指令
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ppt.layout_generator import LayoutGenerator, LayoutType


def test_layout_generator():
    """测试布局生成器的基本功能"""

    print("=" * 80)
    print("布局生成器测试")
    print("=" * 80)
    print()

    # 创建布局生成器
    generator = LayoutGenerator(seed=42)  # 使用固定种子以获得可复现结果

    # 测试场景：一个包含10页的PPT
    ppt_title = "2024年新能源汽车市场分析"

    test_pages = [
        # 页面1：封面页
        {
            "slide_number": 1,
            "page_type": "title",
            "has_chart": False,
            "has_image": False,
        },
        # 页面2：目录页
        {
            "slide_number": 2,
            "page_type": "section",
            "has_chart": False,
            "has_image": False,
        },
        # 页面3：内容页（有图表）
        {
            "slide_number": 3,
            "page_type": "content",
            "has_chart": True,
            "has_image": False,
        },
        # 页面4：内容页（有图表和图片）
        {
            "slide_number": 4,
            "page_type": "content",
            "has_chart": True,
            "has_image": True,
        },
        # 页面5：内容页（纯文字）
        {
            "slide_number": 5,
            "page_type": "content",
            "has_chart": False,
            "has_image": False,
        },
        # 页面6：内容页（有图片）
        {
            "slide_number": 6,
            "page_type": "content",
            "has_chart": False,
            "has_image": True,
        },
        # 页面7：内容页（有图表）
        {
            "slide_number": 7,
            "page_type": "content",
            "has_chart": True,
            "has_image": False,
        },
        # 页面8：内容页（有图表和图片）
        {
            "slide_number": 8,
            "page_type": "content",
            "has_chart": True,
            "has_image": True,
        },
        # 页面9：章节分隔页
        {
            "slide_number": 9,
            "page_type": "section",
            "has_chart": False,
            "has_image": False,
        },
        # 页面10：结论页
        {
            "slide_number": 10,
            "page_type": "conclusion",
            "has_chart": False,
            "has_image": False,
        },
    ]

    # 为每一页生成布局指令
    selected_layouts = []

    for i, page in enumerate(test_pages, 1):
        print(f"\n{'=' * 80}")
        print(f"页面 {i}: {page['page_type'].upper()}")
        print(f"{'=' * 80}")

        # 生成布局指令
        layout_instruction = generator.generate_layout_instruction(
            page_type=page['page_type'],
            slide_number=page['slide_number'],
            has_chart=page['has_chart'],
            has_image=page['has_image'],
            ppt_id=ppt_title
        )

        # 获取选择的布局模板
        template = generator.get_layout_for_page(
            page_type=page['page_type'],
            slide_number=page['slide_number'],
            has_chart=page['has_chart'],
            has_image=page['has_image'],
            ppt_id=ppt_title
        )

        selected_layouts.append(template.layout_type.value)

        print(f"\n选择的布局: {template.name}")
        print(f"布局类型: {template.layout_type.value}")
        print(f"优先级: {template.priority}")
        print(f"\n{layout_instruction}")

    # 统计布局使用情况
    print(f"\n\n{'=' * 80}")
    print("布局使用统计")
    print(f"{'=' * 80}")
    print()

    from collections import Counter
    layout_counts = Counter(selected_layouts)

    print(f"总页数: {len(test_pages)}")
    print(f"使用的布局类型数: {len(layout_counts)}")
    print()

    print("布局使用详情:")
    for layout_type, count in sorted(layout_counts.items(), key=lambda x: -x[1]):
        percentage = (count / len(test_pages)) * 100
        print(f"  - {layout_type}: {count}次 ({percentage:.1f}%)")

    print()
    print("✅ 布局多样性验证:")
    if len(layout_counts) >= len(test_pages) * 0.6:
        print(f"  ✓ 优秀！使用了 {len(layout_counts)} 种不同的布局，占比 {len(layout_counts)/len(test_pages)*100:.1f}%")
    elif len(layout_counts) >= len(test_pages) * 0.4:
        print(f"  ✓ 良好！使用了 {len(layout_counts)} 种不同的布局，占比 {len(layout_counts)/len(test_pages)*100:.1f}%")
    else:
        print(f"  ⚠ 需要改进。仅使用了 {len(layout_counts)} 种不同的布局，占比 {len(layout_counts)/len(test_pages)*100:.1f}%")

    print()
    print("=" * 80)


def demonstrate_layout_types():
    """演示所有可用的布局类型"""

    print("\n\n")
    print("=" * 80)
    print("所有可用布局类型")
    print("=" * 80)
    print()

    generator = LayoutGenerator()

    # 按类别展示布局
    categories = {
        "封面和目录类": [
            LayoutType.TITLE_PAGE,
            LayoutType.TOC_PAGE,
            LayoutType.SECTION_PAGE,
        ],
        "标准内容页": [
            LayoutType.TWO_COLUMN_STANDARD,
            LayoutType.TWO_COLUMN_REVERSED,
            LayoutType.TWO_COLUMN_BALANCED,
        ],
        "上下分割布局": [
            LayoutType.VERTICAL_SPLIT_TOP,
            LayoutType.VERTICAL_SPLIT_BOTTOM,
        ],
        "多栏布局": [
            LayoutType.THREE_COLUMN,
        ],
        "网格布局": [
            LayoutType.CARD_GRID_2X2,
            LayoutType.CARD_GRID_3X2,
        ],
        "特色布局": [
            LayoutType.FULL_CHART,
            LayoutType.FOCUS_HIGHLIGHT,
            LayoutType.COMPARISON,
            LayoutType.TIMELINE,
            LayoutType.LIST_LAYOUT,
        ],
    }

    for category, layout_types in categories.items():
        print(f"\n【{category}】")
        print("-" * 80)

        templates = generator.templates
        for layout_type in layout_types:
            template = next((t for t in templates if t.layout_type == layout_type), None)
            if template:
                print(f"\n  {template.name}")
                print(f"    类型: {layout_type.value}")
                print(f"    描述: {template.description}")
                print(f"    适用: {', '.join(template.applicable_types)}")
                print(f"    优先级: {template.priority}")

    print()
    print("=" * 80)


if __name__ == "__main__":
    # 运行测试
    test_layout_generator()

    # 展示所有布局类型
    demonstrate_layout_types()