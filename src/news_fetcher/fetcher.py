"""新闻内容获取模块"""
import httpx
import trafilatura
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List
from datetime import datetime
from src.models.schemas import NewsArticle, NewsContent
from src.utils.logger import get_logger

logger = get_logger()

# 线程池用于执行同步的trafilatura操作
_executor = ThreadPoolExecutor(max_workers=10)


class NewsFetcher:
    """新闻内容获取器"""

    def __init__(self, timeout: int = 10, max_retries: int = 2):
        """初始化新闻获取器

        Args:
            timeout: 请求超时时间（秒），默认10秒
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=timeout)

    async def fetch(self, article: NewsArticle) -> Optional[NewsContent]:
        """获取单条新闻的完整内容

        Args:
            article: 新闻文章基础信息

        Returns:
            包含完整内容的新闻对象，失败返回None
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"获取新闻: {article.title[:30]}... (尝试 {attempt + 1})")

                # 使用线程池执行同步的trafilatura操作，添加超时控制
                loop = asyncio.get_event_loop()
                try:
                    downloaded = await asyncio.wait_for(
                        loop.run_in_executor(_executor, trafilatura.fetch_url, article.url),
                        timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"获取超时 (尝试 {attempt + 1}/{self.max_retries}): {article.url}")
                    continue

                if downloaded:
                    content = trafilatura.extract(downloaded)
                    if content:
                        content_length = len(content)
                        logger.debug(f"成功提取内容，长度: {content_length} 字符")

                        return NewsContent(
                            article=article,
                            content=content,
                            content_length=content_length,
                            fetched_at=datetime.now()
                        )

                # 如果trafilatura失败，尝试直接获取（也加上超时）
                try:
                    response = await asyncio.wait_for(
                        self.client.get(article.url),
                        timeout=self.timeout
                    )
                    response.raise_for_status()

                    # 使用线程池执行extract
                    content = await loop.run_in_executor(
                        _executor, trafilatura.extract, response.text
                    )
                    if content:
                        return NewsContent(
                            article=article,
                            content=content,
                            content_length=len(content),
                            fetched_at=datetime.now()
                        )
                except asyncio.TimeoutError:
                    logger.warning(f"直接获取超时 (尝试 {attempt + 1}/{self.max_retries}): {article.url}")
                    continue

            except Exception as e:
                logger.warning(f"获取失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"最终放弃获取: {article.url}")

        return None

    async def fetch_batch(self, articles: List[NewsArticle]) -> List[NewsContent]:
        """批量获取新闻内容

        Args:
            articles: 新闻文章列表

        Returns:
            成功获取的新闻内容列表
        """
        logger.info(f"开始批量获取 {len(articles)} 条新闻内容")
        start_time = datetime.now()

        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(3)  # 最多同时3个请求

        async def fetch_with_progress(article, index):
            async with semaphore:
                logger.info(f"进度: [{index+1}/{len(articles)}] 正在获取...")
                result = await self.fetch(article)
                if result:
                    logger.debug(f"[{index+1}/{len(articles)}] 成功: {article.title[:30]}...")
                else:
                    logger.debug(f"[{index+1}/{len(articles)}] 失败: {article.title[:30]}...")
                return result

        tasks = [fetch_with_progress(article, i) for i, article in enumerate(articles)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = [r for r in results if isinstance(r, NewsContent)]
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"批量获取完成，耗时{elapsed:.1f}秒，成功 {len(valid_results)}/{len(articles)} 条")

        return valid_results

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
