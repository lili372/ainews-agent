"""使用SerpAPI的Google新闻搜索实现"""
from typing import List
import os
import time
from src.news_searcher.base import BaseNewsSearcher
from src.models.schemas import NewsArticle
from src.utils.logger import get_logger

logger = get_logger()

# 国内常用新闻域名白名单
CHINESE_NEWS_DOMAINS = {
    # 官方媒体
    'xinhuanet.com', 'news.cn', 'people.com.cn', 'cctv.com', 'china.com',
    'gov.cn', 'chinanews.com', 'gdtv.cn', 'sina.com', 'sohu.com',
    'qq.com', '163.com', 'baidu.com', 'ifeng.com',
    # 商业媒体
    'caixin.com', 'yicai.com', 'cls.cn', 'wallstreetcn.com',
    'eastmoney.com', 'finance.sina.com', 'tech.sina.com',
    'jbk.39.net', 'pinduoduo.com', 'kugou.com',
    # 地方媒体
    'thepaper.cn', 'jiemian.com', 'bjnews.com.cn', 'ydniu.com',
    'qdaily.com', 'time-weekly.com', 'sixthtone.com',
    # 科技媒体
    '36kr.com', 'leiphone.com', 'ithome.com', '虎嗅网', 'huxiu.com',
    'ai', 'it', 'tech', 'keji', 'aijishijian',
    # 其他中文网站
    'cn', 'com.cn', 'net.cn', 'org.cn', 'gov.cn',
}

# 已知境外/不可靠域名黑名单
FOREIGN_DOMAINS_BLACKLIST = {
    'bbc.com', 'reuters.com', 'apnews.com', 'afp.com',
    'dw.com', 'voa.com', 'rfi.fr', 'nthu.com',
}


def is_chinese_news_site(url: str) -> bool:
    """检查URL是否来自国内网站

    Args:
        url: 新闻URL

    Returns:
        是否是国内网站
    """
    url_lower = url.lower()

    # 先检查黑名单
    for domain in FOREIGN_DOMAINS_BLACKLIST:
        if domain in url_lower:
            return False

    # 检查是否是中文域名或国内常见域名
    for domain in CHINESE_NEWS_DOMAINS:
        if domain in url_lower:
            return True

    # 检查是否是.cn结尾的域名
    if '.cn' in url_lower and not url_lower.startswith('http://en.'):
        return True

    return False


class SerpAPISearcher(BaseNewsSearcher):
    """SerpAPI Google新闻搜索器"""

    def __init__(self, api_key: str = None, timeout: int = 15):
        """初始化SerpAPI搜索器

        Args:
            api_key: SerpAPI密钥，默认从环境变量获取
            timeout: 超时时间（秒），默认15秒
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY未设置，请检查环境变量配置")

    def search(self, keywords: List[str], max_results: int = 10) -> List[NewsArticle]:
        """使用SerpAPI搜索Google新闻

        Args:
            keywords: 搜索关键词列表
            max_results: 最大结果数

        Returns:
            新闻文章列表
        """
        try:
            from serpapi import Client
        except ImportError:
            logger.error("请先安装 serpapi: pip install serpapi")
            raise

        # 构建搜索查询
        query = " OR ".join(keywords) if len(keywords) > 1 else keywords[0]
        logger.info(f"开始搜索，关键词: {query}")

        all_articles = []

        try:
            client = Client(api_key=self.api_key, timeout=self.timeout)

            # 显示进度
            logger.info("正在请求SerpAPI...")
            start_time = time.time()

            # 使用news引擎进行搜索
            results = client.search(
                engine="google_news",
                q=query,
                num=max_results,
                gl="cn",  # 中国地区
                hl="zh-CN"  # 中文
            )

            elapsed = time.time() - start_time
            logger.info(f"搜索完成，耗时: {elapsed:.1f}秒")

            # 解析结果
            news_results = results.get("news_results", [])
            logger.info(f"发现 {len(news_results)} 条新闻")

            for i, item in enumerate(news_results):
                url = item.get("link", "")

                # 过滤非国内网站
                if not is_chinese_news_site(url):
                    logger.debug(f"[{i+1}] 跳过境外网站: {url}")
                    continue

                logger.debug(f"解析新闻 {i+1}/{len(news_results)}: {item.get('title', '')[:30]}...")
                article = NewsArticle(
                    title=item.get("title", ""),
                    url=url,
                    source=item.get("source", {}).get("name") if isinstance(item.get("source"), dict) else item.get("source"),
                    snippet=item.get("snippet", ""),
                )
                all_articles.append(article)

            logger.info(f"SerpAPI搜索完成，筛选后剩余 {len(all_articles)} 条国内新闻")

        except Exception as e:
            logger.error(f"SerpAPI搜索失败: {e}")

        return all_articles

    def get_name(self) -> str:
        return "serpapi"
