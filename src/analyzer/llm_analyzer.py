"""LLM新闻分析模块"""
import os
import asyncio
import httpx
from typing import List, Optional
from pathlib import Path
from src.models.schemas import NewsContent, NewsSummary, NewsArticle
from src.utils.logger import get_logger
from src.utils.config_loader import config

logger = get_logger()


class LLMAnalyzer:
    """LLM新闻分析器"""

    def __init__(self, provider: str = None, model: str = None):
        """初始化LLM分析器

        Args:
            provider: LLM提供商，默认从配置文件读取
            model: 模型名称，默认从配置文件读取
        """
        self.provider = provider or config.get("llm.provider", "minimax")
        self.model = model or config.get("llm.model", "MiniMax-Text-01")
        self._setup_llm()
        self._load_prompt_template()

    def _setup_llm(self):
        """设置LLM客户端"""
        if self.provider == "minimax":
            api_key = os.getenv("MINIMAX_API_KEY")
            if not api_key:
                raise ValueError("MINIMAX_API_KEY未设置，请检查环境变量配置")

            self.api_key = api_key
            self.base_url = "https://api.minimax.chat/v1"
            logger.info(f"初始化Minimax LLM: {self.model}")

        elif self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY未设置")
            self.api_key = api_key
            self.base_url = "https://api.openai.com/v1"
            logger.info(f"初始化OpenAI LLM: {self.model}")

        elif self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY未设置")
            self.api_key = api_key
            self.base_url = "https://api.anthropic.com/v1"
            logger.info(f"初始化Anthropic LLM: {self.model}")

        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")

        self.client = httpx.AsyncClient(timeout=120)

    def _load_prompt_template(self):
        """加载提示词模板"""
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "summarize_prompt.txt"

        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.prompt_template = f.read()
            logger.debug(f"加载提示词模板: {prompt_path}")
        else:
            # 使用内置默认模板
            self.prompt_template = """根据以下新闻内容生成摘要：

标题: {title}
来源: {source}
链接: {url}
正文: {content}

要求：
1. 只基于提供的正文内容进行总结，不得添加原文未提及的信息
2. 生成3-5个关键点
3. 保持原文链接

请按以下格式输出：
标题: {title}
来源: {source}
链接: {url}
摘要: [在这里写摘要]
关键点:
- [关键点1]
- [关键点2]
- [关键点3]"""
            logger.warning(f"提示词模板文件不存在，使用内置模板")

    def _build_prompt(self, news_content: NewsContent) -> str:
        """构建提示词

        Args:
            news_content: 新闻内容对象

        Returns:
            格式化后的提示词
        """
        return self.prompt_template.format(
            title=news_content.article.title,
            source=news_content.article.source or "未知",
            url=news_content.article.url,
            content=news_content.content[:8000]  # 限制内容长度
        )

    async def _call_minimax(self, prompt: str) -> str:
        """调用Minimax API

        Args:
            prompt: 提示词

        Returns:
            LLM响应文本
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        result = response.json()
        logger.debug(f"Minimax API原始响应: {result}")

        # 尝试从响应中提取文本内容
        # 尝试标准OpenAI格式
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if isinstance(choice, dict):
                if "message" in choice and isinstance(choice["message"], dict):
                    return choice["message"].get("content", "")
                if "text" in choice:
                    return choice["text"]

        # MiniMax特有格式
        if "output" in result:
            return str(result["output"])
        if "text" in result:
            return str(result["text"])
        if "completion" in result:
            return str(result["completion"])

        logger.error(f"无法从响应中提取内容: {result}")
        return ""

    async def _call_openai(self, prompt: str) -> str:
        """调用OpenAI API

        Args:
            prompt: 提示词

        Returns:
            LLM响应文本
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    async def _call_anthropic(self, prompt: str) -> str:
        """调用Anthropic API

        Args:
            prompt: 提示词

        Returns:
            LLM响应文本
        """
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }

        response = await self.client.post(
            f"{self.base_url}/messages",
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        result = response.json()
        return result["content"][0]["text"]

    async def analyze_async(self, news_content: NewsContent) -> Optional[NewsSummary]:
        """异步分析单条新闻

        Args:
            news_content: 新闻内容对象

        Returns:
            新闻摘要对象，失败返回None
        """
        try:
            logger.debug(f"分析新闻: {news_content.article.title[:30]}...")

            # 构建提示词
            prompt = self._build_prompt(news_content)

            # 调用LLM
            if self.provider == "minimax":
                summary_text = await self._call_minimax(prompt)
            elif self.provider == "openai":
                summary_text = await self._call_openai(prompt)
            elif self.provider == "anthropic":
                summary_text = await self._call_anthropic(prompt)
            else:
                raise ValueError(f"不支持的LLM提供商: {self.provider}")

            # 解析输出（简化处理，直接使用原始响应）
            return NewsSummary(
                article=news_content.article,
                summary=summary_text,
                key_points=[],  # 关键点从summary中提取
                original_link=news_content.article.url,
                generated_at=news_content.fetched_at
            )

        except Exception as e:
            import traceback
            logger.error(f"分析新闻失败: {type(e).__name__}: {e}")
            logger.error(f"堆栈: {traceback.format_exc()}")
            return None

    def analyze(self, news_content: NewsContent) -> Optional[NewsSummary]:
        """分析单条新闻（同步版本）

        Args:
            news_content: 新闻内容对象

        Returns:
            新闻摘要对象，失败返回None
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.analyze_async(news_content))

    async def analyze_batch_async(self, news_contents: List[NewsContent]) -> List[NewsSummary]:
        """异步批量分析新闻

        Args:
            news_contents: 新闻内容列表

        Returns:
            成功分析的摘要列表
        """
        logger.info(f"开始批量分析 {len(news_contents)} 条新闻")

        tasks = [self.analyze_async(content) for content in news_contents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        summaries = [r for r in results if isinstance(r, NewsSummary)]

        logger.info(f"批量分析完成，成功 {len(summaries)}/{len(news_contents)} 条")
        return summaries

    async def select_top_n(self, summaries: List[NewsSummary], n: int = 10) -> List[NewsSummary]:
        """从新闻摘要列表中选择Top N条最重要的新闻

        Args:
            summaries: 新闻摘要列表
            n: 选择数量，默认10

        Returns:
            选中的Top N条新闻摘要
        """
        import json
        import re

        if len(summaries) <= n:
            logger.info(f"新闻数量({len(summaries)}) <= {n}，直接返回全部")
            return summaries

        logger.info(f"开始从 {len(summaries)} 条新闻中选择 Top {n} 条")

        # 构建新闻列表
        news_list = []
        for i, s in enumerate(summaries, 1):
            news_list.append(f"{i}. {s.article.title} | 来源:{s.article.source or '未知'} | 摘要:{s.summary[:100]}...")
        news_text = "\n".join(news_list)

        prompt = f"""你是一个资深的AI新闻编辑。请从以下{len(summaries)}条新闻中选择{n}条最重要的新闻。

选择标准：
1. 新闻价值高（对行业发展有重大影响）
2. 时效性强（最新发生的重大事件）
3. 受众关注度高（大多数人应该知道）
4. 内容质量好（信息来源可靠、内容完整）

请直接输出JSON数组格式，包含选中的新闻序号（1-{len(summaries)}），按重要性排序：
[1, 5, 8, 3, 2, 6, 9, 10, 4, 7]

只输出JSON数组，不要包含其他内容。

新闻列表：
{news_text}"""

        try:
            if self.provider == "minimax":
                response = await self._call_minimax(prompt)
            elif self.provider == "openai":
                response = await self._call_openai(prompt)
            elif self.provider == "anthropic":
                response = await self._call_anthropic(prompt)
            else:
                raise ValueError(f"不支持的LLM提供商: {self.provider}")

            # 解析JSON响应
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                indices = json.loads(json_match.group())
                top_summaries = [summaries[i-1] for i in indices if 1 <= i <= len(summaries)]
                logger.info(f"Top {n} 选择完成")
                return top_summaries[:n]
            else:
                logger.warning(f"无法解析Top {n}选择结果，直接返回前{n}条")
                return summaries[:n]

        except Exception as e:
            logger.error(f"Top {n}选择失败: {e}")
            return summaries[:n]

    def analyze_batch(self, news_contents: List[NewsContent]) -> List[NewsSummary]:
        """批量分析新闻

        Args:
            news_contents: 新闻内容列表

        Returns:
            成功分析的摘要列表
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.analyze_batch_async(news_contents))

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
