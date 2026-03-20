# -*- coding: utf-8 -*-
"""
HTML输出器

使用Jinja2模板将新闻摘要输出为HTML格式的文件。
"""

import os
from datetime import datetime
from typing import List
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

from .base import BaseOutput
from src.models.schemas import NewsSummary


class HTMLOutput(BaseOutput):
    """HTML格式输出器

    使用Jinja2模板引擎将新闻摘要输出为HTML格式的文件。
    输出文件保存在配置的输出目录中。

    Attributes:
        output_dir: 输出目录路径
        filename_template: 文件名模板
    """

    # 默认HTML模板
    DEFAULT_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI新闻日报 - {{ date }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eaeaea;
        }
        h1 {
            color: #1a1a1a;
            font-size: 2.2em;
            margin-bottom: 10px;
        }
        .date {
            color: #666;
            font-size: 1.1em;
        }
        .stats {
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .news-item {
            margin-bottom: 30px;
            padding: 25px;
            border: 1px solid #eaeaea;
            border-radius: 8px;
            background: white;
        }
        .news-item:hover {
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .news-title {
            font-size: 1.4em;
            color: #1a1a1a;
            margin-bottom: 10px;
        }
        .news-source {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
        }
        .news-summary {
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            border-radius: 0 5px 5px 0;
        }
        .key-points {
            margin: 15px 0;
        }
        .key-points h4 {
            color: #333;
            margin-bottom: 10px;
        }
        .key-points ul {
            list-style: none;
            padding-left: 0;
        }
        .key-points li {
            padding: 5px 0;
            padding-left: 20px;
            position: relative;
        }
        .key-points li::before {
            content: "•";
            color: #007bff;
            position: absolute;
            left: 0;
            font-weight: bold;
        }
        .source-link {
            margin-top: 15px;
        }
        .source-link a {
            color: #007bff;
            text-decoration: none;
        }
        .source-link a:hover {
            text-decoration: underline;
        }
        footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eaeaea;
            color: #999;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AI新闻日报</h1>
            <p class="date">{{ date }}</p>
        </header>

        <div class="stats">
            共 {{ summaries|length }} 条新闻
        </div>

        {% for summary in summaries %}
        <article class="news-item">
            <h2 class="news-title">{{ loop.index }}. {{ summary.title }}</h2>
            <p class="news-source">来源: {{ summary.source }}</p>

            <div class="news-summary">
                <strong>摘要:</strong> {{ summary.summary }}
            </div>

            {% if summary.key_points %}
            <div class="key-points">
                <h4>关键点:</h4>
                <ul>
                    {% for point in summary.key_points %}
                    <li>{{ point }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}

            <div class="source-link">
                <a href="{{ summary.source_link }}" target="_blank">阅读原文</a>
            </div>
        </article>
        {% endfor %}

        <footer>
            <p>由AI新闻日报系统生成 | {{ timestamp }}</p>
        </footer>
    </div>
</body>
</html>
"""

    def __init__(
        self,
        output_dir: str = "./output",
        filename_template: str = "ai_news_{date}.html",
        template_path: str = None
    ):
        """初始化HTML输出器

        Args:
            output_dir: 输出目录路径，默认为./output
            filename_template: 文件名模板，默认为ai_news_{date}.html
            template_path: 自定义模板路径，默认为None使用内置模板
        """
        self.output_dir = Path(output_dir)
        self.filename_template = filename_template
        self.template_path = template_path
        self._env = None

    def _get_template(self) -> Template:
        """获取Jinja2模板

        Returns:
            Jinja2 Template对象
        """
        if self.template_path:
            # 从文件加载模板
            template_dir = Path(self.template_path).parent
            template_name = Path(self.template_path).name
            env = Environment(loader=FileSystemLoader(template_dir))
            return env.get_template(template_name)
        else:
            # 使用默认模板
            return Template(self.DEFAULT_TEMPLATE)

    def output(self, summaries: List[NewsSummary]) -> None:
        """输出HTML格式的新闻摘要

        将摘要列表输出为HTML文件。

        Args:
            summaries: 新闻摘要列表

        Raises:
            ValueError: 当摘要列表为空时
        """
        if not self._validate_summaries(summaries):
            raise ValueError("摘要列表不能为空")

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = self.filename_template.format(date=date_str)
        filepath = self.output_dir / filename

        # 渲染模板
        template = self._get_template()
        content = template.render(
            summaries=summaries,
            date=datetime.now().strftime("%Y年%m月%d日"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"HTML输出完成: {filepath}")
