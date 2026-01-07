"""
依赖注入模块
提供FastAPI依赖项
"""
from functools import lru_cache
from typing import Annotated
from fastapi import Depends

from ..services.ppt_service import PPTService


@lru_cache()
def get_ppt_service() -> PPTService:
    """
    获取PPT服务实例（单例）

    使用lru_cache确保整个应用生命周期内只有一个实例
    """
    return PPTService()


# 类型别名，用于依赖注入
PPTServiceDep = Annotated[PPTService, Depends(get_ppt_service)]


# TODO: 后续添加其他服务
# async def get_conversion_service() -> ConversionService:
#     ...
#
# ConversionServiceDep = Annotated[ConversionService, Depends(get_conversion_service)]
#
#
# async def get_file_service() -> FileService:
#     ...
#
# FileServiceDep = Annotated[FileService, Depends(get_file_service)]
