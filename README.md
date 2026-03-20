# ainews-agent
AI日报agent，功能是在网络上搜索最新的AI新闻，然后交给LLM来分析总结摘要，最后输出结果。

用户触发任务
       │
       v
  配置加载 (ConfigLoader)
       │
       v
  缓存检查 (NewsCache) ──有缓存──> 直接使用
       │无缓存
       v
  新闻搜索 (NewsSearcher) ──> 获取新闻列表
       │
       v
  时效性过滤 (FreshnessFilter) ──> 过滤过期新闻
       │
       v
  初筛过滤 (QualityFilter) ──> 标题+摘要筛选、去重
       │
       v
  内容获取 (NewsFetcher) ──> 获取详细内容
       │
       v
  语言过滤 (MultiLanguage) ──> 检测并处理多语言
       │
       v
  截断处理 (Truncator) ──> 控制文章长度
       │
       v
  敏感内容过滤 (ContentModeration) ──> 安全检查
       │
       v
  批量LLM分析 (LLMAnalyzer) ──> 生成摘要总结
       │
       v
  飞书推送 (FeishuSender) ──> 发送到飞书群
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
