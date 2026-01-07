"""Search models"""

from pydantic import BaseModel
from typing import Optional


class SearchLink(BaseModel):
    """搜索结果链接模型"""
    url: str
    title: str
    snippet: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
