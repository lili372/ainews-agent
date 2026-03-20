"""配置加载模块"""
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class ConfigLoader:
    """配置加载器"""

    _instance: Optional['ConfigLoader'] = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._config:
            self.load()

    def load(self, config_path: Optional[str] = None) -> None:
        """加载配置文件

        Args:
            config_path: 配置文件路径，默认使用config/config.yaml
        """
        # 确定项目根目录
        project_root = Path(__file__).parent.parent.parent

        # 加载环境变量（指定.env文件路径）
        env_path = project_root / ".env"
        load_dotenv(env_path)

        if config_path is None:
            config_path = project_root / "config" / "config.yaml"

        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项

        Args:
            key: 配置键，支持点号分隔的路径，如 "news_search.max_results"
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()


# 全局配置实例
config = ConfigLoader()
