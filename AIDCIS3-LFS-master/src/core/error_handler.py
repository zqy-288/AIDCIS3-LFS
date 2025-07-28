"""
统一错误处理系统
提供全局错误处理、分类、报告和恢复机制

作者: AI-4 测试与质量保证工程师
创建时间: 2025-07-17
"""

import sys
import os
import traceback
import logging
import time
import json
import threading
from typing import Dict, Any, Optional, Callable, List, Union, Type
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from contextlib import contextmanager

from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtWidgets import QMessageBox, QApplication

from .dependency_injection import injectable, ServiceLifetime, get_container
from .error_recovery import ErrorRecoveryManager, ErrorRecord, ErrorSeverity, RecoveryStrategy


class ErrorCategory(Enum):
    """错误分类"""
    SYSTEM = "system"           # 系统级错误
    APPLICATION = "application" # 应用程序错误
    UI = "ui"                   # UI界面错误
    DATA = "data"               # 数据访问错误
    NETWORK = "network"         # 网络错误
    FILE = "file"               # 文件操作错误
    SECURITY = "security"       # 安全相关错误
    PERFORMANCE = "performance" # 性能相关错误
    VALIDATION = "validation"   # 数据验证错误
    BUSINESS = "business"       # 业务逻辑错误


class ErrorCode(Enum):
    """标准错误代码"""
    # 系统错误 (1000-1999)
    SYSTEM_STARTUP_FAILED = 1001
    SYSTEM_SHUTDOWN_FAILED = 1002
    SYSTEM_RESOURCE_EXHAUSTED = 1003
    SYSTEM_PERMISSION_DENIED = 1004
    
    # 应用程序错误 (2000-2999)
    APP_INITIALIZATION_FAILED = 2001
    APP_CONFIGURATION_ERROR = 2002
    APP_DEPENDENCY_MISSING = 2003
    APP_STATE_INVALID = 2004
    
    # UI错误 (3000-3999)
    UI_COMPONENT_CREATION_FAILED = 3001
    UI_COMPONENT_DESTROYED = 3002
    UI_LAYOUT_ERROR = 3003
    UI_MEMORY_LEAK = 3004
    
    # 数据错误 (4000-4999)
    DATA_CONNECTION_FAILED = 4001
    DATA_QUERY_FAILED = 4002
    DATA_VALIDATION_FAILED = 4003
    DATA_CORRUPTION = 4004
    
    # 网络错误 (5000-5999)
    NETWORK_CONNECTION_FAILED = 5001
    NETWORK_TIMEOUT = 5002
    NETWORK_PROTOCOL_ERROR = 5003
    
    # 文件错误 (6000-6999)
    FILE_NOT_FOUND = 6001
    FILE_ACCESS_DENIED = 6002
    FILE_CORRUPTED = 6003
    FILE_DISK_FULL = 6004


