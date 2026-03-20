# -*- coding: utf-8 -*-
"""
多语言处理模块

使用langdetect检测语言，根据配置的语言列表过滤新闻。
"""

from typing import List, Set, Optional, Dict
from loguru import logger

try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect未安装，语言检测功能将不可用")


class MultiLanguageHandler:
    """
    多语言处理器

    支持：
    - 语言检测
    - 语言过滤
    - 多语言新闻处理
    """

    # 支持的语言代码到中文名称的映射
    LANGUAGE_NAMES = {
        'zh-cn': '简体中文',
        'zh-tw': '繁体中文',
        'zh': '中文',
        'en': '英语',
        'ja': '日语',
        'ko': '韩语',
        'fr': '法语',
        'de': '德语',
        'es': '西班牙语',
        'pt': '葡萄牙语',
        'ru': '俄语',
        'ar': '阿拉伯语',
        'hi': '印地语',
        'th': '泰语',
        'vi': '越南语',
        'id': '印尼语',
        'ms': '马来语',
        'tr': '土耳其语',
        'pl': '波兰语',
        'nl': '荷兰语',
        'it': '意大利语',
    }

    def __init__(
        self,
        allowed_languages: Optional[List[str]] = None,
        detect_threshold: float = 0.7,
        fallback_language: str = 'en'
    ):
        """
        初始化多语言处理器

        Args:
            allowed_languages: 允许的语言代码列表，如['zh-cn', 'en']
                              如果为None，则保留所有语言
            detect_threshold: 语言检测置信度阈值（0-1）
            fallback_language: 检测失败时的默认语言
        """
        self.allowed_languages: Set[str] = set(allowed_languages) if allowed_languages else set()
        self.detect_threshold = detect_threshold
        self.fallback_language = fallback_language

        if not LANGDETECT_AVAILABLE:
            logger.warning(
                "langdetect库未安装，语言检测功能不可用。"
                "请运行: pip install langdetect"
            )

    def detect_language(self, text: str) -> Optional[str]:
        """
        检测文本语言

        Args:
            text: 要检测的文本

        Returns:
            检测到的语言代码，如检测失败返回None
        """
        if not text or not LANGDETECT_AVAILABLE:
            return None

        try:
            # langdetect返回的是ISO 639-1代码
            lang = detect(text)
            return lang
        except LangDetectException as e:
            logger.debug(f"语言检测失败: {str(e)}")
            return None

    def detect_language_with_confidence(self, text: str) -> Dict:
        """
        检测语言并返回置信度信息

        Args:
            text: 要检测的文本

        Returns:
            包含语言代码和置信度的字典
        """
        if not text or not LANGDETECT_AVAILABLE:
            return {
                'language': self.fallback_language,
                'confidence': 0.0,
                'available': False
            }

        try:
            # 使用langdetect进行检测
            lang = detect(text)
            # langdetect不直接提供置信度，这里返回1.0作为默认值
            return {
                'language': lang,
                'confidence': 1.0,
                'available': True,
                'language_name': self.LANGUAGE_NAMES.get(lang, lang)
            }
        except LangDetectException as e:
            logger.debug(f"语言检测失败: {str(e)}")
            return {
                'language': self.fallback_language,
                'confidence': 0.0,
                'available': False,
                'error': str(e)
            }

    def filter_by_language(self, articles: List[dict]) -> List[dict]:
        """
        根据语言过滤新闻列表

        Args:
            articles: 新闻列表，每条新闻应包含title或content字段

        Returns:
            过滤后的新闻列表
        """
        if not articles:
            return []

        # 如果没有设置语言过滤，直接返回
        if not self.allowed_languages:
            return articles

        filtered = []
        for article in articles:
            # 获取文本进行检测
            text = self._get_text_for_detection(article)

            if not text:
                # 没有文本的新闻默认保留
                filtered.append(article)
                continue

            lang = self.detect_language(text)

            if lang is None:
                # 检测失败的新闻默认保留
                filtered.append(article)
                continue

            # 检查语言是否在允许列表中
            if self._is_language_allowed(lang):
                article['detected_language'] = lang
                article['language_name'] = self.LANGUAGE_NAMES.get(lang, lang)
                filtered.append(article)
            else:
                logger.debug(
                    f"语言过滤移除: {article.get('title', 'Unknown')}, "
                    f"检测到语言: {lang}"
                )

        removed_count = len(articles) - len(filtered)
        if removed_count > 0:
            logger.info(f"语言过滤: 移除 {removed_count} 条不支持语言的新闻")

        return filtered

    def _get_text_for_detection(self, article: dict) -> str:
        """
        从文章中获取用于语言检测的文本

        优先使用标题，然后是摘要，最后是内容

        Args:
            article: 新闻文章

        Returns:
            用于检测的文本
        """
        # 尝试多个字段
        for field in ['title', 'summary', 'snippet', 'content', 'text']:
            text = article.get(field, '').strip()
            if text:
                return text[:500]  # 截取前500字符用于检测
        return ''

    def _is_language_allowed(self, lang: str) -> bool:
        """
        检查语言是否在允许列表中

        支持语言代码的模糊匹配：
        - 'zh' 匹配所有中文变体
        - 'zh-cn' 精确匹配简体中文

        Args:
            lang: 语言代码

        Returns:
            是否允许
        """
        # 精确匹配
        if lang in self.allowed_languages:
            return True

        # 中文模糊匹配
        if lang.startswith('zh') and 'zh' in self.allowed_languages:
            return True

        # 英文模糊匹配
        if lang == 'en' and 'en' in self.allowed_languages:
            return True

        return False

    def add_allowed_language(self, lang: str):
        """
        添加允许的语言

        Args:
            lang: 语言代码
        """
        self.allowed_languages.add(lang)
        logger.debug(f"添加允许的语言: {lang}")

    def remove_allowed_language(self, lang: str):
        """
        移除允许的语言

        Args:
            lang: 语言代码
        """
        self.allowed_languages.discard(lang)
        logger.debug(f"移除允许的语言: {lang}")

    def set_allowed_languages(self, languages: List[str]):
        """
        设置允许的语言列表

        Args:
            languages: 语言代码列表
        """
        self.allowed_languages = set(languages)
        logger.info(f"设置允许的语言: {languages}")

    def get_language_stats(self, articles: List[dict]) -> Dict:
        """
        获取新闻列表的语言分布统计

        Args:
            articles: 新闻列表

        Returns:
            语言统计字典
        """
        stats = {
            'total': len(articles),
            'languages': {},
            'undetected': 0
        }

        for article in articles:
            lang = article.get('detected_language')
            if lang:
                stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
            else:
                stats['undetected'] += 1

        return stats

    def translate_article_field(
        self,
        article: dict,
        field: str,
        target_lang: str = 'zh-cn'
    ) -> dict:
        """
        翻译文章指定字段（预留接口）

        注意：实际的翻译功能需要接入翻译API

        Args:
            article: 文章
            field: 要翻译的字段名
            target_lang: 目标语言

        Returns:
            添加了翻译字段的文章
        """
        # 这是一个预留接口，实际翻译需要接入翻译服务
        logger.debug(f"翻译接口预留: 字段={field}, 目标语言={target_lang}")
        return article

    def is_supported(self) -> bool:
        """
        检查语言检测功能是否可用

        Returns:
            功能是否可用
        """
        return LANGDETECT_AVAILABLE
