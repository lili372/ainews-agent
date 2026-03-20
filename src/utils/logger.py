"""日志工具模块"""
import loguru
import sys
from pathlib import Path


def setup_logger(log_dir: str = "logs", level: str = "INFO") -> None:
    """配置日志系统

    Args:
        log_dir: 日志目录
        level: 日志级别
    """
    # 移除默认处理器
    loguru.logger.remove()

    # 添加控制台处理器
    loguru.logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
    )

    # 确保日志目录存在
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)

    # 添加文件处理器
    loguru.logger.add(
        log_dir_path / "ai_news_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
    )


def get_logger():
    """获取logger实例"""
    return loguru.logger
