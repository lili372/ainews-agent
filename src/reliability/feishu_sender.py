"""飞书推送模块"""
import os
import httpx
from typing import List, Optional
from src.models.schemas import NewsSummary
from src.utils.logger import get_logger

logger = get_logger()


class FeishuSender:
    """飞书Webhook消息发送器"""

    def __init__(self, webhook_url: str = None, mention_all: bool = False):
        """初始化飞书发送器

        Args:
            webhook_url: 飞书Webhook地址，默认从环境变量获取
            mention_all: 是否@所有人
        """
        self.webhook_url = webhook_url or os.getenv("FEISHU_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("FEISHU_WEBHOOK_URL未设置，请检查环境变量配置")

        self.mention_all = mention_all
        self.client = httpx.AsyncClient(timeout=30)

    async def send(self, content: str) -> bool:
        """发送文本消息到飞书

        Args:
            content: 消息内容（支持Markdown）

        Returns:
            是否发送成功
        """
        try:
            payload = {
                "msg_type": "text",
                "content": {
                    "text": content
                }
            }

            response = await self.client.post(
                self.webhook_url,
                json=payload
            )
            response.raise_for_status()

            logger.info("飞书消息发送成功")
            return True

        except Exception as e:
            logger.error(f"飞书消息发送失败: {e}")
            return False

    async def send_summaries(self, summaries: List[NewsSummary], title: str = "AI新闻日报") -> bool:
        """发送新闻摘要列表到飞书

        Args:
            summaries: 新闻摘要列表
            title: 消息标题

        Returns:
            是否发送成功
        """
        try:
            # 构建消息内容
            content_lines = [f"📰 **{title}**\n"]

            if self.mention_all:
                content_lines.append("<at id=all></at>\n")

            content_lines.append(f"共 {len(summaries)} 条新闻\n")
            content_lines.append("-" * 30 + "\n")

            for i, summary in enumerate(summaries, 1):
                # 标题
                content_lines.append(f"**【{i}】{summary.article.title}**\n")

                # 来源和链接
                source = summary.article.source or "未知来源"
                content_lines.append(f"📍 来源: {source}\n")
                content_lines.append(f"🔗 链接: {summary.original_link}\n")

                # 摘要内容（简化处理）
                summary_text = summary.summary
                # 飞书Markdown链接格式
                content_lines.append(f"\n{summary_text}\n")
                content_lines.append("-" * 30 + "\n")

            content = "".join(content_lines)

            # 飞书支持Markdown格式
            payload = {
                "msg_type": "text",
                "content": {
                    "text": content
                }
            }

            # 尝试使用markdown格式
            markdown_payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": title
                        },
                        "template": "blue"
                    },
                    "elements": []
                }
            }

            # 由于飞书卡片格式复杂，使用简单文本格式
            response = await self.client.post(
                self.webhook_url,
                json=payload
            )
            response.raise_for_status()

            logger.info(f"飞书新闻推送成功，共 {len(summaries)} 条")
            return True

        except Exception as e:
            logger.error(f"飞书新闻推送失败: {e}")
            return False

    async def send_card(self, summaries: List[NewsSummary], title: str = "AI新闻日报") -> bool:
        """使用飞书卡片格式发送消息

        Args:
            summaries: 新闻摘要列表
            title: 消息标题

        Returns:
            是否发送成功
        """
        try:
            # 构建卡片元素
            elements = []

            for i, summary in enumerate(summaries[:10], 1):  # 飞书卡片限制，最多10条
                # 截断过长的摘要
                summary_text = summary.summary
                if len(summary_text) > 300:
                    summary_text = summary_text[:300] + "..."

                element = {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"**【{i}】{summary.article.title}**\n"
                            f"来源: {summary.article.source or '未知'}\n"
                            f"链接: {summary.original_link}\n"
                            f"\n{summary_text}"
                        )
                    }
                }
                elements.append(element)

                if i < len(summaries) and i < 10:
                    elements.append({"tag": "hr"})

            # 如果有更多新闻，添加提示
            if len(summaries) > 10:
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"\n...还有 {len(summaries) - 10} 条新闻未显示"
                    }
                })

            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": f"{title} ({len(summaries)}条)"
                        },
                        "template": "blue"
                    },
                    "elements": elements
                }
            }

            response = await self.client.post(
                self.webhook_url,
                json=payload
            )
            response.raise_for_status()

            logger.info(f"飞书卡片推送成功，共 {len(summaries)} 条")
            return True

        except Exception as e:
            logger.error(f"飞书卡片推送失败: {e}")
            # 降级到普通文本格式
            return await self.send_summaries(summaries, title)

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
