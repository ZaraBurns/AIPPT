"""搜索器基类 - 延迟导入 Playwright 避免不必要的资源占用"""

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

# 使用 TYPE_CHECKING 避免顶层导入 Playwright
if TYPE_CHECKING:
    from playwright.async_api import Page

from ..models.search import SearchLink


class BaseSearcher(ABC):
    """TODO: Add docstring."""
    
    def __init__(self, topk: int = 5):
        self.topk = topk
    
    @abstractmethod
    async def search(self, page: "Page", query: str) -> List[SearchLink]:
        """
        搜索方法(子类必须实现)

        Args:
            page: Playwright 页面对象
            query: 搜索查询词

        Returns:
            搜索结果列表
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """TODO: Add docstring."""
        pass