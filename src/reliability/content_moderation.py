# -*- coding: utf-8 -*-
"""
敏感内容过滤模块

基于敏感词列表进行内容过滤，支持自定义敏感词。
预留了扩展接口，可接入第三方审核API。
"""

import re
from typing import List, Set, Optional, Dict, Callable
from loguru import logger


class ContentModeration:
    """
    敏感内容过滤器

    提供以下功能：
    - 敏感词检测
    - 广告内容检测
    - 可扩展的审核接口
    """

    def __init__(
        self,
        sensitive_keywords: Optional[List[str]] = None,
        ad_keywords: Optional[List[str]] = None,
        block_on_match: bool = True
    ):
        """
        初始化内容过滤器

        Args:
            sensitive_keywords: 敏感词列表
            ad_keywords: 广告关键词列表
            block_on_match: 匹配时是阻止还是标记（True=阻止，False=标记）
        """
        # 默认敏感词列表（示例，实际使用时请根据需要配置）
        self.sensitive_keywords: Set[str] = set(sensitive_keywords) if sensitive_keywords else set()
        self.ad_keywords: Set[str] = set(ad_keywords) if ad_keywords else set()

        # 预留的外部审核函数
        self._external_moderator: Optional[Callable] = None

        # 是否在匹配时阻止
        self.block_on_match = block_on_match

    def moderate(self, text: str) -> Dict:
        """
        对文本进行内容审核

        Args:
            text: 要审核的文本

        Returns:
            审核结果字典
        """
        if not text:
            return {
                'is_safe': True,
                'has_sensitive': False,
                'has_ad': False,
                'matched_keywords': [],
                'reason': None
            }

        result = {
            'is_safe': True,
            'has_sensitive': False,
            'has_ad': False,
            'matched_keywords': [],
            'reason': None
        }

        # 检查敏感词
        sensitive_matches = self._check_keywords(text, self.sensitive_keywords)
        if sensitive_matches:
            result['has_sensitive'] = True
            result['matched_keywords'].extend(sensitive_matches)
            result['is_safe'] = self.block_on_match is False
            result['reason'] = f"包含敏感词: {', '.join(sensitive_matches[:5])}"
            if len(sensitive_matches) > 5:
                result['reason'] += f" 等{len(sensitive_matches)}个"

        # 检查广告词
        ad_matches = self._check_keywords(text, self.ad_keywords)
        if ad_matches:
            result['has_ad'] = True
            result['matched_keywords'].extend(ad_matches)
            result['reason'] = f"包含广告词: {', '.join(ad_matches[:5])}"
            if len(ad_matches) > 5:
                result['reason'] += f" 等{len(ad_matches)}个"

        # 调用外部审核（如果有）
        if self._external_moderator and result['is_safe']:
            try:
                external_result = self._external_moderator(text)
                if external_result.get('is_safe') is False:
                    result['is_safe'] = self.block_on_match is False
                    result['reason'] = external_result.get('reason', '外部审核未通过')
                    result['external_moderation'] = external_result
            except Exception as e:
                logger.error(f"外部审核调用失败: {str(e)}")

        if not result['is_safe']:
            logger.warning(f"内容审核未通过: {result['reason']}")

        return result

    def _check_keywords(self, text: str, keywords: Set[str]) -> List[str]:
        """
        检查文本中是否包含关键词

        Args:
            text: 文本
            keywords: 关键词集合

        Returns:
            匹配的关键词列表
        """
        if not keywords:
            return []

        text_lower = text.lower()
        matched = []

        for keyword in keywords:
            # 使用正则表达式进行大小写不敏感匹配
            pattern = re.escape(keyword.lower())
            if re.search(pattern, text_lower):
                matched.append(keyword)

        return matched

    def moderate_article(self, article: dict) -> Dict:
        """
        审核整篇文章

        Args:
            article: 文章字典，应包含title、content等字段

        Returns:
            审核结果字典
        """
        # 合并标题和内容进行审核
        title = article.get('title', '')
        content = article.get('content', article.get('summary', ''))
        text = f"{title}\n{content}"

        result = self.moderate(text)

        # 添加文章信息
        result['article_title'] = title

        return result

    def filter_articles(self, articles: List[dict]) -> List[dict]:
        """
        过滤文章列表

        Args:
            articles: 文章列表

        Returns:
            过滤后的文章列表
        """
        if not articles:
            return []

        filtered = []
        blocked_count = 0

        for article in articles:
            result = self.moderate_article(article)

            if result['is_safe']:
                # 添加审核信息到文章
                article['moderation_result'] = result
                filtered.append(article)
            else:
                blocked_count += 1
                logger.debug(
                    f"文章审核阻止: {article.get('title', 'Unknown')}, "
                    f"原因: {result['reason']}"
                )

        if blocked_count > 0:
            logger.info(f"内容审核: 阻止 {blocked_count} 条问题文章")

        return filtered

    def check_title(self, title: str) -> Dict:
        """
        专门检查标题

        Args:
            title: 标题

        Returns:
            审核结果
        """
        return self.moderate(title)

    def add_sensitive_keyword(self, keyword: str):
        """
        添加敏感词

        Args:
            keyword: 敏感词
        """
        self.sensitive_keywords.add(keyword)
        logger.debug(f"添加敏感词: {keyword}")

    def remove_sensitive_keyword(self, keyword: str):
        """
        移除敏感词

        Args:
            keyword: 敏感词
        """
        self.sensitive_keywords.discard(keyword)
        logger.debug(f"移除敏感词: {keyword}")

    def add_ad_keyword(self, keyword: str):
        """
        添加广告词

        Args:
            keyword: 广告词
        """
        self.ad_keywords.add(keyword)
        logger.debug(f"添加广告词: {keyword}")

    def remove_ad_keyword(self, keyword: str):
        """
        移除广告词

        Args:
            keyword: 广告词
        """
        self.ad_keywords.discard(keyword)
        logger.debug(f"移除广告词: {keyword}")

    def set_external_moderator(self, moderator: Callable[[str], Dict]):
        """
        设置外部审核函数

        Args:
            moderator: 接收文本，返回审核结果字典的函数
                      返回格式: {'is_safe': bool, 'reason': str}
        """
        self._external_moderator = moderator
        logger.info("已设置外部审核函数")

    def clear_keywords(self):
        """
        清空所有关键词
        """
        self.sensitive_keywords.clear()
        self.ad_keywords.clear()
        logger.debug("已清空所有关键词")

    def get_keywords_stats(self) -> Dict:
        """
        获取关键词统计信息

        Returns:
            统计信息字典
        """
        return {
            'sensitive_keywords_count': len(self.sensitive_keywords),
            'ad_keywords_count': len(self.ad_keywords),
            'sensitive_keywords': list(self.sensitive_keywords)[:20],  # 最多显示20个
            'ad_keywords': list(self.ad_keywords)[:20]
        }
