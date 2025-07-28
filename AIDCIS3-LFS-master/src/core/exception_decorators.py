"""
异常装饰器集合
提供各种异常处理和恢复装饰器

作者: AI-4 测试与质量保证工程师
创建时间: 2025-07-17
"""

import time
import functools
import traceback
import threading
from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass
from enum import Enum

from .error_handler import ErrorHandler, ErrorCategory, ErrorCode, ErrorSeverity, get_error_handler
from .logger import Logger, LogLevel, get_logger


class RetryStrategy(Enum):
    """重试策略"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    JITTER = "jitter"


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    exceptions: tuple = (Exception,)
    on_retry: Optional[Callable] = None
    on_failure: Optional[Callable] = None


class ExceptionCounter:
    """异常计数器"""
    
    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._lock = threading.Lock()
    
    def increment(self, key: str) -> int:
        """递增计数器"""
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + 1
            return self._counters[key]
    
    def get_count(self, key: str) -> int:
        """获取计数"""
        with self._lock:
            return self._counters.get(key, 0)
    
    def reset(self, key: str):
        """重置计数器"""
        with self._lock:
            self._counters[key] = 0
    
    def clear(self):
        """清除所有计数器"""
        with self._lock:
            self._counters.clear()


# 全局异常计数器
_exception_counter = ExceptionCounter()


def retry(config: Optional[RetryConfig] = None, 
          max_attempts: int = 3,
          base_delay: float = 1.0,
          strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
          exceptions: tuple = (Exception,),
          component: str = "Unknown"):
    """重试装饰器"""
    retry_config = config or RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        strategy=strategy,
        exceptions=exceptions
    )
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            logger = get_logger()
            
            last_exception = None
            
            for attempt in range(retry_config.max_attempts):
                try:
                    return func(*args, **kwargs)
                
                except retry_config.exceptions as e:
                    last_exception = e
                    
                    # 记录重试日志
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{retry_config.max_attempts} for {func.__name__}: {str(e)}",
                        component=component,
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_attempts=retry_config.max_attempts
                    )
                    
                    # 记录错误
                    error_handler.handle_error(
                        error=e,
                        component=component,
                        category=ErrorCategory.APPLICATION,
                        severity=ErrorSeverity.MEDIUM
                    )
                    
                    # 如果是最后一次尝试，不需要延迟
                    if attempt == retry_config.max_attempts - 1:
                        break
                    
                    # 计算延迟时间
                    delay = _calculate_delay(retry_config, attempt)
                    
                    # 调用重试回调
                    if retry_config.on_retry:
                        retry_config.on_retry(e, attempt + 1, delay)
                    
                    # 等待
                    time.sleep(delay)
            
            # 所有重试都失败了
            if retry_config.on_failure:
                retry_config.on_failure(last_exception, retry_config.max_attempts)
            
            # 记录最终失败
            logger.error(
                f"All retry attempts failed for {func.__name__}: {str(last_exception)}",
                component=component,
                function=func.__name__,
                max_attempts=retry_config.max_attempts
            )
            
            # 重新抛出异常
            raise last_exception
        
        return wrapper
    return decorator


def _calculate_delay(config: RetryConfig, attempt: int) -> float:
    """计算延迟时间"""
    if config.strategy == RetryStrategy.FIXED_DELAY:
        return config.base_delay
    
    elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
        delay = config.base_delay * (2 ** attempt)
        return min(delay, config.max_delay)
    
    elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
        delay = config.base_delay * (attempt + 1)
        return min(delay, config.max_delay)
    
    elif config.strategy == RetryStrategy.JITTER:
        import random
        delay = config.base_delay * (2 ** attempt)
        jitter = random.uniform(0, delay * 0.1)
        return min(delay + jitter, config.max_delay)
    
    return config.base_delay


def circuit_breaker(failure_threshold: int = 5,
                   recovery_timeout: int = 60,
                   expected_exception: Type[Exception] = Exception,
                   component: str = "Unknown"):
    """熔断器装饰器"""
    
    class CircuitState(Enum):
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"
    
    state = CircuitState.CLOSED
    failure_count = 0
    last_failure_time = 0
    lock = threading.Lock()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal state, failure_count, last_failure_time
            
            error_handler = get_error_handler()
            logger = get_logger()
            
            with lock:
                current_time = time.time()
                
                # 检查是否可以从开路状态恢复
                if state == CircuitState.OPEN:
                    if current_time - last_failure_time > recovery_timeout:
                        state = CircuitState.HALF_OPEN
                        logger.info(f"Circuit breaker half-open for {func.__name__}", component=component)
                    else:
                        # 熔断器开路，直接抛出异常
                        error_msg = f"Circuit breaker open for {func.__name__}"
                        logger.warning(error_msg, component=component)
                        raise RuntimeError(error_msg)
                
                try:
                    result = func(*args, **kwargs)
                    
                    # 成功执行，重置计数器
                    if state == CircuitState.HALF_OPEN:
                        state = CircuitState.CLOSED
                        failure_count = 0
                        logger.info(f"Circuit breaker closed for {func.__name__}", component=component)
                    
                    return result
                
                except expected_exception as e:
                    failure_count += 1
                    last_failure_time = current_time
                    
                    # 记录错误
                    error_handler.handle_error(
                        error=e,
                        component=component,
                        category=ErrorCategory.APPLICATION,
                        severity=ErrorSeverity.MEDIUM
                    )
                    
                    # 检查是否达到失败阈值
                    if failure_count >= failure_threshold:
                        state = CircuitState.OPEN
                        logger.error(
                            f"Circuit breaker opened for {func.__name__} after {failure_count} failures",
                            component=component
                        )
                    
                    raise
        
        return wrapper
    return decorator


def timeout(seconds: float, component: str = "Unknown"):
    """超时装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            error_handler = get_error_handler()
            logger = get_logger()
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            
            # 设置信号处理器
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # 取消超时
                return result
            
            except TimeoutError as e:
                # 记录超时错误
                error_handler.handle_error(
                    error=e,
                    component=component,
                    category=ErrorCategory.PERFORMANCE,
                    severity=ErrorSeverity.MEDIUM,
                    code=ErrorCode.NETWORK_TIMEOUT
                )
                
                logger.error(
                    f"Timeout in {func.__name__} after {seconds} seconds",
                    component=component,
                    function=func.__name__,
                    timeout=seconds
                )
                
                raise
            
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator


