"""新闻搜索模块"""

from src.news_searcher.base import BaseNewsSearcher
from src.news_searcher.serpapi_searcher import SerpAPISearcher

__all__ = ["BaseNewsSearcher", "SerpAPISearcher"]