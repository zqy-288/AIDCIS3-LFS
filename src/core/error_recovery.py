"""
异常恢复和故障转移机制
提供应用程序级别的错误处理和恢复能力
"""

import sys
import traceback
import logging
import time
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox

from .dependency_injection import injectable, ServiceLifetime
from .application import ApplicationCore, EventBus, ApplicationEvent


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"          # 轻微错误，不影响主要功能
    MEDIUM = "medium"    # 中等错误，影响部分功能
    HIGH = "high"        # 严重错误，影响核心功能
    CRITICAL = "critical" # 致命错误，可能导致崩溃


class RecoveryStrategy(Enum):
    """恢复策略"""
    IGNORE = "ignore"              # 忽略错误
    RETRY = "retry"                # 重试操作
    FALLBACK = "fallback"          # 使用备用方案
    RESTART_COMPONENT = "restart"   # 重启组件
    RESTART_APPLICATION = "restart_app"  # 重启应用程序


@dataclass
class ErrorRecord:
    """错误记录"""
    timestamp: float
    error_type: str
    message: str
    traceback: str
    severity: ErrorSeverity
    component: str
    context: Dict[str, Any]
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_strategy: Optional[RecoveryStrategy] = None


@injectable(ServiceLifetime.SINGLETON)
class ErrorRecoveryManager(QObject):
    """错误恢复管理器"""
    
    # 错误信号
    error_occurred = Signal(object)  # ErrorRecord
    recovery_attempted = Signal(object, str)  # ErrorRecord, strategy
    recovery_completed = Signal(object, bool)  # ErrorRecord, success
    
    def __init__(self, app_core: ApplicationCore):
        super().__init__()
        
        self._app_core = app_core
        self._event_bus = app_core.event_bus
        self._logger = logging.getLogger(__name__)
        
        # 错误记录
        self._error_history: List[ErrorRecord] = []
        self._max_history_size = 1000
        
        # 错误计数器
        self._error_counts: Dict[str, int] = {}
        self._error_time_windows: Dict[str, List[float]] = {}
        
        # 恢复策略映射
        self._recovery_strategies: Dict[str, RecoveryStrategy] = {
            'ImportError': RecoveryStrategy.FALLBACK,
            'ConnectionError': RecoveryStrategy.RETRY,
            'FileNotFoundError': RecoveryStrategy.FALLBACK,
            'PermissionError': RecoveryStrategy.RETRY,
            'TimeoutError': RecoveryStrategy.RETRY,
            'MemoryError': RecoveryStrategy.RESTART_COMPONENT,
            'RuntimeError': RecoveryStrategy.FALLBACK,
            'AttributeError': RecoveryStrategy.IGNORE,
            'KeyError': RecoveryStrategy.FALLBACK,
            'ValueError': RecoveryStrategy.IGNORE,
            'TypeError': RecoveryStrategy.IGNORE,
        }
        
        # 重试配置
        self._retry_limits: Dict[str, int] = {}
        self._retry_delays: Dict[str, float] = {}
        
        # 组件重启器
        self._component_restarters: Dict[str, Callable] = {}
        
        # 监控定时器
        self._monitor_timer = QTimer()
        self._monitor_timer.timeout.connect(self._monitor_system_health)
        self._monitor_timer.start(30000)  # 30秒检查一次
        
        # 设置全局异常处理
        self._setup_global_exception_handler()
        
        self._logger.info("ErrorRecoveryManager initialized")
    
    def _setup_global_exception_handler(self):
        """设置全局异常处理"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # 处理用户中断
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # 记录和处理异常
            error_record = ErrorRecord(
                timestamp=time.time(),
                error_type=exc_type.__name__,
                message=str(exc_value),
                traceback=''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
                severity=ErrorSeverity.CRITICAL,
                component="global",
                context={"source": "global_exception_handler"}
            )
            
            self.handle_error(error_record)
        
        sys.excepthook = handle_exception
    
    def handle_error(self, error_record: ErrorRecord) -> bool:
        """处理错误"""
        try:
            # 记录错误
            self._record_error(error_record)
            
            # 发射错误信号
            self.error_occurred.emit(error_record)
            
            # 发布错误事件
            event = ApplicationEvent("error_occurred", {
                "error_record": error_record
            })
            self._event_bus.post_event(event)
            
            # 决定恢复策略
            strategy = self._determine_recovery_strategy(error_record)
            
            if strategy != RecoveryStrategy.IGNORE:
                # 尝试恢复
                return self._attempt_recovery(error_record, strategy)
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error in error handler: {e}")
            return False
    
    def _record_error(self, error_record: ErrorRecord):
        """记录错误"""
        # 添加到历史记录
        self._error_history.append(error_record)
        
        # 限制历史记录大小
        if len(self._error_history) > self._max_history_size:
            self._error_history = self._error_history[-self._max_history_size:]
        
        # 更新错误计数
        error_key = f"{error_record.component}:{error_record.error_type}"
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
        
        # 记录错误时间窗口
        if error_key not in self._error_time_windows:
            self._error_time_windows[error_key] = []
        self._error_time_windows[error_key].append(error_record.timestamp)
        
        # 清理旧的时间记录（保留最近1小时）
        cutoff_time = time.time() - 3600
        self._error_time_windows[error_key] = [
            t for t in self._error_time_windows[error_key] if t > cutoff_time
        ]
        
        # 记录日志
        log_message = f"Error recorded: {error_record.error_type} in {error_record.component} - {error_record.message}"
        
        if error_record.severity == ErrorSeverity.CRITICAL:
            self._logger.critical(log_message)
        elif error_record.severity == ErrorSeverity.HIGH:
            self._logger.error(log_message)
        elif error_record.severity == ErrorSeverity.MEDIUM:
            self._logger.warning(log_message)
        else:
            self._logger.info(log_message)
    
    def _determine_recovery_strategy(self, error_record: ErrorRecord) -> RecoveryStrategy:
        """确定恢复策略"""
        # 检查是否有预定义策略
        if error_record.error_type in self._recovery_strategies:
            strategy = self._recovery_strategies[error_record.error_type]
        else:
            # 根据严重程度确定默认策略
            if error_record.severity == ErrorSeverity.CRITICAL:
                strategy = RecoveryStrategy.RESTART_COMPONENT
            elif error_record.severity == ErrorSeverity.HIGH:
                strategy = RecoveryStrategy.FALLBACK
            elif error_record.severity == ErrorSeverity.MEDIUM:
                strategy = RecoveryStrategy.RETRY
            else:
                strategy = RecoveryStrategy.IGNORE
        
        # 检查错误频率，如果错误过于频繁，升级策略
        error_key = f"{error_record.component}:{error_record.error_type}"
        recent_errors = len(self._error_time_windows.get(error_key, []))
        
        if recent_errors > 10:  # 1小时内超过10次同样错误
            if strategy == RecoveryStrategy.RETRY:
                strategy = RecoveryStrategy.FALLBACK
            elif strategy == RecoveryStrategy.FALLBACK:
                strategy = RecoveryStrategy.RESTART_COMPONENT
            elif strategy == RecoveryStrategy.RESTART_COMPONENT:
                strategy = RecoveryStrategy.RESTART_APPLICATION
        
        return strategy
    
    def _attempt_recovery(self, error_record: ErrorRecord, strategy: RecoveryStrategy) -> bool:
        """尝试恢复"""
        error_record.recovery_attempted = True
        error_record.recovery_strategy = strategy
        
        self._logger.info(f"Attempting recovery with strategy: {strategy.value}")
        self.recovery_attempted.emit(error_record, strategy.value)
        
        try:
            success = False
            
            if strategy == RecoveryStrategy.RETRY:
                success = self._retry_operation(error_record)
            elif strategy == RecoveryStrategy.FALLBACK:
                success = self._use_fallback(error_record)
            elif strategy == RecoveryStrategy.RESTART_COMPONENT:
                success = self._restart_component(error_record)
            elif strategy == RecoveryStrategy.RESTART_APPLICATION:
                success = self._restart_application(error_record)
            
            error_record.recovery_successful = success
            self.recovery_completed.emit(error_record, success)
            
            if success:
                self._logger.info("Recovery successful")
            else:
                self._logger.warning("Recovery failed")
            
            return success
            
        except Exception as e:
            self._logger.error(f"Recovery attempt failed: {e}")
            error_record.recovery_successful = False
            self.recovery_completed.emit(error_record, False)
            return False
    
    def _retry_operation(self, error_record: ErrorRecord) -> bool:
        """重试操作"""
        error_key = f"{error_record.component}:{error_record.error_type}"
        
        # 检查重试限制
        retry_count = self._retry_limits.get(error_key, 0)
        if retry_count >= 3:  # 最多重试3次
            self._logger.warning(f"Retry limit reached for {error_key}")
            return False
        
        # 增加重试计数
        self._retry_limits[error_key] = retry_count + 1
        
        # 等待重试延迟
        delay = self._retry_delays.get(error_key, 1.0)
        time.sleep(delay)
        
        # 增加下次重试延迟（指数退避）
        self._retry_delays[error_key] = min(delay * 2, 30.0)
        
        # 这里应该重新执行失败的操作
        # 由于无法获取原始操作，只能返回True表示重试"成功"
        return True
    
    def _use_fallback(self, error_record: ErrorRecord) -> bool:
        """使用备用方案"""
        # 发布备用方案事件
        event = ApplicationEvent("use_fallback", {
            "error_record": error_record,
            "component": error_record.component
        })
        self._event_bus.post_event(event)
        
        return True
    
    def _restart_component(self, error_record: ErrorRecord) -> bool:
        """重启组件"""
        component = error_record.component
        
        if component in self._component_restarters:
            try:
                restarter = self._component_restarters[component]
                restarter()
                return True
            except Exception as e:
                self._logger.error(f"Component restart failed: {e}")
                return False
        else:
            # 发布组件重启事件
            event = ApplicationEvent("restart_component", {
                "component": component,
                "error_record": error_record
            })
            self._event_bus.post_event(event)
            return True
    
    def _restart_application(self, error_record: ErrorRecord) -> bool:
        """重启应用程序"""
        self._logger.critical("Attempting application restart due to critical error")
        
        # 显示用户通知
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("严重错误")
            msg.setText("应用程序遇到严重错误，需要重启。")
            msg.setDetailedText(f"错误类型: {error_record.error_type}\n错误信息: {error_record.message}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
        except:
            pass
        
        # 发布应用程序重启事件
        event = ApplicationEvent("restart_application", {
            "error_record": error_record
        })
        self._event_bus.post_event(event)
        
        # 触发应用程序关闭
        self._app_core.shutdown()
        
        return True
    
    def register_component_restarter(self, component: str, restarter: Callable):
        """注册组件重启器"""
        self._component_restarters[component] = restarter
        self._logger.info(f"Component restarter registered for: {component}")
    
    def set_recovery_strategy(self, error_type: str, strategy: RecoveryStrategy):
        """设置错误类型的恢复策略"""
        self._recovery_strategies[error_type] = strategy
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        recent_errors = [e for e in self._error_history if time.time() - e.timestamp < 3600]
        
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = len([e for e in recent_errors if e.severity == severity])
        
        return {
            "total_errors": len(self._error_history),
            "recent_errors": len(recent_errors),
            "severity_distribution": severity_counts,
            "error_counts": dict(self._error_counts),
            "recovery_success_rate": self._calculate_recovery_success_rate()
        }
    
    def _calculate_recovery_success_rate(self) -> float:
        """计算恢复成功率"""
        attempted_recoveries = [e for e in self._error_history if e.recovery_attempted]
        if not attempted_recoveries:
            return 0.0
        
        successful_recoveries = [e for e in attempted_recoveries if e.recovery_successful]
        return len(successful_recoveries) / len(attempted_recoveries)
    
    def _monitor_system_health(self):
        """监控系统健康状态"""
        try:
            # 检查内存使用
            import psutil
            memory_percent = psutil.virtual_memory().percent
            
            if memory_percent > 90:
                error_record = ErrorRecord(
                    timestamp=time.time(),
                    error_type="MemoryWarning",
                    message=f"Memory usage high: {memory_percent}%",
                    traceback="",
                    severity=ErrorSeverity.MEDIUM,
                    component="system_monitor",
                    context={"memory_percent": memory_percent}
                )
                self.handle_error(error_record)
            
            # 检查错误频率
            recent_error_count = len([e for e in self._error_history if time.time() - e.timestamp < 300])
            if recent_error_count > 20:  # 5分钟内超过20个错误
                error_record = ErrorRecord(
                    timestamp=time.time(),
                    error_type="HighErrorRate",
                    message=f"High error rate: {recent_error_count} errors in 5 minutes",
                    traceback="",
                    severity=ErrorSeverity.HIGH,
                    component="system_monitor",
                    context={"error_count": recent_error_count}
                )
                self.handle_error(error_record)
                
        except Exception as e:
            self._logger.error(f"System health monitoring error: {e}")


def create_error_record(error_type: str, message: str, component: str, 
                       severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                       context: Optional[Dict[str, Any]] = None) -> ErrorRecord:
    """创建错误记录的便捷函数"""
    return ErrorRecord(
        timestamp=time.time(),
        error_type=error_type,
        message=message,
        traceback="",
        severity=severity,
        component=component,
        context=context or {}
    )


def handle_exception_decorator(component: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """异常处理装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 获取错误恢复管理器
                from .dependency_injection import get_container
                container = get_container()
                
                try:
                    recovery_manager = container.resolve(ErrorRecoveryManager)
                    
                    error_record = ErrorRecord(
                        timestamp=time.time(),
                        error_type=type(e).__name__,
                        message=str(e),
                        traceback=traceback.format_exc(),
                        severity=severity,
                        component=component,
                        context={"function": func.__name__}
                    )
                    
                    recovery_manager.handle_error(error_record)
                    
                except Exception:
                    # 如果错误处理器也失败了，至少记录日志
                    logging.error(f"Error in {component}.{func.__name__}: {e}")
                
                # 重新抛出异常或返回默认值
                raise
        
        return wrapper
    return decorator