def rate_limit(max_calls: int, time_window: int = 60, component: str = "Unknown"):
    """速率限制装饰器"""
    calls = []
    lock = threading.Lock()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            logger = get_logger()
            
            with lock:
                current_time = time.time()
                
                # 清理过期的调用记录
                calls[:] = [call_time for call_time in calls if current_time - call_time < time_window]
                
                # 检查是否超过限制
                if len(calls) >= max_calls:
                    error_msg = f"Rate limit exceeded for {func.__name__}: {max_calls} calls per {time_window} seconds"
                    
                    # 记录错误
                    error_handler.handle_error(
                        error=error_msg,
                        component=component,
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.MEDIUM
                    )
                    
                    logger.warning(error_msg, component=component)
                    raise RuntimeError(error_msg)
                
                # 记录此次调用
                calls.append(current_time)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def exception_counter(threshold: int = 10, time_window: int = 3600, component: str = "Unknown"):
    """异常计数装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            logger = get_logger()
            
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                # 增加异常计数
                counter_key = f"{component}:{func.__name__}"
                count = _exception_counter.increment(counter_key)
                
                # 记录错误
                error_handler.handle_error(
                    error=e,
                    component=component,
                    category=ErrorCategory.APPLICATION,
                    severity=ErrorSeverity.MEDIUM
                )
                
                # 检查是否达到阈值
                if count >= threshold:
                    logger.critical(
                        f"Exception threshold reached for {func.__name__}: {count} exceptions",
                        component=component,
                        function=func.__name__,
                        exception_count=count,
                        threshold=threshold
                    )
                
                raise
        
        return wrapper
    return decorator


def fallback(fallback_func: Callable, exceptions: tuple = (Exception,), component: str = "Unknown"):
    """降级装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            logger = get_logger()
            
            try:
                return func(*args, **kwargs)
            
            except exceptions as e:
                # 记录错误
                error_handler.handle_error(
                    error=e,
                    component=component,
                    category=ErrorCategory.APPLICATION,
                    severity=ErrorSeverity.MEDIUM
                )
                
                logger.warning(
                    f"Fallback triggered for {func.__name__}: {str(e)}",
                    component=component,
                    function=func.__name__,
                    fallback_function=fallback_func.__name__
                )
                
                # 调用降级函数
                try:
                    return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(
                        f"Fallback function {fallback_func.__name__} also failed: {str(fallback_error)}",
                        component=component
                    )
                    raise
        
        return wrapper
    return decorator


