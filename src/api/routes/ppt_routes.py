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
from ..dependencies import PPTServiceDep, ConversionServiceDep, FileServiceDep
from loguru import logger
from pathlib import Path
from fastapi.responses import FileResponse

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
    ppt_service: PPTServiceDep,
    conversion_service: ConversionServiceDep = None
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
            "pptx_file": None,
            "status": project_info.status
        }

        # 如果需要转换PPTX
        if request.convert_to_pptx and conversion_service:
            logger.info(f"开始自动转换PPTX: {project_info.project_id}")

            try:
                # 获取项目目录
                project_dir = ppt_service.get_project_dir(project_info.project_id)

                # 自动转换
                task = await conversion_service.auto_convert_after_generation(
                    project_id=project_info.project_id,
                    project_dir=project_dir
                )

                if task and task.status == "completed":
                    result["pptx_file"] = task.pptx_path
                    result["conversion_stats"] = task.stats
                    logger.info(f"✅ PPTX自动转换成功: {task.pptx_path}")
                else:
                    result["pptx_error"] = task.error if task else "转换服务未初始化"
                    logger.warning(f"PPTX转换失败: {result.get('pptx_error')}")

            except Exception as e:
                result["pptx_error"] = str(e)
                logger.error(f"PPTX自动转换异常: {e}")
                # PPTX转换失败不影响整体响应
        elif request.convert_to_pptx and not conversion_service:
            result["pptx_note"] = "转换服务未初始化"

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
    description="将已生成的HTML演示文稿转换为PPTX格式"
)
async def convert_to_pptx(
    project_id: str,
    enable_llm_fix: bool = True,
    ppt_service: PPTServiceDep = None,
    conversion_service: ConversionServiceDep = None
):
    """
    转换为PPTX

    将已生成的HTML演示文稿转换为PPTX格式。

    - **project_id**: 项目ID
    - **enable_llm_fix**: 是否启用LLM修复（默认True）

    返回转换任务信息，包括任务ID、状态、PPTX路径和统计信息。
    """
    try:
        logger.info(f"收到PPTX转换请求: {project_id}")

        # 获取项目目录
        project_dir = ppt_service.get_project_dir(project_id)
        if not project_dir:
            return APIResponse.not_found(
                message=f"项目不存在: {project_id}"
            )

        # 查找HTML文件夹
        html_folder = project_dir / "reports" / "ppt" / "slides"
        if not html_folder.exists():
            return APIResponse.bad_request(
                message=f"未找到HTML幻灯片文件夹"
            )

        # 检查是否已有PPTX文件
        existing_pptx = conversion_service.get_project_pptx_path(project_id)
        if existing_pptx and existing_pptx.exists():
            logger.info(f"PPTX文件已存在: {existing_pptx}")
            return APIResponse.success(
                data={
                    "task_id": "existing",
                    "status": "completed",
                    "pptx_path": str(existing_pptx),
                    "conversion_stats": {
                        "note": "使用已存在的PPTX文件"
                    }
                },
                message="PPTX文件已存在"
            )

        # 设置输出路径
        output_pptx = project_dir / "reports" / "ppt" / "output.pptx"

        # 执行转换
        task = await conversion_service.convert_to_pptx(
            project_id=project_id,
            html_folder=html_folder,
            output_pptx=output_pptx
        )

        # 构建响应
        result = {
            "task_id": task.task_id,
            "status": task.status,
            "pptx_path": task.pptx_path,
            "conversion_stats": task.stats
        }

        if task.status == "completed":
            logger.info(f"✅ PPTX转换成功: {task.task_id}")
            return APIResponse.success(
                data=result,
                message="PPTX转换成功"
            )
        else:
            logger.error(f"❌ PPTX转换失败: {task.error}")
            return APIResponse.error(
                message=f"PPTX转换失败: {task.error}",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=result
            )

    except Exception as e:
        logger.error(f"PPTX转换异常: {e}")
        return APIResponse.error(
            message=f"PPTX转换异常: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/{project_id}/download/{file_type}",
    summary="下载文件",
    description="下载PPT文件（HTML/PPTX/ZIP）"
)
async def download_file(
    project_id: str,
    file_type: str,
    file_service: FileServiceDep
):
    """
    下载文件

    支持下载：
    - **pptx**: PPTX文件
    - **html**: HTML导航页
    - **all**: 所有文件（ZIP压缩包）

    - **project_id**: 项目ID
    - **file_type**: 文件类型（pptx/html/all）
    """
    try:
        logger.info(f"收到文件下载请求: {project_id} - {file_type}")

        # 验证file_type
        if file_type not in ["pptx", "html", "all"]:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_type}。支持的类型: pptx, html, all"
            )

        # 根据类型返回文件
        if file_type == "pptx":
            return file_service.create_pptx_response(project_id)

        elif file_type == "html":
            return file_service.create_html_response(project_id)

        elif file_type == "all":
            return file_service.create_zip_response(
                project_id=project_id,
                include_pptx=True,
                include_html=True
            )

    except Exception as e:
        # 如果是HTTPException，直接抛出
        if hasattr(e, "status_code"):
            raise

        # 其他异常返回错误响应
        logger.error(f"文件下载失败: {e}")
        return APIResponse.error(
            message=f"文件下载失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
