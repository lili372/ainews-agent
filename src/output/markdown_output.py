"""Markdown输出模块"""
from pathlib import Path
from typing import List
from datetime import datetime
from src.output.base import BaseOutput
from src.models.schemas import NewsSummary, DailyNewsReport
from src.utils.logger import get_logger

logger = get_logger()


class MarkdownOutput(BaseOutput):
    """Markdown格式输出"""

    def __init__(self, output_dir: str = "output"):
        """初始化Markdown输出器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def output(self, report: DailyNewsReport) -> bool:
        """输出报告为Markdown文件"""
        try:
            filename = f"ai_news_{report.date}.md"
            filepath = self.output_dir / filename

            content = self._build_markdown(report)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Markdown报告已保存: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Markdown输出失败: {e}")
            return False

    def output_summaries(self, summaries: List[NewsSummary]) -> bool:
        """直接输出摘要列表为Markdown"""
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"ai_news_{date_str}.md"
            filepath = self.output_dir / filename

            content = self._build_markdown_from_summaries(summaries, date_str)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Markdown已保存: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Markdown输出失败: {e}")
            return False

    def output_top10(self, summaries: List[NewsSummary], date_str: str = None) -> bool:
        """输出Top 10精选新闻为Markdown"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"ai_news_top10_{date_str}.md"
            filepath = self.output_dir / filename

            content = self._build_markdown_from_summaries(summaries, date_str, is_top10=True)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Top 10 Markdown已保存: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Top 10 Markdown输出失败: {e}")
            return False

    def _build_markdown(self, report: DailyNewsReport) -> str:
        """构建Markdown内容"""
        lines = [
            f"# AI新闻日报 - {report.date}",
            "",
            f"**生成时间**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**新闻总数**: {report.total_count}",
            "",
            "---",
            ""
        ]

        for i, summary in enumerate(report.summaries, 1):
            lines.append(f"## 【{i}】{summary.article.title}")
            lines.append("")
            lines.append(f"**来源**: {summary.article.source or '未知'}")
            lines.append(f"**链接**: [{summary.original_link}]({summary.original_link})")
            lines.append("")
            lines.append("### 摘要")
            lines.append("")
            lines.append(summary.summary)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _build_markdown_from_summaries(self, summaries: List[NewsSummary], date_str: str, is_top10: bool = False) -> str:
        """从摘要列表构建Markdown"""
        title_prefix = "精选AI新闻Top 10" if is_top10 else "AI新闻日报"
        lines = [
            f"# {title_prefix} - {date_str}",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**新闻总数**: {len(summaries)}",
            "",
            "---",
            ""
        ]

        for i, summary in enumerate(summaries, 1):
            lines.append(f"## 【{i}】{summary.article.title}")
            lines.append("")
            lines.append(f"**来源**: {summary.article.source or '未知'}")
            lines.append(f"**链接**: [{summary.original_link}]({summary.original_link})")
            lines.append("")
            lines.append("### 摘要")
            lines.append("")
            lines.append(summary.summary)
            lines.append("")
            lines.append("---")
            lines.append("")

        if is_top10:
            lines.append("\n> 📊 精选依据：新闻价值、时效性、行业影响力、技术创新性、产业化程度")

        return "\n".join(lines)