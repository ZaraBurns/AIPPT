"""
统一响应模型
"""
from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """
    统一API响应格式

    Args:
        code: 状态码 (200=成功, 400=客户端错误, 500=服务器错误)
        message: 响应消息
        data: 响应数据
        request_id: 请求ID（用于追踪）
        timestamp: 响应时间戳
    """
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="请求ID"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="响应时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": {},
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-01-07T14:30:00"
            }
        }

    @classmethod
    def success(cls, data: Any = None, message: str = "success") -> "APIResponse[T]":
        """创建成功响应"""
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, message: str, code: int = 500, data: Any = None) -> "APIResponse[T]":
        """创建错误响应"""
        return cls(code=code, message=message, data=data)

    @classmethod
    def not_found(cls, message: str = "Resource not found") -> "APIResponse[T]":
        """创建404响应"""
        return cls(code=404, message=message)

    @classmethod
    def bad_request(cls, message: str, data: Any = None) -> "APIResponse[T]":
        """创建400响应"""
        return cls(code=400, message=message, data=data)


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应格式

    Args:
        items: 数据列表
        total: 总数量
        page: 当前页码
        page_size: 每页大小
        pages: 总页数
    """
    items: list[T] = Field(description="数据列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
    pages: int = Field(description="总页数")

    @classmethod
    def create(
        cls,
        items: list,
        total: int,
        page: int = 1,
        page_size: int = 10
    ) -> "PaginatedResponse[T]":
        """创建分页响应"""
        pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )
