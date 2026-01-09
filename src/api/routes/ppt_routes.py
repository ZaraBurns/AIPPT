"""
PPT相关API路由
提供PPT生成、转换、下载等接口
"""
import asyncio
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..schemas.ppt import (
    PPTOutlineRequest,
    PPTGenerateRequest,
    PPTOutlineResponse,
    PPTGenerateResponse,
    ProjectStatusResponse,
    GenerateFromOutlineRequest,
)
from ...models.response import APIResponse
from ..dependencies import PPTServiceDep, HTML2PPTXServiceDep, FileServiceDep
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
    - **custom_materials**: 自定义参考资料（可选）
    """
    try:
        logger.info(f"收到大纲生成请求: {request.topic}")

        # 调用服务生成大纲
        result = await ppt_service.generate_outline(
            topic=request.topic,
            style=request.style.value,
            slides=request.slides,
            custom_materials=request.custom_materials
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


async def _convert_html_to_pptx(html_folder: Path, output_pptx: Path, html2pptx_service):
    """
    异步转换HTML到PPTX

    Args:
        html_folder: HTML文件夹路径
        output_pptx: 输出PPTX文件路径
        html2pptx_service: HTML2PPTXService实例

    Returns:
        转换结果字典

    Raises:
        RuntimeError: 如果转换失败或PPTX文件未生成
    """
    loop = asyncio.get_event_loop()
    stats = await loop.run_in_executor(
        None,
        html2pptx_service.convert_folder,
        str(html_folder),
        str(output_pptx)
    )

    # 检查转换是否真正成功
    if stats.success == 0 or not output_pptx.exists():
        error_msg = f"PPTX转换失败: {stats.failed}个文件处理失败"
        if stats.failed_files:
            error_msg += f", 首个错误: {stats.failed_files[0].get('error', 'unknown')}"
        raise RuntimeError(error_msg)

    return {
        "total": stats.total,
        "success_count": stats.success,  # 重命名避免与APIResponse.success冲突
        "failed": stats.failed,
        "elapsed_time": stats.elapsed_time,
        "total_tokens": {
            "input_tokens": stats.total_tokens.input_tokens,
            "output_tokens": stats.total_tokens.output_tokens,
            "total_tokens": stats.total_tokens.total_tokens
        }
    }


@router.post(
    "/generate",
    response_model=APIResponse,
    summary="生成完整PPT",
    description="从主题生成完整的演示文稿，包括HTML版本和可选的PPTX版本。"
)
async def generate_ppt(
    request: PPTGenerateRequest,
    ppt_service: PPTServiceDep,
    html2pptx_service: HTML2PPTXServiceDep = None
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
    - **custom_materials**: 自定义参考资料（可选）
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
            custom_materials=request.custom_materials
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
        if request.convert_to_pptx and html2pptx_service:
            logger.info(f"开始自动转换PPTX: {project_info.project_id}")

            try:
                # 获取项目目录
                project_dir = ppt_service.get_project_dir(project_info.project_id)
                html_folder = project_dir / "reports" / "ppt" / "slides"
                output_pptx = project_dir / "reports" / "ppt" / "output.pptx"

                # 执行转换
                stats = await _convert_html_to_pptx(html_folder, output_pptx, html2pptx_service)

                result["pptx_file"] = str(output_pptx)
                result["conversion_stats"] = stats
                logger.info(f"✅ PPTX自动转换成功: {output_pptx}")

            except Exception as e:
                result["pptx_error"] = str(e)
                logger.error(f"PPTX自动转换异常: {e}")
                # PPTX转换失败不影响整体响应
        elif request.convert_to_pptx and not html2pptx_service:
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
    html2pptx_service: HTML2PPTXServiceDep = None,
    file_service: FileServiceDep = None
):
    """
    转换为PPTX

    将已生成的HTML演示文稿转换为PPTX格式。

    - **project_id**: 项目ID
    - **enable_llm_fix**: 是否启用LLM修复（默认True，已由配置管理）

    返回转换结果信息，包括状态、PPTX路径和统计信息。
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
        output_pptx = project_dir / "reports" / "ppt" / "output.pptx"
        if output_pptx.exists():
            logger.info(f"PPTX文件已存在: {output_pptx}")
            return APIResponse.success(
                data={
                    "status": "completed",
                    "pptx_path": str(output_pptx),
                    "conversion_stats": {
                        "note": "使用已存在的PPTX文件"
                    }
                },
                message="PPTX文件已存在"
            )

        # 执行转换
        stats = await _convert_html_to_pptx(html_folder, output_pptx, html2pptx_service)

        # 构建响应
        result = {
            "status": "completed",
            "pptx_path": str(output_pptx),
            "conversion_stats": stats
        }

        logger.info(f"✅ PPTX转换成功: {output_pptx}")
        return APIResponse.success(
            data=result,
            message="PPTX转换成功"
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
    description="下载PPT文件（HTML/PPTX/ALL）"
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


@router.post(
    "/generate-from-outline",
    response_model=APIResponse,
    summary="从大纲生成PPT",
    description="接受结构化大纲数据，生成HTML和PPTX格式的演示文稿"
)
async def generate_from_outline(
    request: GenerateFromOutlineRequest,
    ppt_service: PPTServiceDep,
    html2pptx_service: HTML2PPTXServiceDep = None
):
    """
    从大纲生成PPT

    接受用户提供的大纲数据（outline.json），生成：
    - HTML版本（可在线演示）
    - PPTX版本（如果convert_to_pptx=True）

    - **outline**: PPT大纲数据（必填，JSON格式）
    - **style**: PPT风格（默认business）
    - **include_speech_notes**: 是否包含演讲稿（默认False）
    - **convert_to_pptx**: 是否转换为PPTX（默认True）
    - **custom_materials**: 自定义参考资料（可选）
    """
    try:
        logger.info(f"收到从大纲生成PPT请求: {request.outline.get('title', 'Unknown')}")

        # 调用服务生成PPT
        project_info = await ppt_service.generate_ppt_from_outline(
            outline=request.outline,
            style=request.style.value,
            include_speech_notes=request.include_speech_notes,
            convert_to_pptx=False,  # 先不转换，稍后处理
            custom_materials=request.custom_materials
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
        if request.convert_to_pptx and html2pptx_service:
            logger.info(f"开始自动转换PPTX: {project_info.project_id}")

            try:
                # 获取项目目录
                project_dir = ppt_service.get_project_dir(project_info.project_id)
                html_folder = project_dir / "reports" / "ppt" / "slides"
                output_pptx = project_dir / "reports" / "ppt" / "output.pptx"

                # 执行转换
                stats = await _convert_html_to_pptx(html_folder, output_pptx, html2pptx_service)

                result["pptx_file"] = str(output_pptx)
                result["conversion_stats"] = stats
                logger.info(f"✅ PPTX自动转换成功: {output_pptx}")

            except Exception as e:
                result["pptx_error"] = str(e)
                logger.error(f"PPTX自动转换异常: {e}")
                # PPTX转换失败不影响整体响应
        elif request.convert_to_pptx and not html2pptx_service:
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
