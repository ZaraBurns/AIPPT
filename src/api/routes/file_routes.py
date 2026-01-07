"""
文件管理API路由
提供文件列表、删除等功能
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from loguru import logger

from ..schemas.common import APIResponse
from ..dependencies import FileServiceDep

router = APIRouter()


@router.get(
    "/list",
    response_model=APIResponse,
    summary="列出所有项目",
    description="获取所有项目及其基本信息"
)
async def list_projects(
    file_service: FileServiceDep
):
    """
    列出所有项目

    返回所有项目的信息，包括：
    - 项目ID
    - 创建时间
    - 项目状态
    - 主题
    """
    try:
        logger.debug("列出所有项目")

        projects = file_service.list_all_projects()

        return APIResponse.success(
            data={
                "total": len(projects),
                "projects": projects
            },
            message=f"共找到 {len(projects)} 个项目"
        )

    except Exception as e:
        logger.error(f"列出项目失败: {e}")
        return APIResponse.error(
            message=f"列出项目失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/{project_id}/files",
    response_model=APIResponse,
    summary="列出项目文件",
    description="获取指定项目的所有文件列表"
)
async def list_project_files(
    project_id: str,
    file_service: FileServiceDep
):
    """
    列出项目文件

    获取指定项目的所有文件，包括：
    - 文件名
    - 相对路径
    - 文件大小
    - 文件类型

    - **project_id**: 项目ID
    """
    try:
        logger.debug(f"列出项目文件: {project_id}")

        files = file_service.list_project_files(project_id)

        return APIResponse.success(
            data={
                "project_id": project_id,
                "total": len(files),
                "files": files
            },
            message=f"共找到 {len(files)} 个文件"
        )

    except Exception as e:
        logger.error(f"列出项目文件失败: {e}")
        return APIResponse.error(
            message=f"列出项目文件失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete(
    "/{project_id}",
    response_model=APIResponse,
    summary="删除项目",
    description="删除指定项目及其所有文件（危险操作）"
)
async def delete_project(
    project_id: str,
    file_service: FileServiceDep
):
    """
    删除项目

    删除指定项目及其所有文件。
    **警告：此操作不可逆！**

    - **project_id**: 项目ID
    """
    try:
        logger.warning(f"请求删除项目: {project_id}")

        # 验证项目是否存在
        files = file_service.list_project_files(project_id)

        # 执行删除
        success = file_service.delete_project(project_id)

        if success:
            return APIResponse.success(
                data={
                    "project_id": project_id,
                    "deleted_files": len(files)
                },
                message=f"项目已删除，共删除 {len(files)} 个文件"
            )
        else:
            return APIResponse.error(
                message="删除失败",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        return APIResponse.error(
            message=f"删除项目失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
