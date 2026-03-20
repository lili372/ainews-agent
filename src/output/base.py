"""输出模块基类"""
from abc import ABC, abstractmethod
from typing import List
from src.models.schemas import NewsSummary, DailyNewsReport


class BaseOutput(ABC):
    """输出抽象基类"""

    @abstractmethod
    def output(self, report: DailyNewsReport) -> bool:
        """输出报告

        Args:
            report: 新闻报告对象

        Returns:
            是否输出成功
        """
        pass

    @abstractmethod
    def output_summaries(self, summaries: List[NewsSummary]) -> bool:
        """直接输出摘要列表

        Args:
            summaries: 摘要列表

        Returns:
            是否输出成功
        """
        pass