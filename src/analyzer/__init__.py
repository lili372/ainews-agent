# -*- coding: utf-8 -*-
"""
LLM分析模块

该模块负责使用大语言模型对新闻内容进行分析和摘要生成。
支持OpenAI GPT-4和Anthropic Claude等多种LLM提供商。
"""

from .llm_analyzer import LLMAnalyzer

__all__ = ["LLMAnalyzer"]