def cache_on_error(ttl: int = 300, component: str = "Unknown"):
    """错误缓存装饰器"""
    cache = {}
    cache_lock = threading.Lock()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            logger = get_logger()
            
            # 生成缓存键
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            try:
                result = func(*args, **kwargs)
                
                # 成功执行，更新缓存
                with cache_lock:
                    cache[cache_key] = {
                        'result': result,
                        'timestamp': time.time()
                    }
                
                return result
            
            except Exception as e:
                # 记录错误
                error_handler.handle_error(
                    error=e,
                    component=component,
                    category=ErrorCategory.APPLICATION,
                    severity=ErrorSeverity.MEDIUM
                )
                
                # 尝试从缓存获取
                with cache_lock:
                    if cache_key in cache:
                        cache_entry = cache[cache_key]
                        if time.time() - cache_entry['timestamp'] < ttl:
                            logger.warning(
                                f"Using cached result for {func.__name__} due to error: {str(e)}",
                                component=component,
                                function=func.__name__
                            )
                            return cache_entry['result']
                
                # 没有缓存，重新抛出异常
                raise
        
        return wrapper
    return decorator


def performance_monitor(threshold: float = 1.0, component: str = "Unknown"):
    """性能监控装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            logger = get_logger()
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # 记录性能指标
                logger.debug(
                    f"Function {func.__name__} executed in {execution_time:.4f}s",
                    component=component,
                    function=func.__name__,
                    execution_time=execution_time
                )
                
                # 检查性能阈值
                if execution_time > threshold:
                    error_handler.handle_error(
                        error=f"Performance threshold exceeded: {execution_time:.4f}s > {threshold}s",
                        component=component,
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.MEDIUM
                    )
                
                return result
            
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.error(
                    f"Function {func.__name__} failed after {execution_time:.4f}s: {str(e)}",
                    component=component,
                    function=func.__name__,
                    execution_time=execution_time
                )
                
                raise
        
        return wrapper
    return decorator


def safe_call(default_value: Any = None, 
              log_errors: bool = True,
              component: str = "Unknown"):
    """安全调用装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                if log_errors:
                    error_handler = get_error_handler()
                    logger = get_logger()
                    
                    error_handler.handle_error(
                        error=e,
                        component=component,
                        category=ErrorCategory.APPLICATION,
                        severity=ErrorSeverity.LOW
                    )
                    
                    logger.warning(
                        f"Safe call caught exception in {func.__name__}: {str(e)}",
                        component=component,
                        function=func.__name__
                    )
                
                return default_value
        
        return wrapper
    return decorator


def async_safe(component: str = "Unknown"):
    """异步安全装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            logger = get_logger()
            
            try:
                return await func(*args, **kwargs)
            
            except Exception as e:
                error_handler.handle_error(
                    error=e,
                    component=component,
                    category=ErrorCategory.APPLICATION,
                    severity=ErrorSeverity.MEDIUM
                )
                
                logger.error(
                    f"Async function {func.__name__} failed: {str(e)}",
                    component=component,
                    function=func.__name__
                )
                
                raise
        
        return wrapper
    return decorator


# 组合装饰器
def robust(component: str = "Unknown",
          max_retries: int = 3,
          timeout_seconds: float = 30.0,
          fallback_func: Optional[Callable] = None):
    """健壮性装饰器（组合多个装饰器）"""
    def decorator(func: Callable) -> Callable:
        # 应用多个装饰器
        wrapped_func = func
        
        # 1. 性能监控
        wrapped_func = performance_monitor(component=component)(wrapped_func)
        
        # 2. 超时控制
        wrapped_func = timeout(timeout_seconds, component=component)(wrapped_func)
        
        # 3. 重试机制
        wrapped_func = retry(max_attempts=max_retries, component=component)(wrapped_func)
        
        # 4. 降级处理
        if fallback_func:
            wrapped_func = fallback(fallback_func, component=component)(wrapped_func)
        
        # 5. 异常计数
        wrapped_func = exception_counter(component=component)(wrapped_func)
        
        return wrapped_func
    
    return decorator


# 工具函数
def get_exception_statistics() -> Dict[str, int]:
    """获取异常统计信息"""
    return dict(_exception_counter._counters)


def reset_exception_counters():
    """重置异常计数器"""
    _exception_counter.clear()


def get_exception_count(component: str, function: str) -> int:
    """获取特定函数的异常计数"""
    counter_key = f"{component}:{function}"
    return _exception_counter.get_count(counter_key)


def reset_exception_counter(component: str, function: str):
    """重置特定函数的异常计数器"""
    counter_key = f"{component}:{function}"
    _exception_counter.reset(counter_key)