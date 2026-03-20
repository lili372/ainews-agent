"""数据模型定义"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class NewsArticle(BaseModel):
    """新闻文章基础信息"""
    title: str = Field(description="新闻标题")
    url: str = Field(description="新闻链接")
    source: Optional[str] = Field(None, description="新闻来源")
    published_at: Optional[datetime] = Field(None, description="发布时间")
    snippet: Optional[str] = Field(None, description="新闻摘要/片段")


class NewsContent(BaseModel):
    """新闻完整内容"""
    article: NewsArticle
    content: str = Field(description="新闻正文内容")
    content_length: int = Field(description="内容长度（字符数）")
    language: Optional[str] = Field(None, description="语言检测结果")
    fetched_at: datetime = Field(default_factory=datetime.now)


class NewsSummary(BaseModel):
    """新闻摘要分析结果"""
    article: NewsArticle
    summary: str = Field(description="新闻摘要")
    key_points: List[str] = Field(default_factory=list, description="关键点列表")
    original_link: str = Field(description="原文链接")
    generated_at: datetime = Field(default_factory=datetime.now)


class DailyNewsReport(BaseModel):
    """每日新闻报告"""
    date: str = Field(description="报告日期")
    total_count: int = Field(description="新闻总数")
    summaries: List[NewsSummary] = Field(default_factory=list, description="新闻摘要列表")
    generated_at: datetime = Field(default_factory=datetime.now)
