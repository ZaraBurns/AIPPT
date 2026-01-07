"""
API相关数据模型
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class PPTProjectInfo(BaseModel):
    """PPT项目信息"""
    project_id: str
    topic: str
    status: str
    created_at: str
    ppt_dir: Optional[str] = None
    total_slides: Optional[int] = None
    pptx_file: Optional[str] = None


class ConversionStats(BaseModel):
    """转换统计信息"""
    total: int
    success: int
    failed: int
    direct: int = 0
    llm: int = 0
    elapsed_time: float = 0.0
