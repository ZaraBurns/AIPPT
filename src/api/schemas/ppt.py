"""
PPT相关API数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class PPTStyle(str, Enum):
    """PPT风格枚举"""
    BUSINESS = "business"
    ACADEMIC = "academic"
    CREATIVE = "creative"
    SIMPLE = "simple"
    EDUCATIONAL = "educational"
    TECH = "tech"
    NATURE = "nature"
    MAGAZINE = "magazine"
    TED = "ted"


# ==================== 请求模型 ====================

class PPTOutlineRequest(BaseModel):
    """PPT大纲生成请求"""
    topic: str = Field(..., min_length=1, max_length=200, description="PPT主题")
    style: PPTStyle = Field(default=PPTStyle.BUSINESS, description="PPT风格")
    slides: int = Field(default=10, ge=1, le=50, description="幻灯片数量")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "人工智能的发展趋势",
                "style": "business",
                "slides": 10
            }
        }


class PPTGenerateRequest(PPTOutlineRequest):
    """PPT生成请求"""
    include_speech_notes: bool = Field(default=False, description="是否包含演讲稿")
    custom_search_results: Optional[List[Dict]] = Field(
        default=None,
        description="自定义搜索结果"
    )
    convert_to_pptx: bool = Field(default=True, description="是否转换为PPTX")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "人工智能的发展趋势",
                "style": "business",
                "slides": 10,
                "include_speech_notes": False,
                "convert_to_pptx": True
            }
        }


class ConversionRequest(BaseModel):
    """转换为PPTX请求"""
    enable_llm_fix: bool = Field(default=True, description="是否启用LLM修复")
    skip_failed_files: bool = Field(default=True, description="是否跳过失败的文件")

    class Config:
        json_schema_extra = {
            "example": {
                "enable_llm_fix": True,
                "skip_failed_files": True
            }
        }


# ==================== 响应模型 ====================

class PPTOutlineResponse(BaseModel):
    """PPT大纲生成响应"""
    outline: Dict[str, Any] = Field(description="PPT大纲数据")
    estimated_slides: int = Field(description="预估幻灯片数量")
    estimated_time: str = Field(description="预估生成时间")

    class Config:
        json_schema_extra = {
            "example": {
                "outline": {
                    "title": "人工智能的发展趋势",
                    "pages": [...]
                },
                "estimated_slides": 10,
                "estimated_time": "3-5分钟"
            }
        }


class PPTGenerateResponse(BaseModel):
    """PPT生成响应"""
    project_id: str = Field(description="项目ID")
    ppt_dir: str = Field(description="PPT目录路径")
    total_slides: int = Field(description="总幻灯片数")
    index_page: str = Field(description="导航页路径")
    presenter_page: str = Field(description="演示页路径")
    pptx_file: Optional[str] = Field(default=None, description="PPTX文件路径")
    status: str = Field(description="状态 (completed/failed)")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "20250107_143052_人工智能的发展趋势",
                "ppt_dir": "storage/20250107_143052_人工智能的发展趋势/reports/ppt/slides",
                "total_slides": 10,
                "index_page": "storage/.../index.html",
                "presenter_page": "storage/.../presenter.html",
                "pptx_file": "storage/.../output.pptx",
                "status": "completed"
            }
        }


class ConversionResponse(BaseModel):
    """PPTX转换响应"""
    task_id: str = Field(description="任务ID")
    status: str = Field(description="转换状态")
    pptx_path: str = Field(description="PPTX文件路径")
    conversion_stats: Dict[str, Any] = Field(description="转换统计信息")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "uuid",
                "status": "completed",
                "pptx_path": "storage/.../output.pptx",
                "conversion_stats": {
                    "total": 10,
                    "success": 10,
                    "failed": 0,
                    "elapsed_time": 45.2
                }
            }
        }


class ProjectStatusResponse(BaseModel):
    """项目状态响应"""
    project_id: str = Field(description="项目ID")
    status: str = Field(description="项目状态")
    created_at: str = Field(description="创建时间")
    files: List[str] = Field(description="文件列表")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "20250107_143052_人工智能的发展趋势",
                "status": "completed",
                "created_at": "2025-01-07T14:30:00",
                "files": ["index.html", "presenter.html", "output.pptx"]
            }
        }


class DownloadRequest(BaseModel):
    """文件下载请求参数（用于路径参数）"""
    file_type: str = Field(description="文件类型 (html/pptx/all)")
