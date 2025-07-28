"""
高级日志记录系统
提供结构化日志记录、日志轮转、压缩、过滤和分析功能

作者: AI-4 测试与质量保证工程师
创建时间: 2025-07-17
"""

import os
import sys
import json
import gzip
import logging
import logging.handlers
import time
import threading
import queue
from typing import Dict, Any, Optional, List, Union, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
import traceback

from PySide6.QtCore import QObject, Signal, QTimer

from .dependency_injection import injectable, ServiceLifetime


class LogLevel(Enum):
    """日志级别"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogFormat(Enum):
    """日志格式"""
    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"
    STRUCTURED = "structured"


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: float
    level: LogLevel
    message: str
    component: str
    thread_id: int
    process_id: int
    filename: str
    line_number: int
    function_name: str
    extra_data: Dict[str, Any]
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class LoggerConfig:
    """日志记录器配置"""
    name: str = "AIDCIS3"
    level: LogLevel = LogLevel.INFO
    format_type: LogFormat = LogFormat.DETAILED
    log_dir: str = "logs"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    backup_count: int = 10
    compress_backups: bool = True
    enable_console: bool = True
    enable_file: bool = True
    enable_json_file: bool = True
    enable_structured_logging: bool = True
    buffer_size: int = 1000
    flush_interval: float = 5.0
    async_logging: bool = True
    log_filters: List[str] = None
    sensitive_fields: List[str] = None


class LogFilter:
    """日志过滤器"""
    
    def __init__(self, 
                 level: Optional[LogLevel] = None,
                 components: Optional[List[str]] = None,
                 exclude_components: Optional[List[str]] = None,
                 message_patterns: Optional[List[str]] = None,
                 exclude_patterns: Optional[List[str]] = None):
        self.level = level
        self.components = components or []
        self.exclude_components = exclude_components or []
        self.message_patterns = message_patterns or []
        self.exclude_patterns = exclude_patterns or []
    
    def should_log(self, entry: LogEntry) -> bool:
        """判断是否应该记录日志"""
        # 级别过滤
        if self.level and entry.level.value < self.level.value:
            return False
        
        # 组件过滤
        if self.components and entry.component not in self.components:
            return False
        
        if self.exclude_components and entry.component in self.exclude_components:
            return False
        
        # 消息模式过滤
        if self.message_patterns:
            import re
            if not any(re.search(pattern, entry.message) for pattern in self.message_patterns):
                return False
        
        if self.exclude_patterns:
            import re
            if any(re.search(pattern, entry.message) for pattern in self.exclude_patterns):
                return False
        
        return True


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def __init__(self, format_type: LogFormat = LogFormat.DETAILED, sensitive_fields: List[str] = None):
        super().__init__()
        self.format_type = format_type
        self.sensitive_fields = sensitive_fields or []
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 获取额外数据
        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'message', 'exc_info', 'exc_text', 
                          'stack_info', 'asctime']:
                extra_data[key] = value
        
        # 过滤敏感字段
        extra_data = self._filter_sensitive_data(extra_data)
        
        # 创建日志条目
        log_entry = LogEntry(
            timestamp=record.created,
            level=LogLevel(record.levelno),
            message=record.getMessage(),
            component=record.name,
            thread_id=record.thread,
            process_id=record.process,
            filename=record.filename,
            line_number=record.lineno,
            function_name=record.funcName,
            extra_data=extra_data,
            trace_id=getattr(record, 'trace_id', None),
            span_id=getattr(record, 'span_id', None),
            user_id=getattr(record, 'user_id', None),
            session_id=getattr(record, 'session_id', None)
        )
        
        # 格式化输出
        if self.format_type == LogFormat.JSON:
            return self._format_json(log_entry)
        elif self.format_type == LogFormat.STRUCTURED:
            return self._format_structured(log_entry)
        elif self.format_type == LogFormat.DETAILED:
            return self._format_detailed(log_entry)
        else:
            return self._format_simple(log_entry)
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤敏感数据"""
        filtered = {}
        for key, value in data.items():
            if key.lower() in [field.lower() for field in self.sensitive_fields]:
                filtered[key] = "***REDACTED***"
            else:
                filtered[key] = value
        return filtered
    
    def _format_json(self, entry: LogEntry) -> str:
        """JSON格式"""
        data = asdict(entry)
        data['timestamp'] = datetime.fromtimestamp(entry.timestamp).isoformat()
        data['level'] = entry.level.name
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    
    def _format_structured(self, entry: LogEntry) -> str:
        """结构化格式"""
        timestamp = datetime.fromtimestamp(entry.timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        parts = [
            f"[{timestamp}]",
            f"[{entry.level.name}]",
            f"[{entry.component}]",
            f"[{entry.filename}:{entry.line_number}]",
            f"[{entry.function_name}]",
            f"[T:{entry.thread_id}]",
            f"[P:{entry.process_id}]",
            entry.message
        ]
        
        if entry.extra_data:
            parts.append(f"extra={json.dumps(entry.extra_data)}")
        
        if entry.trace_id:
            parts.append(f"trace_id={entry.trace_id}")
        
        if entry.span_id:
            parts.append(f"span_id={entry.span_id}")
        
        return " ".join(parts)
    
    def _format_detailed(self, entry: LogEntry) -> str:
        """详细格式"""
        timestamp = datetime.fromtimestamp(entry.timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        return (
            f"{timestamp} | {entry.level.name:8} | {entry.component:20} | "
            f"{entry.filename}:{entry.line_number:4} | {entry.function_name:15} | "
            f"T:{entry.thread_id:5} | {entry.message}"
        )
    
    def _format_simple(self, entry: LogEntry) -> str:
        """简单格式"""
        timestamp = datetime.fromtimestamp(entry.timestamp).strftime('%H:%M:%S')
        return f"{timestamp} [{entry.level.name}] {entry.component}: {entry.message}"


class AsyncLogHandler(logging.Handler):
    """异步日志处理器"""
    
    def __init__(self, target_handler: logging.Handler, buffer_size: int = 1000):
        super().__init__()
        self.target_handler = target_handler
        self.buffer_size = buffer_size
        self.log_queue = queue.Queue(maxsize=buffer_size)
        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
    
    def emit(self, record: logging.LogRecord):
        """发送日志记录"""
        try:
            self.log_queue.put(record, block=False)
        except queue.Full:
            # 队列满了，丢弃最旧的记录
            try:
                self.log_queue.get(block=False)
                self.log_queue.put(record, block=False)
            except queue.Empty:
                pass
    
    def _worker(self):
        """工作线程"""
        while not self.stop_event.is_set():
            try:
                record = self.log_queue.get(timeout=1)
                self.target_handler.emit(record)
                self.log_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in async log handler: {e}")
    
    def close(self):
        """关闭处理器"""
        self.stop_event.set()
        self.worker_thread.join(timeout=5)
        self.target_handler.close()
        super().close()


class CompressedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """压缩轮转文件处理器"""
    
    def __init__(self, *args, compress_backups: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.compress_backups = compress_backups
    
    def doRollover(self):
        """执行轮转"""
        super().doRollover()
        
        if self.compress_backups and self.backupCount > 0:
            # 压缩最新的备份文件
            backup_name = f"{self.baseFilename}.1"
            if os.path.exists(backup_name):
                compressed_name = f"{backup_name}.gz"
                
                with open(backup_name, 'rb') as f_in:
                    with gzip.open(compressed_name, 'wb') as f_out:
                        f_out.writelines(f_in)
                
                os.remove(backup_name)
                
                # 重命名其他备份文件
                for i in range(2, self.backupCount + 1):
                    old_name = f"{backup_name}.{i-1}.gz"
                    new_name = f"{backup_name}.{i}.gz"
                    
                    if os.path.exists(old_name):
                        if os.path.exists(new_name):
                            os.remove(new_name)
                        os.rename(old_name, new_name)


@injectable(ServiceLifetime.SINGLETON)
class Logger(QObject):
    """高级日志记录器"""
    
    # 日志信号
    log_entry_created = Signal(object)  # LogEntry
    log_threshold_reached = Signal(str, int)  # level, count
    log_performance_warning = Signal(float)  # processing_time
    
    def __init__(self, config: Optional[LoggerConfig] = None):
        super().__init__()
        
        self.config = config or LoggerConfig()
        self._setup_logging()
        
        # 统计信息
        self._log_stats = {level.name: 0 for level in LogLevel}
        self._performance_stats = []
        self._last_flush_time = time.time()
        
        # 过滤器
        self._filters: List[LogFilter] = []
        
        # 上下文信息
        self._context_stack: List[Dict[str, Any]] = []
        self._thread_local = threading.local()
        
        # 性能监控
        self._performance_monitor = QTimer()
        self._performance_monitor.timeout.connect(self._check_performance)
        self._performance_monitor.start(60000)  # 1分钟检查一次
        
        # 日志缓冲
        self._log_buffer: List[LogEntry] = []
        self._buffer_lock = threading.Lock()
        
        # 刷新定时器
        if self.config.flush_interval > 0:
            self._flush_timer = QTimer()
            self._flush_timer.timeout.connect(self._flush_buffer)
            self._flush_timer.start(int(self.config.flush_interval * 1000))
        
        self.info("Logger initialized", component="Logger")
    
    def _setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建主日志记录器
        self._logger = logging.getLogger(self.config.name)
        self._logger.setLevel(self.config.level.value)
        
        # 清除现有处理器
        self._logger.handlers.clear()
        
        # 创建格式化器
        self._formatter = StructuredFormatter(
            self.config.format_type,
            self.config.sensitive_fields
        )
        
        # 控制台处理器
        if self.config.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.config.level.value)
            console_handler.setFormatter(self._formatter)
            
            if self.config.async_logging:
                console_handler = AsyncLogHandler(console_handler, self.config.buffer_size)
            
            self._logger.addHandler(console_handler)
        
        # 文件处理器
        if self.config.enable_file:
            file_path = log_dir / f"{self.config.name}.log"
            file_handler = CompressedRotatingFileHandler(
                file_path,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count,
                compress_backups=self.config.compress_backups,
                encoding='utf-8'
            )
            file_handler.setLevel(self.config.level.value)
            file_handler.setFormatter(self._formatter)
            
            if self.config.async_logging:
                file_handler = AsyncLogHandler(file_handler, self.config.buffer_size)
            
            self._logger.addHandler(file_handler)
        
        # JSON文件处理器
        if self.config.enable_json_file:
            json_formatter = StructuredFormatter(LogFormat.JSON, self.config.sensitive_fields)
            json_path = log_dir / f"{self.config.name}.json"
            json_handler = CompressedRotatingFileHandler(
                json_path,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count,
                compress_backups=self.config.compress_backups,
                encoding='utf-8'
            )
            json_handler.setLevel(self.config.level.value)
            json_handler.setFormatter(json_formatter)
            
            if self.config.async_logging:
                json_handler = AsyncLogHandler(json_handler, self.config.buffer_size)
            
            self._logger.addHandler(json_handler)
    
    def _create_log_entry(self, level: LogLevel, message: str, component: str, **kwargs) -> LogEntry:
        """创建日志条目"""
        # 获取调用栈信息
        frame = sys._getframe(3)  # 跳过内部调用
        
        # 获取上下文信息
        context = self._get_current_context()
        
        extra_data = dict(kwargs)
        extra_data.update(context)
        
        return LogEntry(
            timestamp=time.time(),
            level=level,
            message=message,
            component=component,
            thread_id=threading.current_thread().ident,
            process_id=os.getpid(),
            filename=os.path.basename(frame.f_code.co_filename),
            line_number=frame.f_lineno,
            function_name=frame.f_code.co_name,
            extra_data=extra_data,
            trace_id=getattr(self._thread_local, 'trace_id', None),
            span_id=getattr(self._thread_local, 'span_id', None),
            user_id=getattr(self._thread_local, 'user_id', None),
            session_id=getattr(self._thread_local, 'session_id', None)
        )
    
    def _get_current_context(self) -> Dict[str, Any]:
        """获取当前上下文"""
        context = {}
        for ctx in self._context_stack:
            context.update(ctx)
        return context
    
    def _should_log(self, entry: LogEntry) -> bool:
        """判断是否应该记录日志"""
        for filter_obj in self._filters:
            if not filter_obj.should_log(entry):
                return False
        return True
    
    def _log(self, level: LogLevel, message: str, component: str, **kwargs):
        """记录日志"""
        start_time = time.time()
        
        try:
            # 创建日志条目
            entry = self._create_log_entry(level, message, component, **kwargs)
            
            # 应用过滤器
            if not self._should_log(entry):
                return
            
            # 更新统计
            self._log_stats[level.name] += 1
            
            # 发射信号
            self.log_entry_created.emit(entry)
            
            # 缓冲或直接记录
            if self.config.buffer_size > 0:
                with self._buffer_lock:
                    self._log_buffer.append(entry)
                    if len(self._log_buffer) >= self.config.buffer_size:
                        self._flush_buffer()
            else:
                self._write_log_entry(entry)
            
            # 性能监控
            processing_time = time.time() - start_time
            self._performance_stats.append(processing_time)
            
            # 保持性能统计大小
            if len(self._performance_stats) > 1000:
                self._performance_stats = self._performance_stats[-1000:]
            
            # 性能警告
            if processing_time > 0.1:  # 100ms
                self.log_performance_warning.emit(processing_time)
            
        except Exception as e:
            # 日志记录失败，直接打印
            print(f"Logging error: {e}")
    
    def _write_log_entry(self, entry: LogEntry):
        """写入日志条目"""
        # 创建logging.LogRecord
        record = logging.LogRecord(
            name=entry.component,
            level=entry.level.value,
            pathname=entry.filename,
            lineno=entry.line_number,
            msg=entry.message,
            args=(),
            exc_info=None,
            func=entry.function_name
        )
        
        # 添加额外信息
        for key, value in entry.extra_data.items():
            setattr(record, key, value)
        
        if entry.trace_id:
            record.trace_id = entry.trace_id
        if entry.span_id:
            record.span_id = entry.span_id
        if entry.user_id:
            record.user_id = entry.user_id
        if entry.session_id:
            record.session_id = entry.session_id
        
        # 写入日志
        self._logger.handle(record)
    
    def _flush_buffer(self):
        """刷新缓冲区"""
        with self._buffer_lock:
            if self._log_buffer:
                for entry in self._log_buffer:
                    self._write_log_entry(entry)
                self._log_buffer.clear()
                self._last_flush_time = time.time()
    
    def _check_performance(self):
        """检查性能"""
        if self._performance_stats:
            avg_time = sum(self._performance_stats) / len(self._performance_stats)
            max_time = max(self._performance_stats)
            
            if avg_time > 0.01:  # 平均超过10ms
                self.warning(
                    f"Logging performance degraded: avg={avg_time:.4f}s, max={max_time:.4f}s",
                    component="Logger"
                )
    
    # 公共日志方法
    def trace(self, message: str, component: str = "Unknown", **kwargs):
        """记录跟踪日志"""
        self._log(LogLevel.TRACE, message, component, **kwargs)
    
    def debug(self, message: str, component: str = "Unknown", **kwargs):
        """记录调试日志"""
        self._log(LogLevel.DEBUG, message, component, **kwargs)
    
    def info(self, message: str, component: str = "Unknown", **kwargs):
        """记录信息日志"""
        self._log(LogLevel.INFO, message, component, **kwargs)
    
    def warning(self, message: str, component: str = "Unknown", **kwargs):
        """记录警告日志"""
        self._log(LogLevel.WARNING, message, component, **kwargs)
    
    def error(self, message: str, component: str = "Unknown", **kwargs):
        """记录错误日志"""
        self._log(LogLevel.ERROR, message, component, **kwargs)
    
    def critical(self, message: str, component: str = "Unknown", **kwargs):
        """记录严重错误日志"""
        self._log(LogLevel.CRITICAL, message, component, **kwargs)
    
    def exception(self, message: str, component: str = "Unknown", **kwargs):
        """记录异常日志"""
        kwargs['traceback'] = traceback.format_exc()
        self._log(LogLevel.ERROR, message, component, **kwargs)
    
    # 上下文管理
    def push_context(self, context: Dict[str, Any]):
        """推入上下文"""
        self._context_stack.append(context)
    
    def pop_context(self):
        """弹出上下文"""
        if self._context_stack:
            self._context_stack.pop()
    
    def set_trace_id(self, trace_id: str):
        """设置追踪ID"""
        self._thread_local.trace_id = trace_id
    
    def set_span_id(self, span_id: str):
        """设置跨度ID"""
        self._thread_local.span_id = span_id
    
    def set_user_id(self, user_id: str):
        """设置用户ID"""
        self._thread_local.user_id = user_id
    
    def set_session_id(self, session_id: str):
        """设置会话ID"""
        self._thread_local.session_id = session_id
    
    # 过滤器管理
    def add_filter(self, filter_obj: LogFilter):
        """添加过滤器"""
        self._filters.append(filter_obj)
    
    def remove_filter(self, filter_obj: LogFilter):
        """移除过滤器"""
        if filter_obj in self._filters:
            self._filters.remove(filter_obj)
    
    def clear_filters(self):
        """清除所有过滤器"""
        self._filters.clear()
    
    # 统计信息
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "log_counts": dict(self._log_stats),
            "performance": {
                "avg_processing_time": sum(self._performance_stats) / len(self._performance_stats) if self._performance_stats else 0,
                "max_processing_time": max(self._performance_stats) if self._performance_stats else 0,
                "min_processing_time": min(self._performance_stats) if self._performance_stats else 0
            },
            "buffer_size": len(self._log_buffer),
            "last_flush_time": self._last_flush_time
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self._log_stats = {level.name: 0 for level in LogLevel}
        self._performance_stats.clear()
    
    # 刷新和关闭
    def flush(self):
        """刷新所有日志"""
        self._flush_buffer()
        for handler in self._logger.handlers:
            handler.flush()
    
    def close(self):
        """关闭日志记录器"""
        self.flush()
        
        for handler in self._logger.handlers:
            handler.close()
        
        if hasattr(self, '_flush_timer'):
            self._flush_timer.stop()
        
        if hasattr(self, '_performance_monitor'):
            self._performance_monitor.stop()


# 便捷函数
def get_logger() -> Logger:
    """获取日志记录器实例"""
    try:
        from .dependency_injection import get_container
        container = get_container()
        return container.resolve(Logger)
    except Exception:
        return Logger()


# 装饰器
def log_calls(component: str = None, level: LogLevel = LogLevel.DEBUG):
    """记录函数调用的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            func_component = component or func.__module__
            
            # 记录函数调用
            logger._log(
                level,
                f"Calling {func.__name__}",
                func_component,
                function=func.__name__,
                args_count=len(args),
                kwargs_count=len(kwargs)
            )
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # 记录成功完成
                logger._log(
                    level,
                    f"Completed {func.__name__} in {execution_time:.4f}s",
                    func_component,
                    function=func.__name__,
                    execution_time=execution_time,
                    success=True
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # 记录异常
                logger._log(
                    LogLevel.ERROR,
                    f"Exception in {func.__name__}: {str(e)}",
                    func_component,
                    function=func.__name__,
                    execution_time=execution_time,
                    error=str(e),
                    success=False,
                    traceback=traceback.format_exc()
                )
                
                raise
        
        return wrapper
    return decorator


# 上下文管理器
class LogContext:
    """日志上下文管理器"""
    
    def __init__(self, context: Dict[str, Any]):
        self.context = context
        self.logger = get_logger()
    
    def __enter__(self):
        self.logger.push_context(self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.pop_context()


# 快捷函数
def trace(message: str, component: str = "Unknown", **kwargs):
    """记录跟踪日志"""
    get_logger().trace(message, component, **kwargs)


def debug(message: str, component: str = "Unknown", **kwargs):
    """记录调试日志"""
    get_logger().debug(message, component, **kwargs)


def info(message: str, component: str = "Unknown", **kwargs):
    """记录信息日志"""
    get_logger().info(message, component, **kwargs)


def warning(message: str, component: str = "Unknown", **kwargs):
    """记录警告日志"""
    get_logger().warning(message, component, **kwargs)


def error(message: str, component: str = "Unknown", **kwargs):
    """记录错误日志"""
    get_logger().error(message, component, **kwargs)


def critical(message: str, component: str = "Unknown", **kwargs):
    """记录严重错误日志"""
    get_logger().critical(message, component, **kwargs)


def exception(message: str, component: str = "Unknown", **kwargs):
    """记录异常日志"""
    get_logger().exception(message, component, **kwargs)