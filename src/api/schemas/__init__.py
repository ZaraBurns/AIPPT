"""
API数据模型
"""
from .common import APIResponse, PaginatedResponse
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
    "PaginatedResponse",
    "PPTOutlineRequest",
    "PPTGenerateRequest",
    "PPTOutlineResponse",
    "PPTGenerateResponse",
    "ConversionRequest",
    "ConversionResponse",
    "DownloadRequest",
]
