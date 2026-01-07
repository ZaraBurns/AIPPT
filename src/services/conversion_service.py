"""
PPTX转换服务
封装HTML到PPTX的转换逻辑
"""
import asyncio
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from loguru import logger

# 导入现有的转换服务
try:
    from script.html2pptx import (
        HTML2PPTXService,
        ServiceConfig,
        ConversionResult,
        BatchConversionStats,
        FixMethod
    )
except ImportError:
    # 如果导入失败，尝试相对导入
    import sys
    from pathlib import Path as PathLib
    script_dir = PathLib(__file__).parent.parent / "script"
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    from html2pptx import (
        HTML2PPTXService,
        ServiceConfig,
        ConversionResult,
        BatchConversionStats,
        FixMethod
    )

from ..models.api import ConversionStats


@dataclass
class ConversionTask:
    """转换任务信息"""
    task_id: str
    project_id: str
    status: str = "pending"  # pending, converting, completed, failed
    pptx_path: Optional[str] = None
    error: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    created_at: float = 0.0
    completed_at: float = 0.0


class ConversionService:
    """
    PPTX转换服务

    封装html2pptx.py的HTML2PPTXService，
    提供异步接口和进度追踪。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_name: str = "deepseek-v3.2-exp",
        enable_llm_fix: bool = True
    ):
        """
        初始化转换服务

        Args:
            api_key: LLM API密钥（用于修复HTML）
            api_base_url: API基础URL
            model_name: 模型名称
            enable_llm_fix: 是否启用LLM修复
        """
        logger.info("初始化PPTX转换服务...")

        # 创建服务配置
        self.config = ServiceConfig(
            api_key=api_key or "",
            api_base_url=api_base_url,
            model_name=model_name,
            enable_llm_fix=enable_llm_fix,
            skip_failed_files=True,
            request_interval=1.0,
            timeout=120
        )

        # 创建底层转换服务
        self.converter = HTML2PPTXService(self.config)

        # 任务存储（内存中，生产环境可使用Redis）
        self.tasks: Dict[str, ConversionTask] = {}

        logger.info("✅ PPTX转换服务初始化完成")

    async def convert_to_pptx(
        self,
        project_id: str,
        html_folder: Path,
        output_pptx: Path,
        progress_callback: Optional[Callable[[str, Dict], None]] = None
    ) -> ConversionTask:
        """
        转换HTML文件夹为PPTX

        Args:
            project_id: 项目ID
            html_folder: HTML文件夹路径
            output_pptx: 输出PPTX文件路径
            progress_callback: 进度回调函数

        Returns:
            ConversionTask对象
        """
        task_id = str(uuid.uuid4())

        logger.info(f"📝 开始转换任务: {task_id}")
        logger.info(f"   项目ID: {project_id}")
        logger.info(f"   HTML文件夹: {html_folder}")
        logger.info(f"   输出文件: {output_pptx}")

        # 创建转换任务
        task = ConversionTask(
            task_id=task_id,
            project_id=project_id,
            status="converting",
            created_at=time.time()
        )
        self.tasks[task_id] = task

        # 设置进度回调
        if progress_callback:
            self.converter.on_progress = progress_callback

        try:
            # 异步执行转换（使用线程池执行同步代码）
            loop = asyncio.get_event_loop()
            stats: BatchConversionStats = await loop.run_in_executor(
                None,
                self.converter.convert_folder,
                html_folder,
                output_pptx
            )

            # 更新任务状态
            task.status = "completed"
            task.pptx_path = str(output_pptx)
            task.completed_at = time.time()
            task.stats = {
                "total": stats.total,
                "success": stats.success,
                "failed": stats.failed,
                "skipped": stats.skipped,
                "direct": stats.direct,
                "llm": stats.llm,
                "elapsed_time": stats.elapsed_time,
                "total_tokens": stats.total_tokens.total_tokens
            }

            logger.info(f"✅ 转换任务完成: {task_id}")
            logger.info(f"   成功: {stats.success}/{stats.total}")
            logger.info(f"   耗时: {stats.elapsed_time:.1f}秒")
            logger.info(f"   Token使用: {stats.total_tokens.total_tokens}")

        except Exception as e:
            logger.error(f"❌ 转换任务失败: {task_id} - {e}")
            task.status = "failed"
            task.error = str(e)
            task.completed_at = time.time()

        return task

    async def convert_with_progress(
        self,
        project_id: str,
        html_folder: Path,
        output_pptx: Path
    ):
        """
        带进度流的转换（用于SSE/WebSocket）

        Args:
            project_id: 项目ID
            html_folder: HTML文件夹路径
            output_pptx: 输出PPTX文件路径

        Yields:
            进度更新字典
        """
        task_id = str(uuid.uuid4())

        def progress_callback(event: str, data: Dict):
            """进度回调"""
            yield {
                "task_id": task_id,
                "event": event,
                "data": data,
                "timestamp": time.time()
            }

        # 执行转换
        task = await self.convert_to_pptx(
            project_id=project_id,
            html_folder=html_folder,
            output_pptx=output_pptx,
            progress_callback=progress_callback
        )

        yield {
            "task_id": task.task_id,
            "event": "completed",
            "data": {
                "status": task.status,
                "pptx_path": task.pptx_path,
                "stats": task.stats
            },
            "timestamp": time.time()
        }

    def get_task_status(self, task_id: str) -> Optional[ConversionTask]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            ConversionTask对象，如果不存在返回None
        """
        return self.tasks.get(task_id)

    def get_project_pptx_path(self, project_id: str) -> Optional[Path]:
        """
        获取项目的PPTX文件路径

        Args:
            project_id: 项目ID

        Returns:
            PPTX文件路径，如果不存在返回None
        """
        storage_base = Path("storage")
        project_dir = storage_base / project_id
        pptx_file = project_dir / "reports" / "ppt" / "output.pptx"

        if pptx_file.exists():
            return pptx_file

        return None

    async def auto_convert_after_generation(
        self,
        project_id: str,
        project_dir: Path
    ) -> Optional[ConversionTask]:
        """
        PPT生成后自动转换为PPTX

        Args:
            project_id: 项目ID
            project_dir: 项目目录

        Returns:
            ConversionTask对象，如果转换失败返回None
        """
        # 查找HTML幻灯片文件夹
        html_folder = project_dir / "reports" / "ppt" / "slides"

        if not html_folder.exists():
            logger.warning(f"HTML文件夹不存在: {html_folder}")
            return None

        # 检查是否有HTML文件
        html_files = list(html_folder.glob("*.html"))
        if not html_files:
            logger.warning(f"没有找到HTML文件: {html_folder}")
            return None

        # 设置输出路径
        output_pptx = project_dir / "reports" / "ppt" / "output.pptx"

        try:
            # 执行转换
            task = await self.convert_to_pptx(
                project_id=project_id,
                html_folder=html_folder,
                output_pptx=output_pptx
            )

            return task

        except Exception as e:
            logger.error(f"自动转换失败: {e}")
            return None
