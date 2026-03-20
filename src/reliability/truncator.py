"""文章截断模块"""
from typing import List
from src.models.schemas import NewsContent
from src.utils.logger import get_logger

logger = get_logger()


class Truncator:
    """文章截断器 - 控制内容长度"""

    def __init__(self, max_chars: int = 8000, max_tokens: int = 4000):
        """初始化截断器

        Args:
            max_chars: 最大字符数
            max_tokens: 最大token数（估算：1 token ≈ 4 字符）
        """
        self.max_chars = max_chars
        self.max_tokens = max_tokens

    def truncate(self, news_content: NewsContent) -> NewsContent:
        """截断单条新闻内容

        Args:
            news_content: 新闻内容对象

        Returns:
            截断后的新闻内容对象
        """
        original_len = news_content.content_length

        # 按字符截断
        if news_content.content_length > self.max_chars:
            truncated_content = news_content.content[:self.max_chars]

            # 尝试在句号或段落后截断，避免句子不完整
            last_period = max(
                truncated_content.rfind('。'),
                truncated_content.rfind('.'),
                truncated_content.rfind('\n')
            )

            if last_period > self.max_chars * 0.8:  # 如果句号在80%位置之后
                truncated_content = truncated_content[:last_period + 1]

            logger.debug(f"截断新闻: {news_content.article.title[:30]}... ({original_len} -> {len(truncated_content)} 字符)")

            return NewsContent(
                article=news_content.article,
                content=truncated_content,
                content_length=len(truncated_content),
                language=news_content.language,
                fetched_at=news_content.fetched_at
            )

        return news_content

    def truncate_batch(self, news_contents: List[NewsContent]) -> List[NewsContent]:
        """批量截断新闻内容

        Args:
            news_contents: 新闻内容列表

        Returns:
            截断后的新闻内容列表
        """
        truncated = []
        for content in news_contents:
            truncated.append(self.truncate(content))

        total_original = sum(c.content_length for c in news_contents)
        total_truncated = sum(c.content_length for c in truncated)

        if total_truncated < total_original:
            logger.info(f"批量截断: {total_original} -> {total_truncated} 字符")

        return truncated