"""
API数据模型
"""
from .common import APIResponse
from .ppt import (
    PPTOutlineRequest,
    PPTGenerateRequest,
    PPTOutlineResponse,
    PPTGenerateResponse,
    ConversionRequest,
    ConversionResponse,
    DownloadRequest
)

__all__ = [
    "APIResponse",
    "PPTOutlineRequest",
    "PPTGenerateRequest",
    "PPTOutlineResponse",
    "PPTGenerateResponse",
    "ConversionRequest",
    "ConversionResponse",
    "DownloadRequest",
]
