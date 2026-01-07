"""
PPT服务层
封装PPT生成业务逻辑
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger

from ..llm.manager import LLMManager
from ..ppt.ppt_coordinator import PPTCoordinator
from ..storage.search_storage import SearchStorage
from ..models.api import PPTProjectInfo


class PPTService:
    """
    PPT生成服务

    封装AIPPTGenerator和PPTCoordinator的复杂逻辑，
    为API层提供简洁的接口。
    """

    def __init__(self, config_path: str = "config/llm_config.yaml"):
        """
        初始化PPT服务

        Args:
            config_path: LLM配置文件路径
        """
        logger.info("初始化PPT服务...")

        # 初始化LLM管理器
        self.llm_manager = LLMManager(config_path)

        # 获取Prompt管理器
        self.prompt_manager = self.llm_manager.get_prompt_manager()

        # 初始化PPT协调器
        self.ppt_coordinator = PPTCoordinator(
            llm_manager=self.llm_manager,
            prompt_manager=self.prompt_manager
        )

        # 初始化存储管理器
        self.storage = SearchStorage(base_dir="storage")

        logger.info("✅ PPT服务初始化完成")

    async def generate_outline(
        self,
        topic: str,
        style: str = "business",
        slides: int = 10
    ) -> Dict[str, Any]:
        """
        生成PPT大纲

        Args:
            topic: PPT主题
            style: PPT风格
            slides: 幻灯片数量

        Returns:
            大纲数据字典
        """
        logger.info(f"📝 生成PPT大纲: {topic}")

        try:
            # 调用PPTCoordinator生成大纲
            outline = await self.ppt_coordinator._generate_outline_v2(
                topic=topic,
                search_results=[],
                style=style,
                slides=slides
            )

            # 返回结果
            result = {
                "outline": outline,
                "estimated_slides": len(outline.get("pages", [])),
                "estimated_time": "3-5分钟"
            }

            logger.info(f"✅ 大纲生成完成，共 {len(outline.get('pages', []))} 页")
            return result

        except Exception as e:
            logger.error(f"❌ 大纲生成失败: {e}")
            raise

    async def generate_ppt_html(
        self,
        topic: str,
        style: str = "business",
        slides: int = 10,
        include_speech_notes: bool = False,
        custom_search_results: Optional[List[Dict]] = None
    ) -> PPTProjectInfo:
        """
        生成完整PPT（HTML格式）

        Args:
            topic: PPT主题
            style: PPT风格
            slides: 幻灯片数量
            include_speech_notes: 是否包含演讲稿
            custom_search_results: 自定义搜索结果

        Returns:
            PPT项目信息
        """
        logger.info(f"📝 生成PPT: {topic}")

        # 创建项目目录
        project_id = self.storage.create_project(topic)
        project_dir = self.storage.get_project_dir()
        logger.info(f"📁 项目ID: {project_id}")

        # 准备搜索结果
        search_results = []
        if custom_search_results:
            logger.info(f"📊 使用自定义搜索结果 ({len(custom_search_results)} 条)")
            search_results = custom_search_results
            # 保存搜索结果
            if search_results:
                self.storage.save_search_results({"all_content": search_results})

        # PPT配置
        ppt_config = {
            "style": style,
            "slides": slides,
            "speech_notes": include_speech_notes
        }

        # 创建输出目录
        output_path = project_dir / "reports" / "ppt"
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            # 生成HTML PPT
            result = await self.ppt_coordinator.generate_ppt_v3(
                topic=topic,
                search_results=search_results,
                ppt_config=ppt_config,
                output_dir=output_path
            )

            # 检查生成结果
            if result.get("status") != "success":
                error_msg = result.get("error", "未知错误")
                logger.error(f"❌ PPT生成失败: {error_msg}")
                raise Exception(error_msg)

            # 构建项目信息
            project_info = PPTProjectInfo(
                project_id=project_id,
                topic=topic,
                status="completed",
                created_at=self.storage.load_metadata().get("created_at"),
                ppt_dir=str(result.get("ppt_dir", "")),
                total_slides=result.get("total_slides", 0),
                pptx_file=None  # 稍后在转换时设置
            )

            # 保存到存储
            self._save_ppt_to_storage(result, topic, project_dir)

            logger.info(f"✅ PPT生成成功: {project_id}")
            logger.info(f"   📄 总页数: {result.get('total_slides')}")
            logger.info(f"   🏠 导航页: {result.get('index_page')}")
            logger.info(f"   🎬 演示页: {result.get('presenter_page')}")

            return project_info

        except Exception as e:
            logger.error(f"❌ PPT生成异常: {e}")
            # 更新项目状态为失败
            metadata = self.storage.load_metadata()
            if metadata:
                metadata["status"] = "failed"
                metadata["error"] = str(e)
                self.storage.save_metadata(metadata)
            raise

    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """
        获取项目状态

        Args:
            project_id: 项目ID

        Returns:
            项目状态信息
        """
        logger.debug(f"查询项目状态: {project_id}")

        try:
            # 从storage目录查找项目
            projects = self.storage.list_projects()
            project = next((p for p in projects if p["project_id"] == project_id), None)

            if not project:
                raise ValueError(f"项目不存在: {project_id}")

            # 获取项目文件列表
            project_dir = Path(project["path"])
            files = []

            # 检查reports目录
            reports_dir = project_dir / "reports"
            if reports_dir.exists():
                ppt_dir = reports_dir / "ppt"
                if ppt_dir.exists():
                    # 列出所有HTML文件
                    for html_file in ppt_dir.glob("*.html"):
                        files.append(html_file.name)

                    # 列出PPTX文件
                    for pptx_file in ppt_dir.glob("*.pptx"):
                        files.append(pptx_file.name)

            result = {
                "project_id": project_id,
                "status": project.get("status", "unknown"),
                "created_at": project.get("created_at", ""),
                "files": files
            }

            return result

        except Exception as e:
            logger.error(f"❌ 查询项目状态失败: {e}")
            raise

    def _save_ppt_to_storage(
        self,
        ppt_result: Dict[str, Any],
        topic: str,
        project_dir: Path
    ):
        """
        将PPT结果保存到SearchStorage

        Args:
            ppt_result: PPT生成结果
            topic: PPT主题
            project_dir: 项目目录
        """
        # 构建报告格式
        report = {
            "ppt": {
                "title": topic,
                "slides": ppt_result.get("slide_files", []),
                "metadata": {
                    "total_slides": ppt_result.get("total_slides", 0),
                    "ppt_dir": str(ppt_result.get("ppt_dir", "")),
                    "index_page": str(ppt_result.get("index_page", "")),
                    "presenter_page": str(ppt_result.get("presenter_page", "")),
                    "generated_at": ppt_result.get("ppt_outline", {}).get(
                        "created_at", ""
                    )
                }
            },
            "html_content": None,
            "output_format": "ppt_v3"
        }

        # 保存最终报告
        self.storage.save_final_report(report, topic)
        logger.debug("✅ 报告已保存到SearchStorage")

    def get_project_dir(self, project_id: str) -> Optional[Path]:
        """
        获取项目目录路径

        Args:
            project_id: 项目ID

        Returns:
            项目目录路径，如果不存在返回None
        """
        storage_base = Path("storage")
        project_dir = storage_base / project_id

        if project_dir.exists():
            return project_dir

        return None