@dataclass
class ErrorContext:
    """错误上下文信息"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    component_state: Optional[Dict[str, Any]] = None
    user_actions: Optional[List[str]] = None
    system_info: Optional[Dict[str, Any]] = None
    thread_id: Optional[int] = None
    process_id: Optional[int] = None


@dataclass
class ErrorHandlerConfig:
    """错误处理器配置"""
    max_error_history: int = 10000
    error_report_threshold: int = 100
    auto_report_enabled: bool = True
    user_notification_enabled: bool = True
    log_file_path: str = "logs/errors.log"
    report_file_path: str = "reports/error_reports.json"
    performance_monitoring: bool = True
    memory_threshold_mb: float = 512.0
    cpu_threshold_percent: float = 85.0
    disk_threshold_percent: float = 90.0


@injectable(ServiceLifetime.SINGLETON)
class ErrorHandler(QObject):
    """统一错误处理器"""
    
    # 错误处理信号
    error_captured = Signal(object)  # ErrorRecord
    error_processed = Signal(object, bool)  # ErrorRecord, success
    error_reported = Signal(object)  # ErrorRecord
    threshold_exceeded = Signal(str, int)  # error_type, count
    
    def __init__(self, config: Optional[ErrorHandlerConfig] = None):
        super().__init__()
        
        self._config = config or ErrorHandlerConfig()
        self._logger = self._setup_logger()
        
        # 错误统计
        self._error_stats: Dict[str, int] = {}
        self._error_history: List[ErrorRecord] = []
        self._error_rates: Dict[str, List[float]] = {}
        
        # 错误处理器映射
        self._error_handlers: Dict[str, Callable[[ErrorRecord], bool]] = {}
        self._category_handlers: Dict[ErrorCategory, Callable[[ErrorRecord], bool]] = {}
        
        # 错误报告系统
        self._report_queue: List[ErrorRecord] = []
        self._report_thread: Optional[QThread] = None
        self._report_lock = threading.Lock()
        
        # 性能监控
        self._performance_monitor: Optional[QTimer] = None
        if self._config.performance_monitoring:
            self._setup_performance_monitoring()
        
        # 集成错误恢复管理器
        self._recovery_manager: Optional[ErrorRecoveryManager] = None
        self._setup_recovery_integration()
        
        # 注册标准错误处理器
        self._register_standard_handlers()
        
        self._logger.info("ErrorHandler initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("ErrorHandler")
        logger.setLevel(logging.DEBUG)
        
        # 创建日志目录
        log_dir = Path(self._config.log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler(self._config.log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _setup_performance_monitoring(self):
        """设置性能监控"""
        self._performance_monitor = QTimer()
        self._performance_monitor.timeout.connect(self._check_system_performance)
        self._performance_monitor.start(30000)  # 30秒检查一次
    
    def _setup_recovery_integration(self):
        """设置错误恢复集成"""
        try:
            container = get_container()
            self._recovery_manager = container.resolve(ErrorRecoveryManager)
            
            # 连接信号
            if self._recovery_manager:
                self._recovery_manager.error_occurred.connect(self._on_recovery_error)
                self._recovery_manager.recovery_completed.connect(self._on_recovery_completed)
                self._logger.info("ErrorRecoveryManager integration successful")
                
        except Exception as e:
            # 只记录一次警告，避免重复日志
            if not hasattr(self, '_recovery_warning_logged'):
                self._logger.warning(f"Failed to integrate with ErrorRecoveryManager: {e}")
                self._recovery_warning_logged = True
    
    def _register_standard_handlers(self):
        """注册标准错误处理器"""
        # 系统错误处理器
        self.register_category_handler(ErrorCategory.SYSTEM, self._handle_system_error)
        self.register_category_handler(ErrorCategory.APPLICATION, self._handle_application_error)
        self.register_category_handler(ErrorCategory.UI, self._handle_ui_error)
        self.register_category_handler(ErrorCategory.DATA, self._handle_data_error)
        self.register_category_handler(ErrorCategory.NETWORK, self._handle_network_error)
        self.register_category_handler(ErrorCategory.FILE, self._handle_file_error)
        self.register_category_handler(ErrorCategory.SECURITY, self._handle_security_error)
        self.register_category_handler(ErrorCategory.PERFORMANCE, self._handle_performance_error)
        self.register_category_handler(ErrorCategory.VALIDATION, self._handle_validation_error)
        self.register_category_handler(ErrorCategory.BUSINESS, self._handle_business_error)
    
    def handle_error(self, 
                    error: Union[Exception, ErrorRecord, str], 
                    component: str = "unknown",
                    category: ErrorCategory = ErrorCategory.APPLICATION,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: Optional[ErrorContext] = None,
                    code: Optional[ErrorCode] = None) -> bool:
        """处理错误"""
        try:
            # 转换为ErrorRecord
            if isinstance(error, ErrorRecord):
                error_record = error
            else:
                error_record = self._create_error_record(
                    error, component, category, severity, context, code
                )
            
            # 记录错误
            self._record_error(error_record)
            
            # 发射信号
            self.error_captured.emit(error_record)
            
            # 处理错误
            success = self._process_error(error_record)
            
            # 发射处理完成信号
            self.error_processed.emit(error_record, success)
            
            # 检查是否需要报告
            if self._should_report_error(error_record):
                self._queue_error_report(error_record)
            
            return success
            
        except Exception as e:
            # 错误处理器本身出错
            self._logger.critical(f"Error in error handler: {e}")
            return False
    
    def _create_error_record(self, 
                           error: Union[Exception, str],
                           component: str,
                           category: ErrorCategory,
                           severity: ErrorSeverity,
                           context: Optional[ErrorContext],
                           code: Optional[ErrorCode]) -> ErrorRecord:
        """创建错误记录"""
        if isinstance(error, Exception):
            error_type = type(error).__name__
            message = str(error)
            traceback_str = traceback.format_exc()
        else:
            error_type = "CustomError"
            message = str(error)
            traceback_str = ""
        
        # 构建上下文
        error_context = {}
        if context:
            error_context.update(asdict(context))
        
        error_context.update({
            "category": category.value,
            "error_code": code.value if code else None,
            "thread_id": threading.current_thread().ident,
            "process_id": os.getpid(),
            "timestamp_iso": datetime.now().isoformat()
        })
        
        return ErrorRecord(
            timestamp=time.time(),
            error_type=error_type,
            message=message,
            traceback=traceback_str,
            severity=severity,
            component=component,
            context=error_context
        )
    
    def _record_error(self, error_record: ErrorRecord):
        """记录错误"""
        # 添加到历史记录
        self._error_history.append(error_record)
        
        # 限制历史记录大小
        if len(self._error_history) > self._config.max_error_history:
            self._error_history = self._error_history[-self._config.max_error_history:]
        
        # 更新统计
        error_key = f"{error_record.component}:{error_record.error_type}"
        self._error_stats[error_key] = self._error_stats.get(error_key, 0) + 1
        
        # 记录错误率
        current_time = time.time()
        if error_key not in self._error_rates:
            self._error_rates[error_key] = []
        self._error_rates[error_key].append(current_time)
        
        # 清理旧记录（保留最近1小时）
        cutoff_time = current_time - 3600
        self._error_rates[error_key] = [
            t for t in self._error_rates[error_key] if t > cutoff_time
        ]
        
        # 检查阈值
        if len(self._error_rates[error_key]) >= self._config.error_report_threshold:
            self.threshold_exceeded.emit(error_key, len(self._error_rates[error_key]))
        
        # 记录日志
        self._log_error(error_record)
    
    def _log_error(self, error_record: ErrorRecord):
        """记录错误日志"""
        log_message = (
            f"[{error_record.component}] {error_record.error_type}: {error_record.message}"
        )
        
        if error_record.severity == ErrorSeverity.CRITICAL:
            self._logger.critical(log_message)
        elif error_record.severity == ErrorSeverity.HIGH:
            self._logger.error(log_message)
        elif error_record.severity == ErrorSeverity.MEDIUM:
            self._logger.warning(log_message)
        else:
            self._logger.info(log_message)
        
        # 记录详细信息
        if error_record.traceback:
            self._logger.debug(f"Traceback: {error_record.traceback}")
        
        if error_record.context:
            self._logger.debug(f"Context: {json.dumps(error_record.context, indent=2)}")
    
    def _process_error(self, error_record: ErrorRecord) -> bool:
        """处理错误"""
        try:
            # 首先尝试特定错误类型的处理器
            error_type = error_record.error_type
            if error_type in self._error_handlers:
                return self._error_handlers[error_type](error_record)
            
            # 然后尝试类别处理器
            category = ErrorCategory(error_record.context.get("category", ErrorCategory.APPLICATION.value))
            if category in self._category_handlers:
                return self._category_handlers[category](error_record)
            
            # 默认处理
            return self._handle_default_error(error_record)
            
        except Exception as e:
            self._logger.error(f"Error processing error: {e}")
            return False
    
    def _handle_system_error(self, error_record: ErrorRecord) -> bool:
        """处理系统错误"""
        self._logger.critical(f"System error: {error_record.message}")
        
        # 系统错误需要立即报告
        self._queue_error_report(error_record)
        
        # 尝试恢复
        if self._recovery_manager:
            return self._recovery_manager.handle_error(error_record)
        
        # 如果没有恢复管理器，至少记录错误但不阻止系统运行
        return True
    
    def _handle_application_error(self, error_record: ErrorRecord) -> bool:
        """处理应用程序错误"""
        self._logger.error(f"Application error: {error_record.message}")
        
        # 应用程序错误尝试恢复
        if self._recovery_manager:
            return self._recovery_manager.handle_error(error_record)
        
        return True
    
    def _handle_ui_error(self, error_record: ErrorRecord) -> bool:
        """处理UI错误"""
        self._logger.warning(f"UI error: {error_record.message}")
        
        # UI错误通常不是致命的
        if self._config.user_notification_enabled:
            self._show_user_notification(error_record)
        
        return True
    
    def _handle_data_error(self, error_record: ErrorRecord) -> bool:
        """处理数据错误"""
        self._logger.error(f"Data error: {error_record.message}")
        
        # 数据错误可能需要回滚
        if self._recovery_manager:
            return self._recovery_manager.handle_error(error_record)
        
        return False
    
    def _handle_network_error(self, error_record: ErrorRecord) -> bool:
        """处理网络错误"""
        self._logger.warning(f"Network error: {error_record.message}")
        
        # 网络错误通常可以重试
        if self._recovery_manager:
            return self._recovery_manager.handle_error(error_record)
        
        return True
    
    def _handle_file_error(self, error_record: ErrorRecord) -> bool:
        """处理文件错误"""
        self._logger.error(f"File error: {error_record.message}")
        
        # 文件错误可能需要用户干预
        if self._config.user_notification_enabled:
            self._show_user_notification(error_record)
        
        return True
    
    def _handle_security_error(self, error_record: ErrorRecord) -> bool:
        """处理安全错误"""
        self._logger.critical(f"Security error: {error_record.message}")
        
        # 安全错误需要立即报告
        self._queue_error_report(error_record)
        
        return False
    
    def _handle_performance_error(self, error_record: ErrorRecord) -> bool:
        """处理性能错误"""
        self._logger.warning(f"Performance error: {error_record.message}")
        
        # 性能错误记录但不阻止执行
        return True
    
    def _handle_validation_error(self, error_record: ErrorRecord) -> bool:
        """处理验证错误"""
        self._logger.info(f"Validation error: {error_record.message}")
        
        # 验证错误通常需要用户修正
        if self._config.user_notification_enabled:
            self._show_user_notification(error_record)
        
        return True
    
    def _handle_business_error(self, error_record: ErrorRecord) -> bool:
        """处理业务错误"""
        self._logger.warning(f"Business error: {error_record.message}")
        
        # 业务错误通常需要用户处理
        if self._config.user_notification_enabled:
            self._show_user_notification(error_record)
        
        return True
    
    def _handle_default_error(self, error_record: ErrorRecord) -> bool:
        """默认错误处理"""
        self._logger.error(f"Unhandled error: {error_record.message}")
        
        # 默认尝试恢复
        if self._recovery_manager:
            return self._recovery_manager.handle_error(error_record)
        
        return True
    
    def _show_user_notification(self, error_record: ErrorRecord):
        """显示用户通知"""
        try:
            if QApplication.instance():
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("错误提示")
                msg.setText(f"发生错误: {error_record.message}")
                msg.setDetailedText(f"组件: {error_record.component}\n类型: {error_record.error_type}")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
        except Exception as e:
            self._logger.error(f"Failed to show user notification: {e}")
    
    def _should_report_error(self, error_record: ErrorRecord) -> bool:
        """判断是否应该报告错误"""
        if not self._config.auto_report_enabled:
            return False
        
        # 严重错误总是报告
        if error_record.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            return True
        
        # 检查错误频率
        error_key = f"{error_record.component}:{error_record.error_type}"
        recent_errors = len(self._error_rates.get(error_key, []))
        
        return recent_errors >= self._config.error_report_threshold
    
    def _queue_error_report(self, error_record: ErrorRecord):
        """将错误加入报告队列"""
        with self._report_lock:
            self._report_queue.append(error_record)
            
            # 如果队列过长，立即处理
            if len(self._report_queue) >= 10:
                self._process_error_reports()
    
    def _process_error_reports(self):
        """处理错误报告"""
        if not self._report_queue:
            return
        
        try:
            # 创建报告目录
            report_dir = Path(self._config.report_file_path).parent
            report_dir.mkdir(parents=True, exist_ok=True)
            
            # 读取现有报告
            existing_reports = []
            if Path(self._config.report_file_path).exists():
                with open(self._config.report_file_path, 'r', encoding='utf-8') as f:
                    existing_reports = json.load(f)
            
            # 添加新报告
            with self._report_lock:
                for error_record in self._report_queue:
                    report = {
                        "timestamp": error_record.timestamp,
                        "error_type": error_record.error_type,
                        "message": error_record.message,
                        "severity": error_record.severity.value,
                        "component": error_record.component,
                        "context": error_record.context,
                        "traceback": error_record.traceback
                    }
                    existing_reports.append(report)
                    
                    # 发射报告信号
                    self.error_reported.emit(error_record)
                
                self._report_queue.clear()
            
            # 保存报告
            with open(self._config.report_file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_reports, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"Error reports saved to {self._config.report_file_path}")
            
        except Exception as e:
            self._logger.error(f"Failed to process error reports: {e}")
    
    def _check_system_performance(self):
        """检查系统性能"""
        try:
            import psutil
            
            # 内存检查
            memory = psutil.virtual_memory()
            if memory.percent > self._config.cpu_threshold_percent:
                self.handle_error(
                    f"High memory usage: {memory.percent}%",
                    component="system_monitor",
                    category=ErrorCategory.PERFORMANCE,
                    severity=ErrorSeverity.MEDIUM
                )
            
            # CPU检查
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self._config.cpu_threshold_percent:
                self.handle_error(
                    f"High CPU usage: {cpu_percent}%",
                    component="system_monitor",
                    category=ErrorCategory.PERFORMANCE,
                    severity=ErrorSeverity.MEDIUM
                )
            
            # 磁盘检查
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > self._config.disk_threshold_percent:
                self.handle_error(
                    f"High disk usage: {disk_percent:.1f}%",
                    component="system_monitor",
                    category=ErrorCategory.PERFORMANCE,
                    severity=ErrorSeverity.MEDIUM
                )
                
        except Exception as e:
            self._logger.error(f"Performance monitoring error: {e}")
    
    def _on_recovery_error(self, error_record):
        """处理恢复管理器的错误"""
        self._logger.info(f"Recovery manager handling error: {error_record.error_type}")
    
    def _on_recovery_completed(self, error_record, success):
        """处理恢复完成"""
        if success:
            self._logger.info(f"Recovery successful for: {error_record.error_type}")
        else:
            self._logger.warning(f"Recovery failed for: {error_record.error_type}")
    
    def register_error_handler(self, error_type: str, handler: Callable[[ErrorRecord], bool]):
        """注册错误处理器"""
        self._error_handlers[error_type] = handler
        self._logger.info(f"Error handler registered for: {error_type}")
    
    def register_category_handler(self, category: ErrorCategory, handler: Callable[[ErrorRecord], bool]):
        """注册类别处理器"""
        self._category_handlers[category] = handler
        self._logger.info(f"Category handler registered for: {category.value}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        recent_errors = [
            e for e in self._error_history 
            if time.time() - e.timestamp < 3600
        ]
        
        # 按严重程度统计
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = len([
                e for e in recent_errors if e.severity == severity
            ])
        
        # 按类别统计
        category_counts = {}
        for category in ErrorCategory:
            category_counts[category.value] = len([
                e for e in recent_errors 
                if e.context.get("category") == category.value
            ])
        
        return {
            "total_errors": len(self._error_history),
            "recent_errors": len(recent_errors),
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "error_rates": {k: len(v) for k, v in self._error_rates.items()},
            "top_errors": self._get_top_errors(),
            "error_trend": self._get_error_trend()
        }
    
    def _get_top_errors(self) -> List[Dict[str, Any]]:
        """获取最高频错误"""
        sorted_errors = sorted(
            self._error_stats.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [
            {"error": error, "count": count} 
            for error, count in sorted_errors[:10]
        ]
    
    def _get_error_trend(self) -> Dict[str, List[int]]:
        """获取错误趋势"""
        now = time.time()
        hours = []
        
        for i in range(24):
            hour_start = now - (i + 1) * 3600
            hour_end = now - i * 3600
            
            hour_errors = len([
                e for e in self._error_history
                if hour_start <= e.timestamp < hour_end
            ])
            
            hours.append(hour_errors)
        
        return {"last_24_hours": list(reversed(hours))}
    
    def clear_error_history(self):
        """清除错误历史"""
        self._error_history.clear()
        self._error_stats.clear()
        self._error_rates.clear()
        self._logger.info("Error history cleared")
    
    def export_error_report(self, filepath: str):
        """导出错误报告"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "statistics": self.get_error_statistics(),
                "recent_errors": [
                    {
                        "timestamp": e.timestamp,
                        "error_type": e.error_type,
                        "message": e.message,
                        "severity": e.severity.value,
                        "component": e.component,
                        "context": e.context
                    }
                    for e in self._error_history[-100:]  # 最近100个错误
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"Error report exported to: {filepath}")
            
        except Exception as e:
            self._logger.error(f"Failed to export error report: {e}")


