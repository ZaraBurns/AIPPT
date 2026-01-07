"""
依赖注入模块
提供FastAPI依赖项
"""
from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from dotenv import load_dotenv
import os

from ..services.ppt_service import PPTService
from ..services.file_service import FileService
from ..services.html2pptx_service import HTML2PPTXService, ServiceConfig

# 加载环境变量
load_dotenv()


@lru_cache()
def get_ppt_service() -> PPTService:
    """
    获取PPT服务实例（单例）

    使用lru_cache确保整个应用生命周期内只有一个实例
    """
    return PPTService()


@lru_cache()
def get_html2pptx_service() -> HTML2PPTXService:
    """
    获取HTML2PPTX服务实例（单例）

    Returns:
        HTML2PPTXService实例
    """
    # 从环境变量获取API配置
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = os.getenv("LLM_MODEL", "deepseek-v3.2-exp")

    # 创建服务配置
    config = ServiceConfig(
        api_key=api_key or "",
        api_base_url=api_base,
        model_name=model,
        enable_llm_fix=True,
        skip_failed_files=True,
        request_interval=1.0,
        timeout=120
    )

    return HTML2PPTXService(config)


@lru_cache()
def get_file_service() -> FileService:
    """
    获取文件服务实例（单例）

    Returns:
        FileService实例
    """
    return FileService(base_storage_dir="storage")


# 类型别名，用于依赖注入
PPTServiceDep = Annotated[PPTService, Depends(get_ppt_service)]
HTML2PPTXServiceDep = Annotated[HTML2PPTXService, Depends(get_html2pptx_service)]
FileServiceDep = Annotated[FileService, Depends(get_file_service)]
