#!/usr/bin/env python3
"""
AIPPT - AI 驱动的 PowerPoint 生成系统
主入口文件
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import argparse

# 添加项目根目录到 Python 路径（而不是 src 目录）
# 这样 src 才能作为顶层包，使得相对导入正常工作
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from loguru import logger
from dotenv import load_dotenv

# 导入项目模块（从 src 包导入）
from src.llm.manager import LLMManager
from src.ppt.ppt_coordinator import PPTCoordinator
from src.storage.search_storage import SearchStorage


# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


class AIPPTGenerator:
    """AIPPT 生成器主类"""

    def __init__(self, config_path: str = "config/llm_config.yaml"):
        """
        初始化 AIPPT 生成器

        Args:
            config_path: LLM 配置文件路径
        """
        logger.info("🚀 初始化 AIPPT 生成器...")

        # 加载环境变量
        load_dotenv()
        logger.info("✓ 环境变量已加载")

        # 初始化 LLM 管理器
        self.llm_manager = LLMManager(config_path)
        logger.info(f"✓ LLM 管理器已初始化")

        # 获取 Prompt 管理器
        self.prompt_manager = self.llm_manager.get_prompt_manager()
        logger.info(f"✓ Prompt 管理器已加载")

        # 初始化 PPT 协调器
        self.ppt_coordinator = PPTCoordinator(
            llm_manager=self.llm_manager,
            prompt_manager=self.prompt_manager
        )
        logger.info(f"✓ PPT 协调器已初始化")

        # 初始化存储管理器 (使用SearchStorage进行结构化管理)
        self.storage = SearchStorage(base_dir="storage")
        logger.info(f"✓ 存储管理器已初始化")

        logger.info("✅ 系统初始化完成\n")

    async def generate_ppt(
        self,
        topic: str,
        style: str = "business",
        slides: int = 10,
        output_dir: str = "output",
        include_speech_notes: bool = False,
        search_enabled: bool = True,
        custom_search_results: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        生成 PPT

        Args:
            topic: PPT 主题
            style: 风格 (business/academic/creative/simple/educational/tech/nature/magazine/ted)
            slides: 幻灯片数量
            output_dir: 输出目录 (保留用于向后兼容,实际使用SearchStorage管理)
            include_speech_notes: 是否包含演讲稿
            search_enabled: 是否启用搜索
            custom_search_results: 自定义搜索结果

        Returns:
            生成结果字典
        """
        logger.info(f"📝 开始生成 PPT")
        logger.info(f"   主题: {topic}")
        logger.info(f"   风格: {style}")
        logger.info(f"   页数: {slides}")
        logger.info(f"   演讲稿: {'是' if include_speech_notes else '否'}")
        logger.info("")

        # 使用SearchStorage创建项目目录 (每个主题独立文件夹)
        project_id = self.storage.create_project(topic)
        logger.info(f"📁 项目ID: {project_id}")
        project_dir = self.storage.get_project_dir()

        # 准备搜索结果
        search_results = []
        if custom_search_results:
            logger.info(f"📊 使用自定义搜索结果 ({len(custom_search_results)} 条)")
            search_results = custom_search_results
            # 保存搜索结果到storage
            if search_results:
                self.storage.save_search_results({"all_content": search_results})
        elif search_enabled:
            logger.info("🔍 搜索相关内容...")
            # 这里可以集成搜索功能
            # search_results = await self._search_topic(topic)
            logger.info("⚠️  搜索功能暂未启用，使用空搜索结果")

        # PPT 配置
        ppt_config = {
            "style": style,
            "slides": slides,
            "speech_notes": include_speech_notes
        }

        # 使用项目目录作为输出目录
        output_path = project_dir / "reports" / "ppt"
        output_path.mkdir(parents=True, exist_ok=True)

        # 使用 generate_ppt_v3 生成多页HTML PPT
        result = await self.ppt_coordinator.generate_ppt_v3(
            topic=topic,
            search_results=search_results,
            ppt_config=ppt_config,
            output_dir=output_path
        )

        # 处理结果
        if result.get("status") == "success":
            logger.info(f"\n✅ PPT 生成成功!")
            logger.info(f"📁 PPT目录: {result.get('ppt_dir')}")
            logger.info(f"📄 总页数: {result.get('total_slides')}")
            logger.info(f"🏠 导航页: {result.get('index_page')}")
            logger.info(f"🎬 演示页: {result.get('presenter_page')}")

            # 使用SearchStorage保存最终报告
            logger.info(f"\n💾 保存报告到SearchStorage...")
            self._save_ppt_to_storage(result, topic, project_dir)
        else:
            logger.error(f"\n❌ PPT 生成失败: {result.get('error', '未知错误')}")

        return result

    def _save_ppt_to_storage(self, ppt_result: Dict[str, Any], topic: str, project_dir: Path):
        """
        将PPT结果保存到SearchStorage

        Args:
            ppt_result: PPT生成结果
            topic: PPT主题
            project_dir: 项目目录
        """
        # 构建适合SearchStorage.save_final_report的格式
        report = {
            "ppt": {
                "title": topic,
                "slides": ppt_result.get("slide_files", []),
                "metadata": {
                    "total_slides": ppt_result.get("total_slides", 0),
                    "ppt_dir": str(ppt_result.get("ppt_dir", "")),
                    "index_page": str(ppt_result.get("index_page", "")),
                    "presenter_page": str(ppt_result.get("presenter_page", "")),
                    "generated_at": datetime.now().isoformat()
                }
            },
            "html_content": None,  # V3已经生成了多页HTML,这里不需要
            "output_format": "ppt_v3"
        }

        # 使用SearchStorage保存最终报告
        self.storage.save_final_report(report, topic)
        logger.info(f"✅ 报告已保存到SearchStorage: {project_dir}")

    async def _save_ppt(self, result: Dict[str, Any], output_dir: str) -> Path:
        """
        保存 PPT 到文件

        Args:
            result: 生成结果
            output_dir: 输出目录

        Returns:
            输出文件路径
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名（使用时间戳和标题）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = result["ppt"]["title"].replace(" ", "_").replace("/", "_")[:30]
        file_name = f"{timestamp}_{title}"

        # 保存 HTML 内容
        if "html_content" in result:
            html_file = output_path / f"{file_name}.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(result["html_content"])
            logger.info(f"   ✓ HTML 文件: {html_file}")

        # 保存 JSON 数据
        json_file = output_path / f"{file_name}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"   ✓ JSON 数据: {json_file}")

        # 保存演讲稿（如果有）
        if "speech_notes" in result:
            notes_file = output_path / f"{file_name}_notes.json"
            with open(notes_file, "w", encoding="utf-8") as f:
                json.dump(result["speech_notes"], f, ensure_ascii=False, indent=2)
            logger.info(f"   ✓ 演讲稿: {notes_file}")

        return output_path


async def main_async():
    """异步主函数"""
    parser = argparse.ArgumentParser(
        description="AIPPT - AI 驱动的 PowerPoint 生成系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本使用
  python src/main.py "人工智能的发展趋势"

  # 指定风格和页数
  python src/main.py "气候变化的影响" --style academic --slides 15

  # 包含演讲稿
  python src/main.py "机器学习基础" --speech-notes

  # 自定义输出目录
  python src/main.py "Python 编程入门" --output my_ppts

可用的风格:
  business    - 商务风格（默认）
  academic    - 学术风格
  creative    - 创意风格
  simple      - 简约风格
  educational - 教育风格
  tech        - 科技风格
  nature      - 自然风格
  magazine    - 杂志风格
  ted         - TED 演讲风格
        """
    )

    parser.add_argument(
        "topic",
        help="PPT 主题"
    )

    parser.add_argument(
        "--style", "-s",
        choices=["business", "academic", "creative", "simple", "educational",
                "tech", "nature", "magazine", "ted"],
        default="business",
        help="PPT 风格 (默认: business)"
    )

    parser.add_argument(
        "--slides", "-n",
        type=int,
        default=10,
        help="幻灯片数量 (默认: 10)"
    )

    parser.add_argument(
        "--output", "-o",
        default="output",
        help="输出目录 (默认: output)"
    )

    parser.add_argument(
        "--speech-notes",
        action="store_true",
        help="是否生成演讲稿"
    )

    parser.add_argument(
        "--no-search",
        action="store_true",
        help="禁用搜索功能"
    )

    parser.add_argument(
        "--config", "-c",
        default="config/llm_config.yaml",
        help="LLM 配置文件路径 (默认: config/llm_config.yaml)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level="DEBUG"
        )

    # 显示欢迎信息
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🤖 AIPPT - AI 驱动的 PowerPoint 生成系统                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    try:
        # 初始化生成器
        generator = AIPPTGenerator(config_path=args.config)

        # 生成 PPT
        result = await generator.generate_ppt(
            topic=args.topic,
            style=args.style,
            slides=args.slides,
            output_dir=args.output,
            include_speech_notes=args.speech_notes,
            search_enabled=not args.no_search
        )

        # 返回状态码
        sys.exit(0 if result.get("status") == "success" else 1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️  用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """同步入口"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.warning("\n⚠️  用户中断")
        sys.exit(130)


if __name__ == "__main__":
    main()
