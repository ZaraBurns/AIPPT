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

    def _process_custom_materials(self, custom_materials: Optional[str]) -> str:
        """
        处理自定义参考资料

        将外部传入的参考资料转换为可用于LLM提示词的格式。
        支持文档解析结果、用户整理的资料、联网搜索结果等。
        进行长度限制以避免提示词过长。

        Args:
            custom_materials: 自定义参考资料（字符串或JSON字符串）

        Returns:
            str: 处理后的参考资料字符串
        """
        if not custom_materials:
            return ""

        # 如果数据已经是字符串，直接使用
        if isinstance(custom_materials, str):
            data_str = custom_materials
        else:
            # 如果是其他类型（如字典），转换为JSON字符串
            import json
            try:
                data_str = json.dumps(custom_materials, ensure_ascii=False)
            except Exception as e:
                logger.warning(f"⚠️  无法转换custom_materials为JSON: {e}")
                return str(custom_materials)

        # 限制长度，避免提示词过长（最大8000字符）
        max_length = 8000
        if len(data_str) > max_length:
            logger.warning(f"⚠️  custom_materials过长({len(data_str)}字符)，截断至{max_length}字符")
            data_str = data_str[:max_length] + "...[内容过长已截断]"

        return data_str

    async def generate_outline(
        self,
        topic: str,
        style: str = "business",
        slides: int = 10,
        custom_materials: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成PPT大纲

        Args:
            topic: PPT主题
            style: PPT风格
            slides: 幻灯片数量
            custom_materials: 自定义参考资料（文档解析、用户整理的资料、联网搜索结果等），最大10000字符

        Returns:
            大纲数据字典
        """
        logger.info(f"📝 生成PPT大纲: {topic}")

        # 处理custom_materials
        custom_content_summary = self._process_custom_materials(custom_materials)

        try:
            # 调用PPTCoordinator生成大纲
            outline = await self.ppt_coordinator._generate_outline_v2(
                topic=topic,
                search_results=[],
                style=style,
                slides=slides,
                custom_content_summary=custom_content_summary if custom_content_summary else None
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
        custom_materials: Optional[str] = None
    ) -> PPTProjectInfo:
        """
        生成完整PPT（HTML格式）

        Args:
            topic: PPT主题
            style: PPT风格
            slides: 幻灯片数量
            include_speech_notes: 是否包含演讲稿
            custom_materials: 自定义参考资料（文档解析、用户整理的资料、联网搜索结果等），最大10000字符

        Returns:
            PPT项目信息
        """
        logger.info(f"📝 生成PPT: {topic}")

        # 处理custom_materials
        custom_content_summary = self._process_custom_materials(custom_materials)

        # 创建项目目录
        project_id = self.storage.create_project(topic)
        project_dir = self.storage.get_project_dir()
        logger.info(f"📁 项目ID: {project_id}")

        # 如果有自定义资料，记录日志
        if custom_content_summary:
            logger.info(f"📊 使用自定义参考资料 ({len(custom_content_summary)} 字符)")

        # PPT配置
        ppt_config = {
            "style": style,
            "slides": slides,
            "speech_notes": include_speech_notes
        }

        # 创建输出目录
        output_path = project_dir / "reports"
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            # 生成HTML PPT
            result = await self.ppt_coordinator.generate_ppt_v3(
                topic=topic,
                search_results=[],  # 不使用传统搜索结果
                ppt_config=ppt_config,
                output_dir=output_path,
                custom_content_summary=custom_content_summary if custom_content_summary else None
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

    async def generate_ppt_from_outline(
        self,
        outline: Dict[str, Any],
        style: str = "business",
        include_speech_notes: bool = False,
        convert_to_pptx: bool = True,
        custom_materials: Optional[str] = None
    ) -> PPTProjectInfo:
        """
        从已有大纲生成PPT

        Args:
            outline: PPT大纲数据（JSON格式）
            style: PPT风格
            include_speech_notes: 是否包含演讲稿
            convert_to_pptx: 是否转换为PPTX
            custom_materials: 自定义参考资料（文档解析、用户整理的资料、联网搜索结果等），最大10000字符

        Returns:
            PPT项目信息
        """
        logger.info(f"📝 从大纲生成PPT: {outline.get('title', 'Unknown')}")

        # 处理custom_materials
        custom_content_summary = self._process_custom_materials(custom_materials)

        # 1. 提取标题并创建项目
        title = outline.get("title", "Untitled")
        project_id = self.storage.create_project(title)
        project_dir = self.storage.get_project_dir()
        logger.info(f"📁 项目ID: {project_id}")

        # 2. 创建输出目录
        output_path = project_dir / "reports"
        output_path.mkdir(parents=True, exist_ok=True)

        # 3. 保存大纲到文件
        outline_path = output_path / "ppt" / "data" / "outline.json"
        outline_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(outline_path, 'w', encoding='utf-8') as f:
            json.dump(outline, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 大纲已保存: {outline_path}")

        try:
            # 4. 调用PPTCoordinator从大纲生成
            ppt_config = {
                "style": style,
                "slides": len(outline.get("pages", [])),
                "speech_notes": include_speech_notes
            }

            result = await self.ppt_coordinator.generate_ppt_from_outline(
                outline=outline,
                ppt_config=ppt_config,
                output_dir=output_path,
                custom_content_summary=custom_content_summary if custom_content_summary else None
            )

            # 5. 检查生成结果
            if result.get("status") != "success":
                error_msg = result.get("error", "未知错误")
                logger.error(f"❌ PPT生成失败: {error_msg}")
                raise Exception(error_msg)

            # 6. 构建项目信息
            project_info = PPTProjectInfo(
                project_id=project_id,
                topic=title,
                status="completed",
                created_at=self.storage.load_metadata().get("created_at"),
                ppt_dir=str(result.get("ppt_dir", "")),
                total_slides=result.get("total_slides", 0),
                pptx_file=None
            )

            # 7. 保存到存储
            self._save_ppt_to_storage(result, title, project_dir)

            logger.info(f"✅ PPT生成成功: {project_id}")
            logger.info(f"   📄 总页数: {result.get('total_slides')}")
            logger.info(f"   🏠 导航页: {result.get('index_page')}")

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
