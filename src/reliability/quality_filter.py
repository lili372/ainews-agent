"""内容质量过滤模块"""
from typing import List, Set
from difflib import SequenceMatcher
from src.models.schemas import NewsArticle
from src.utils.logger import get_logger

logger = get_logger()


class QualityFilter:
    """内容质量过滤器"""

    def __init__(self, similarity_threshold: float = 0.8):
        """初始化过滤器

        Args:
            similarity_threshold: 相似度阈值，超过此值认为是重复
        """
        self.similarity_threshold = similarity_threshold
        self.low_quality_keywords = [
            "标题党", "震惊", "惊人", "必看", "转发"
        ]

    def filter(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """过滤低质量和重复新闻

        Args:
            articles: 新闻列表

        Returns:
            过滤后的新闻列表
        """
        # 第一步：标题党检测
        articles = self._filter_clickbait(articles)

        # 第二步：相似度去重
        articles = self._deduplicate(articles)

        return articles

    def _filter_clickbait(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """过滤标题党新闻"""
        filtered = []

        for article in articles:
            title_lower = article.title.lower()
            is_clickbait = any(kw in title_lower for kw in self.low_quality_keywords)

            if is_clickbait:
                logger.debug(f"过滤标题党: {article.title[:30]}")
            else:
                filtered.append(article)

        return filtered

    def _deduplicate(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """基于相似度去重"""
        if not articles:
            return []

        unique: List[NewsArticle] = []

        for article in articles:
            is_duplicate = False

            for existing in unique:
                # 计算标题相似度
                similarity = SequenceMatcher(
                    None,
                    article.title,
                    existing.title
                ).ratio()

                # 计算摘要相似度
                snippet_sim = 0.0
                if article.snippet and existing.snippet:
                    snippet_sim = SequenceMatcher(
                        None,
                        article.snippet,
                        existing.snippet
                    ).ratio()

                if similarity > self.similarity_threshold or snippet_sim > self.similarity_threshold:
                    is_duplicate = True
                    logger.debug(f"去重: '{article.title[:30]}' 与 '{existing.title[:30]}' 相似")
                    break

            if not is_duplicate:
                unique.append(article)

        removed = len(articles) - len(unique)
        if removed > 0:
            logger.info(f"质量过滤: 移除 {removed} 条重复/低质量新闻")

        return unique