"""控制台输出模块"""
from typing import List
from src.output.base import BaseOutput
from src.models.schemas import NewsSummary, DailyNewsReport
from src.utils.logger import get_logger

logger = get_logger()


class ConsoleOutput(BaseOutput):
    """控制台输出"""

    def output(self, report: DailyNewsReport) -> bool:
        """输出报告到控制台"""
        try:
            print("\n" + "=" * 60)
            print(f"📰 AI新闻日报 - {report.date}")
            print("=" * 60)
            print(f"共 {report.total_count} 条新闻\n")

            for i, summary in enumerate(report.summaries, 1):
                print(f"\n【{i}】{summary.article.title}")
                print(f"来源: {summary.article.source or '未知'}")
                print(f"链接: {summary.original_link}")
                print(f"\n{summary.summary}")
                print("-" * 40)

            print("\n" + "=" * 60)
            print(f"生成时间: {report.generated_at}")
            print("=" * 60 + "\n")
            return True

        except Exception as e:
            logger.error(f"控制台输出失败: {e}")
            return False

    def output_summaries(self, summaries: List[NewsSummary]) -> bool:
        """直接输出摘要列表到控制台"""
        try:
            print("\n" + "=" * 60)
            print(f"📰 AI新闻摘要 (共 {len(summaries)} 条)")
            print("=" * 60 + "\n")

            for i, summary in enumerate(summaries, 1):
                print(f"\n【{i}】{summary.article.title}")
                print(f"来源: {summary.article.source or '未知'}")
                print(f"链接: {summary.original_link}")
                print(f"\n{summary.summary}")
                print("-" * 40)

            print("\n")
            return True

        except Exception as e:
            logger.error(f"控制台输出失败: {e}")
            return False