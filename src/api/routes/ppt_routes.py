"""
PPT相关API路由
提供PPT生成、转换、下载等接口
"""
from fastapi import APIRouter, HTTPException
from ..schemas.ppt import (
    PPTOutlineRequest,
    PPTGenerateRequest,
    ConversionRequest,
    PPTOutlineResponse,
    PPTGenerateResponse,
    ConversionResponse,
)

router = APIRouter()


@router.post("/outline", response_model= dict)
async def generate_outline(request: PPTOutlineRequest):
    """
    生成PPT大纲

    只生成PPT的结构化大纲，不生成完整内容。
    适合快速预览PPT结构。
    """
    # TODO: 实现大纲生成逻辑
    raise HTTPException(status_code=501, detail="接口尚未实现")


@router.post("/generate", response_model=dict)
async def generate_ppt(request: PPTGenerateRequest):
    """
    生成完整PPT（HTML + PPTX）

    从主题生成完整的演示文稿，包括：
    - HTML版本（可在线演示）
    - PPTX版本（可下载编辑）
    """
    # TODO: 实现PPT生成逻辑
    raise HTTPException(status_code=501, detail="接口尚未实现")


@router.post("/{project_id}/convert", response_model=dict)
async def convert_to_pptx(project_id: str, request: ConversionRequest):
    """
    转换为PPTX

    将已生成的HTML演示文稿转换为PPTX格式。
    """
    # TODO: 实现PPTX转换逻辑
    raise HTTPException(status_code=501, detail="接口尚未实现")


@router.get("/{project_id}/download/{file_type}")
async def download_file(project_id: str, file_type: str):
    """
    下载文件

    支持下载：
    - html: HTML演示文稿（ZIP）
    - pptx: PPTX文件
    - all: 所有文件（ZIP）
    """
    # TODO: 实现文件下载逻辑
    raise HTTPException(status_code=501, detail="接口尚未实现")