# 便捷函数和装饰器
def get_error_handler() -> ErrorHandler:
    """获取错误处理器实例"""
    try:
        container = get_container()
        return container.resolve(ErrorHandler)
    except Exception:
        # 如果无法获取，创建一个默认的
        return ErrorHandler()


def error_handler(component: str, 
                 category: ErrorCategory = ErrorCategory.APPLICATION,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 code: Optional[ErrorCode] = None,
                 reraise: bool = True):
    """错误处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_error_handler()
                
                context = ErrorContext(
                    component_state={"function": func.__name__, "args": len(args), "kwargs": len(kwargs)},
                    thread_id=threading.current_thread().ident,
                    process_id=os.getpid()
                )
                
                handler.handle_error(
                    error=e,
                    component=component,
                    category=category,
                    severity=severity,
                    context=context,
                    code=code
                )
                
                if reraise:
                    raise
                
                return None
        
        return wrapper
    return decorator


@contextmanager
def error_context(component: str, 
                 category: ErrorCategory = ErrorCategory.APPLICATION,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """错误上下文管理器"""
    handler = get_error_handler()
    
    try:
        yield handler
    except Exception as e:
        context = ErrorContext(
            thread_id=threading.current_thread().ident,
            process_id=os.getpid()
        )
        
        handler.handle_error(
            error=e,
            component=component,
            category=category,
            severity=severity,
            context=context
        )
        
        raise


# 快捷函数
def handle_error(error: Union[Exception, str], 
                component: str,
                category: ErrorCategory = ErrorCategory.APPLICATION,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                **kwargs):
    """处理错误的快捷函数"""
    handler = get_error_handler()
    return handler.handle_error(error, component, category, severity, **kwargs)


def log_error(message: str, component: str, **kwargs):
    """记录错误的快捷函数"""
    return handle_error(message, component, **kwargs)


def log_warning(message: str, component: str, **kwargs):
    """记录警告的快捷函数"""
    return handle_error(message, component, severity=ErrorSeverity.LOW, **kwargs)


def log_critical(message: str, component: str, **kwargs):
    """记录严重错误的快捷函数"""
    return handle_error(message, component, severity=ErrorSeverity.CRITICAL, **kwargs)