"""时效性过滤模块"""
from datetime import datetime, timedelta
from typing import List
from src.models.schemas import NewsArticle
from src.utils.logger import get_logger

logger = get_logger()


class FreshnessFilter:
    """时效性过滤器 - 过滤过期新闻"""

    def __init__(self, max_age_hours: int = 24):
        """初始化过滤器

        Args:
            max_age_hours: 最大时效时间（小时）
        """
        self.max_age_hours = max_age_hours

    def filter(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """过滤过期新闻

        Args:
            articles: 新闻列表

        Returns:
            过滤后的新闻列表
        """
        now = datetime.now()
        cutoff_time = now - timedelta(hours=self.max_age_hours)

        filtered = []
        for article in articles:
            if article.published_at is None:
                # 如果没有发布时间，保守起见保留
                filtered.append(article)
                logger.debug(f"保留无发布时间新闻: {article.title[:30]}")
            elif article.published_at >= cutoff_time:
                filtered.append(article)
            else:
                logger.debug(f"过滤过期新闻: {article.title[:30]}")

        removed_count = len(articles) - len(filtered)
        if removed_count > 0:
            logger.info(f"时效性过滤: 移除 {removed_count} 条过期新闻")

        return filtered