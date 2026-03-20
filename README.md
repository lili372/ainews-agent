# ainews-agent
AI日报agent，功能是在网络上搜索最新的AI新闻，然后交给LLM来分析总结摘要，最后输出结果。

用户触发任务──> 
配置加载 ──>缓存检查 ──> 新闻搜索 ─>时效性过滤 ─>初筛过滤 ──>内容获取    ──>语言过滤  ──>截断处理   ──>敏感内容过滤  ──>批量LLM分析  ──>飞书推送
```
├── src/
│   ├── __init__.py
│   ├── main.py                   # 程序入口
│   ├── news_searcher/            # 新闻搜索模块
│   │   ├── __init__.py
│   │   ├── base.py              # 搜索基类
│   │   └── serpapi_searcher.py  # SerpAPI实现
│   ├── news_fetcher/            # 新闻内容获取
│   │   └── fetcher.py
│   ├── analyzer/                # LLM分析模块
│   │   └── llm_analyzer.py
│   ├── output/                  # 输出模块
│   │   ├── base.py
│   │   ├── markdown_output.py
│   │   ├── html_output.py
│   │   └── console_output.py
│   ├── reliability/             # 可靠性保障模块
│   │   ├── __init__.py
│   │   ├── freshness_filter.py  # 时效性过滤
│   │   ├── quality_filter.py    # 内容质量过滤
│   │   ├── circuit_breaker.py   # API降级与熔断
│   │   ├── truncator.py         # 文章截断处理
│   │   ├── multi_language.py    # 多语言处理
│   │   ├── content_moderation.py # 敏感内容过滤
│   │   └── feishu_sender.py     # 飞书推送
│   ├── models/                  # 数据模型
│   │   └── schemas.py
│   └── utils/                   # 工具类
│       ├── cache.py
│       ├── logger.py
│       └── config_loader.py
