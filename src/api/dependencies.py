"""
依赖注入模块
提供FastAPI依赖项
"""
from functools import lru_cache
from typing import Annotated, Optional
from fastapi import Depends
from dotenv import load_dotenv
import os

from ..services.ppt_service import PPTService
from ..services.conversion_service import ConversionService

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
def get_conversion_service() -> ConversionService:
    """
    获取转换服务实例（单例）

    Returns:
        ConversionService实例
    """
    # 从环境变量获取API配置
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = os.getenv("LLM_MODEL", "deepseek-v3.2-exp")

    return ConversionService(
        api_key=api_key,
        api_base_url=api_base,
        model_name=model,
        enable_llm_fix=True
    )


# 类型别名，用于依赖注入
PPTServiceDep = Annotated[PPTService, Depends(get_ppt_service)]
ConversionServiceDep = Annotated[ConversionService, Depends(get_conversion_service)]


# TODO: 后续添加FileService
# async def get_file_service() -> FileService:
#     ...
#
# FileServiceDep = Annotated[FileService, Depends(get_file_service)]
