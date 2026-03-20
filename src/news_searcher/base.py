"""新闻搜索基类"""
from abc import ABC, abstractmethod
from typing import List
from src.models.schemas import NewsArticle


class BaseNewsSearcher(ABC):
    """新闻搜索抽象基类"""

    @abstractmethod
    def search(self, keywords: List[str], max_results: int = 10) -> List[NewsArticle]:
        """搜索新闻

        Args:
            keywords: 搜索关键词列表
            max_results: 最大结果数

        Returns:
            新闻文章列表
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """获取搜索器名称"""
        pass