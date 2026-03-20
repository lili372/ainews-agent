"""熔断器模块 - API调用保护"""
import time
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps
from src.utils.logger import get_logger

logger = get_logger()


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""
    pass


class CircuitBreaker:
    """熔断器实现 - 防止API过载"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """初始化熔断器

        Args:
            failure_threshold: 连续失败次数阈值，达到后触发熔断
            recovery_timeout: 恢复超时时间（秒），之后尝试半开
            expected_exception: 期望捕获的异常类型
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """通过熔断器执行函数

        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数

        Returns:
            函数返回值

        Raises:
            Exception: 当熔断器打开时抛出异常
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("熔断器进入半开状态")
            else:
                logger.warning("熔断器打开中，拒绝调用")
                raise CircuitBreakerOpenError("熔断器打开，API调用被拒绝")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """成功回调"""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("熔断器关闭，恢复正常")
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """失败回调"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"熔断器打开 (连续失败 {self.failure_count} 次)")

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试恢复"""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.recovery_timeout


def circuit_breaker_decorator(
    failure_threshold: int = 5,
    recovery_timeout: int = 60
):
    """熔断器装饰器

    Args:
        failure_threshold: 连续失败次数阈值
        recovery_timeout: 恢复超时时间（秒）
    """
    breaker = CircuitBreaker(failure_threshold, recovery_timeout)

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator