"""AI新闻日报 - 主程序入口"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger, get_logger
from src.utils.config_loader import config
from src.utils.cache import NewsCache
from src.models.schemas import NewsArticle, DailyNewsReport
from src.news_searcher.serpapi_searcher import SerpAPISearcher
from src.news_fetcher.fetcher import NewsFetcher
from src.analyzer.llm_analyzer import LLMAnalyzer
from src.output.console_output import ConsoleOutput
from src.output.markdown_output import MarkdownOutput
from src.reliability.freshness_filter import FreshnessFilter
from src.reliability.quality_filter import QualityFilter
from src.reliability.truncator import Truncator
from src.reliability.multi_language import MultiLanguageHandler
from src.reliability.content_moderation import ContentModeration
from src.reliability.feishu_sender import FeishuSender

logger = get_logger()


class AINewsDaily:
    """AI新闻日报主类"""

    def __init__(self):
        """初始化AI新闻日报"""
        # 设置日志
        setup_logger(level=config.get("logging.level", "INFO"))

        # 加载配置
        logger.info("AI新闻日报启动")

        # 初始化各模块
        self._init_modules()

    def _init_modules(self):
        """初始化各模块"""
        # 缓存
        cache_enabled = config.get("cache.enabled", True)
        cache_ttl = config.get("cache.ttl_hours", 1)
        self.cache = NewsCache(ttl_hours=cache_ttl) if cache_enabled else None

        # 搜索器
        self.searcher = SerpAPISearcher()

        # 内容获取器
        self.fetcher = NewsFetcher()

        # LLM分析器
        llm_provider = config.get("llm.provider", "minimax")
        llm_model = config.get("llm.model", "MiniMax-Text-01")
        self.analyzer = LLMAnalyzer(provider=llm_provider, model=llm_model)

        # 过滤器
        freshness_hours = config.get("filter.freshness_hours", 24)
        self.freshness_filter = FreshnessFilter(max_age_hours=freshness_hours)
        self.quality_filter = QualityFilter()

        # 截断器
        max_chars = config.get("filter.max_article_length", 8000)
        self.truncator = Truncator(max_chars=max_chars)

        # 多语言处理器
        supported_langs = config.get("preferences.languages", ["zh", "en"])
        self.lang_processor = MultiLanguageHandler(allowed_languages=supported_langs)

        # 内容审核
        self.content_filter = ContentModeration()

        # 输出器
        self.console_output = ConsoleOutput()
        self.markdown_output = MarkdownOutput()

        # 飞书发送器
        feishu_mention = config.get("output.feishu.mention_all", False)
        self.feishu_sender = FeishuSender(mention_all=feishu_mention)

        logger.info("所有模块初始化完成")

    async def run(self):
        """运行完整流程"""
        try:
            logger.info("=" * 50)
            logger.info("开始获取AI新闻")
            logger.info("=" * 50)

            # 1. 获取搜索关键词
            keywords = config.get("preferences.keywords.include", ["AI", "人工智能"])
            max_results = config.get("news_search.max_results", 20)

            # 2. 搜索新闻
            logger.info(f"搜索关键词: {keywords}")
            articles = self.searcher.search(keywords, max_results)
            logger.info(f"搜索到 {len(articles)} 条新闻")

            if not articles:
                logger.warning("没有搜索到任何新闻")
                return

            # 3. 时效性过滤
            articles = self.freshness_filter.filter(articles)
            logger.info(f"时效性过滤后剩余 {len(articles)} 条")

            # 4. 质量过滤
            articles = self.quality_filter.filter(articles)
            logger.info(f"质量过滤后剩余 {len(articles)} 条")

            if not articles:
                logger.warning("过滤后没有剩余新闻")
                return

            # 5. 获取内容
            logger.info("开始获取新闻内容...")
            news_contents = await self.fetcher.fetch_batch(articles)
            logger.info(f"成功获取 {len(news_contents)} 条内容")

            if not news_contents:
                logger.warning("无法获取任何新闻内容")
                return

            # 6. 语言过滤（暂时跳过，API不匹配）
            # news_contents = self.lang_processor.filter_by_language(news_contents)
            # logger.info(f"语言过滤后剩余 {len(news_contents)} 条")

            # 7. 截断处理
            news_contents = self.truncator.truncate_batch(news_contents)

            # 8. 内容审核（暂时跳过，API不匹配）
            # logger.info(f"内容审核后剩余 {len(news_contents)} 条")

            if not news_contents:
                logger.warning("审核后没有剩余新闻")
                return

            # 9. LLM分析
            logger.info("开始LLM分析...")
            summaries = await self.analyzer.analyze_batch_async(news_contents)
            logger.info(f"成功分析 {len(summaries)} 条新闻")

            if not summaries:
                logger.warning("LLM分析没有返回任何结果")
                return

            # 10. 输出结果
            logger.info("输出结果...")

            # 控制台输出
            self.console_output.output_summaries(summaries)

            # Markdown输出完整版
            self.markdown_output.output_summaries(summaries)

            # LLM选择Top 10
            logger.info("开始选择Top 10精选新闻...")
            top10_summaries = await self.analyzer.select_top_n(summaries, n=10)
            logger.info(f"Top 10选择完成")

            # Markdown输出Top 10
            if top10_summaries:
                self.markdown_output.output_top10(top10_summaries)

            # 飞书推送Top 10
            if top10_summaries:
                await self.feishu_sender.send_card(top10_summaries, title="精选AI新闻Top 10")

            logger.info("=" * 50)
            logger.info("AI新闻日报生成完成")
            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"运行出错: {e}", exc_info=True)

        finally:
            # 清理资源
            await self.fetcher.close()
            await self.analyzer.close()
            await self.feishu_sender.close()


async def main():
    """主函数"""
    app = AINewsDaily()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
