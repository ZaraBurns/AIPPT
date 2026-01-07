"""
依赖注入模块
提供FastAPI依赖项
"""
from fastapi import Depends
from typing import Annotated


# TODO: 实现依赖注入
# 例如：
# - 获取当前用户
# - 获取服务实例
# - 验证权限等


async def get_ppt_service():
    """获取PPT服务实例"""
    # TODO: 返回PPTService实例
    pass


async def get_conversion_service():
    """获取转换服务实例"""
    # TODO: 返回ConversionService实例
    pass


async def get_file_service():
    """获取文件服务实例"""
    # TODO: 返回FileService实例
    pass
