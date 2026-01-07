"""
文件管理API路由
提供文件列表、删除等功能
"""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/list")
async def list_files():
    """
    列出项目文件

    获取所有项目及其文件列表。
    """
    # TODO: 实现文件列表逻辑
    raise HTTPException(status_code=501, detail="接口尚未实现")


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """
    删除项目

    删除指定项目及其所有文件。
    """
    # TODO: 实现项目删除逻辑
    raise HTTPException(status_code=501, detail="接口尚未实现")
