"""
PPT相关API路由
提供PPT生成、转换、下载等接口
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..schemas.ppt import (
    PPTOutlineRequest,
    PPTGenerateRequest,
    PPTOutlineResponse,
    PPTGenerateResponse,
    ProjectStatusResponse,
)
from ..schemas.common import APIResponse
from ..dependencies import PPTServiceDep
from loguru import logger

router = APIRouter()


@router.post(
    "/outline",
    response_model=APIResponse,
    summary="生成PPT大纲",
    description="生成PPT的结构化大纲，不生成完整内容。适合快速预览PPT结构。"
)
async def generate_outline(
    request: PPTOutlineRequest,
    ppt_service: PPTServiceDep
):
    """
    生成PPT大纲

    只生成PPT的结构化大纲，不生成完整内容。
    适合快速预览PPT结构。

    - **topic**: PPT主题（必填）
    - **style**: PPT风格（默认business）
    - **slides**: 幻灯片数量（默认10，范围1-50）
    """
    try:
        logger.info(f"收到大纲生成请求: {request.topic}")

        # 调用服务生成大纲
        result = await ppt_service.generate_outline(
            topic=request.topic,
            style=request.style.value,
            slides=request.slides
        )

        return APIResponse.success(
            data=result,
            message="大纲生成成功"
        )

    except Exception as e:
        logger.error(f"大纲生成失败: {e}")
        return APIResponse.error(
            message=f"大纲生成失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/generate",
    response_model=APIResponse,
    summary="生成完整PPT",
    description="从主题生成完整的演示文稿，包括HTML版本和可选的PPTX版本。"
)
async def generate_ppt(
    request: PPTGenerateRequest,
    ppt_service: PPTServiceDep
):
    """
    生成完整PPT（HTML + 可选PPTX）

    从主题生成完整的演示文稿，包括：
    - HTML版本（可在线演示）
    - PPTX版本（如果convert_to_pptx=True）

    - **topic**: PPT主题（必填）
    - **style**: PPT风格（默认business）
    - **slides**: 幻灯片数量（默认10，范围1-50）
    - **include_speech_notes**: 是否包含演讲稿（默认False）
    - **custom_search_results**: 自定义搜索结果（可选）
    - **convert_to_pptx**: 是否转换为PPTX（默认True）
    """
    try:
        logger.info(f"收到PPT生成请求: {request.topic}")

        # 调用服务生成PPT
        project_info = await ppt_service.generate_ppt_html(
            topic=request.topic,
            style=request.style.value,
            slides=request.slides,
            include_speech_notes=request.include_speech_notes,
            custom_search_results=request.custom_search_results
        )

        # 构建响应数据
        result = {
            "project_id": project_info.project_id,
            "ppt_dir": project_info.ppt_dir,
            "total_slides": project_info.total_slides,
            "index_page": project_info.ppt_dir + "/index.html",
            "presenter_page": project_info.ppt_dir + "/presenter.html",
            "pptx_file": project_info.pptx_file,
            "status": project_info.status
        }

        # 如果需要转换PPTX，这里暂时跳过（等阶段3实现）
        if request.convert_to_pptx:
            result["pptx_note"] = "PPTX转换功能将在阶段3实现"

        return APIResponse.success(
            data=result,
            message="PPT生成成功"
        )

    except Exception as e:
        logger.error(f"PPT生成失败: {e}")
        return APIResponse.error(
            message=f"PPT生成失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/{project_id}/status",
    response_model=APIResponse,
    summary="查询项目状态",
    description="查询指定项目的状态和文件列表。"
)
async def get_project_status(
    project_id: str,
    ppt_service: PPTServiceDep
):
    """
    查询项目状态

    获取指定项目的：
    - 项目状态
    - 创建时间
    - 文件列表

    - **project_id**: 项目ID（格式：timestamp_topic）
    """
    try:
        logger.debug(f"查询项目状态: {project_id}")

        # 调用服务获取状态
        result = await ppt_service.get_project_status(project_id)

        return APIResponse.success(
            data=result,
            message="查询成功"
        )

    except ValueError as e:
        logger.warning(f"项目不存在: {project_id}")
        return APIResponse.not_found(
            message=f"项目不存在: {project_id}"
        )

    except Exception as e:
        logger.error(f"查询项目状态失败: {e}")
        return APIResponse.error(
            message=f"查询失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/{project_id}/convert",
    response_model=APIResponse,
    summary="转换为PPTX",
    description="将已生成的HTML演示文稿转换为PPTX格式。（阶段3实现）"
)
async def convert_to_pptx(
    project_id: str,
    enable_llm_fix: bool = True
):
    """
    转换为PPTX

    将已生成的HTML演示文稿转换为PPTX格式。

    - **project_id**: 项目ID
    - **enable_llm_fix**: 是否启用LLM修复（默认True）

    **注意**: 此接口将在阶段3实现
    """
    return APIResponse.error(
        message="PPTX转换功能将在阶段3实现",
        code=status.HTTP_501_NOT_IMPLEMENTED
    )


@router.get(
    "/{project_id}/download/{file_type}",
    summary="下载文件",
    description="下载PPT文件（HTML/PPTX）。（阶段4实现）"
)
async def download_file(
    project_id: str,
    file_type: str
):
    """
    下载文件

    支持下载：
    - **html**: HTML演示文稿（ZIP）
    - **pptx**: PPTX文件
    - **all**: 所有文件（ZIP）

    **注意**: 此接口将在阶段4实现
    """
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "code": 501,
            "message": "文件下载功能将在阶段4实现",
            "data": {
                "note": "请稍后，功能正在开发中",
                "project_id": project_id,
                "file_type": file_type
            }
        }
    )
