"""
异常报告系统
提供异常报告生成、发送、监控和分析功能

作者: AI-4 测试与质量保证工程师
创建时间: 2025-07-17
"""

import os
import json
import smtplib
import sqlite3
import threading
import time
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    from email.mime.base import MimeBase
    from email import encoders
except ImportError:
    # 备用导入
    MimeText = None
    MimeMultipart = None
    MimeBase = None
    encoders = None
import zipfile
import tempfile

from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtWidgets import QApplication, QMessageBox

from .dependency_injection import injectable, ServiceLifetime
from .error_handler import ErrorHandler, ErrorRecord, ErrorSeverity, ErrorCategory
from .logger import Logger, LogLevel


@dataclass
class ReportConfig:
    """报告配置"""
    # 报告生成
    auto_generate: bool = True
    report_interval: int = 3600  # 1小时
    max_report_size: int = 10 * 1024 * 1024  # 10MB
    
    # 报告存储
    report_dir: str = "reports"
    database_path: str = "reports/error_reports.db"
    
    # 邮件配置
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    sender_email: str = ""
    recipient_emails: List[str] = None
    
    # 监控配置
    critical_threshold: int = 5
    error_threshold: int = 20
    warning_threshold: int = 50
    
    # 报告内容
    include_logs: bool = True
    include_statistics: bool = True
    include_system_info: bool = True
    include_screenshots: bool = False
    
    # 压缩配置
    compress_reports: bool = True
    compression_level: int = 9


@dataclass
class ErrorReport:
    """错误报告"""
    id: str
    timestamp: float
    severity: ErrorSeverity
    category: ErrorCategory
    title: str
    summary: str
    error_records: List[ErrorRecord]
    statistics: Dict[str, Any]
    system_info: Dict[str, Any]
    attachments: List[str]
    status: str = "pending"
    sent_at: Optional[float] = None
    sent_to: List[str] = None


@dataclass
class AlertConfig:
    """告警配置"""
    enabled: bool = True
    severity_levels: List[ErrorSeverity] = None
    rate_threshold: int = 10  # 每分钟错误数
    burst_threshold: int = 5   # 连续错误数
    cooldown_period: int = 300  # 5分钟冷却期
    notification_methods: List[str] = None  # email, system, custom


class ErrorReportDatabase:
    """错误报告数据库"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建报告表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_reports (
                    id TEXT PRIMARY KEY,
                    timestamp REAL,
                    severity TEXT,
                    category TEXT,
                    title TEXT,
                    summary TEXT,
                    error_count INTEGER,
                    statistics TEXT,
                    system_info TEXT,
                    attachments TEXT,
                    status TEXT,
                    sent_at REAL,
                    sent_to TEXT
                )
            """)
            
            # 创建错误记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT,
                    timestamp REAL,
                    error_type TEXT,
                    message TEXT,
                    component TEXT,
                    severity TEXT,
                    traceback TEXT,
                    context TEXT,
                    FOREIGN KEY (report_id) REFERENCES error_reports (id)
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_timestamp ON error_reports(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_severity ON error_reports(severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_report_id ON error_records(report_id)")
            
            conn.commit()
    
    def save_report(self, report: ErrorReport):
        """保存报告"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 保存报告
            cursor.execute("""
                INSERT OR REPLACE INTO error_reports 
                (id, timestamp, severity, category, title, summary, error_count, 
                 statistics, system_info, attachments, status, sent_at, sent_to)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.id,
                report.timestamp,
                report.severity.value,
                report.category.value,
                report.title,
                report.summary,
                len(report.error_records),
                json.dumps(report.statistics),
                json.dumps(report.system_info),
                json.dumps(report.attachments),
                report.status,
                report.sent_at,
                json.dumps(report.sent_to) if report.sent_to else None
            ))
            
            # 保存错误记录
            for record in report.error_records:
                cursor.execute("""
                    INSERT INTO error_records 
                    (report_id, timestamp, error_type, message, component, severity, traceback, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report.id,
                    record.timestamp,
                    record.error_type,
                    record.message,
                    record.component,
                    record.severity.value,
                    record.traceback,
                    json.dumps(record.context)
                ))
            
            conn.commit()
    
    def get_report(self, report_id: str) -> Optional[ErrorReport]:
        """获取报告"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM error_reports WHERE id = ?", (report_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # 获取错误记录
            cursor.execute("SELECT * FROM error_records WHERE report_id = ?", (report_id,))
            record_rows = cursor.fetchall()
            
            error_records = []
            for record_row in record_rows:
                error_records.append(ErrorRecord(
                    timestamp=record_row[2],
                    error_type=record_row[3],
                    message=record_row[4],
                    traceback=record_row[6],
                    severity=ErrorSeverity(record_row[5]),
                    component=record_row[4],
                    context=json.loads(record_row[7])
                ))
            
            return ErrorReport(
                id=row[0],
                timestamp=row[1],
                severity=ErrorSeverity(row[2]),
                category=ErrorCategory(row[3]),
                title=row[4],
                summary=row[5],
                error_records=error_records,
                statistics=json.loads(row[7]),
                system_info=json.loads(row[8]),
                attachments=json.loads(row[9]),
                status=row[10],
                sent_at=row[11],
                sent_to=json.loads(row[12]) if row[12] else None
            )
    
    def get_reports(self, 
                   start_time: Optional[float] = None,
                   end_time: Optional[float] = None,
                   severity: Optional[ErrorSeverity] = None,
                   limit: int = 100) -> List[ErrorReport]:
        """获取报告列表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM error_reports WHERE 1=1"
            params = []
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            if severity:
                query += " AND severity = ?"
                params.append(severity.value)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            reports = []
            for row in rows:
                report = ErrorReport(
                    id=row[0],
                    timestamp=row[1],
                    severity=ErrorSeverity(row[2]),
                    category=ErrorCategory(row[3]),
                    title=row[4],
                    summary=row[5],
                    error_records=[],  # 不加载完整记录
                    statistics=json.loads(row[7]),
                    system_info=json.loads(row[8]),
                    attachments=json.loads(row[9]),
                    status=row[10],
                    sent_at=row[11],
                    sent_to=json.loads(row[12]) if row[12] else None
                )
                reports.append(report)
            
            return reports
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 总报告数
            cursor.execute("SELECT COUNT(*) FROM error_reports")
            total_reports = cursor.fetchone()[0]
            
            # 按严重程度统计
            cursor.execute("""
                SELECT severity, COUNT(*) 
                FROM error_reports 
                GROUP BY severity
            """)
            severity_stats = dict(cursor.fetchall())
            
            # 按类别统计
            cursor.execute("""
                SELECT category, COUNT(*) 
                FROM error_reports 
                GROUP BY category
            """)
            category_stats = dict(cursor.fetchall())
            
            # 最近24小时的报告
            day_ago = time.time() - 86400
            cursor.execute("""
                SELECT COUNT(*) 
                FROM error_reports 
                WHERE timestamp > ?
            """, (day_ago,))
            recent_reports = cursor.fetchone()[0]
            
            return {
                "total_reports": total_reports,
                "recent_reports": recent_reports,
                "severity_distribution": severity_stats,
                "category_distribution": category_stats
            }


@injectable(ServiceLifetime.SINGLETON)
class ErrorReportingSystem(QObject):
    """错误报告系统"""
    
    # 信号
    report_generated = Signal(object)  # ErrorReport
    report_sent = Signal(object)       # ErrorReport
    alert_triggered = Signal(str, object)  # alert_type, data
    
    def __init__(self, 
                 config: Optional[ReportConfig] = None,
                 error_handler: Optional[ErrorHandler] = None,
                 logger: Optional[Logger] = None):
        super().__init__()
        
        self.config = config or ReportConfig()
        self.error_handler = error_handler
        self.logger = logger
        
        # 初始化数据库
        self.database = ErrorReportDatabase(self.config.database_path)
        
        # 报告生成器
        self._report_generator = None
        self._report_timer = None
        
        # 告警系统
        self._alert_config = AlertConfig()
        self._alert_counters = {}
        self._alert_cooldowns = {}
        
        # 错误缓冲区
        self._error_buffer: List[ErrorRecord] = []
        self._buffer_lock = threading.Lock()
        
        # 初始化系统
        self._init_system()
        
        if self.logger:
            self.logger.info("ErrorReportingSystem initialized", component="ErrorReporting")
    
    def _init_system(self):
        """初始化系统"""
        # 创建报告目录
        Path(self.config.report_dir).mkdir(parents=True, exist_ok=True)
        
        # 连接错误处理器
        if self.error_handler:
            self.error_handler.error_captured.connect(self._on_error_captured)
        
        # 设置报告生成定时器
        if self.config.auto_generate:
            self._report_timer = QTimer()
            self._report_timer.timeout.connect(self._generate_periodic_report)
            self._report_timer.start(self.config.report_interval * 1000)
    
    def _on_error_captured(self, error_record: ErrorRecord):
        """处理捕获的错误"""
        with self._buffer_lock:
            self._error_buffer.append(error_record)
        
        # 检查是否需要触发告警
        self._check_alerts(error_record)
        
        # 检查是否需要立即生成报告
        if error_record.severity == ErrorSeverity.CRITICAL:
            self._generate_critical_report(error_record)
    
    def _check_alerts(self, error_record: ErrorRecord):
        """检查告警条件"""
        if not self._alert_config.enabled:
            return
        
        current_time = time.time()
        
        # 检查严重程度告警
        if (self._alert_config.severity_levels and 
            error_record.severity in self._alert_config.severity_levels):
            self._trigger_alert("severity", error_record)
        
        # 检查错误率告警
        rate_key = f"rate_{error_record.component}"
        if rate_key not in self._alert_counters:
            self._alert_counters[rate_key] = []
        
        self._alert_counters[rate_key].append(current_time)
        
        # 清理旧记录
        minute_ago = current_time - 60
        self._alert_counters[rate_key] = [
            t for t in self._alert_counters[rate_key] if t > minute_ago
        ]
        
        # 检查是否超过阈值
        if len(self._alert_counters[rate_key]) > self._alert_config.rate_threshold:
            if self._can_send_alert(rate_key):
                self._trigger_alert("rate", {
                    "component": error_record.component,
                    "rate": len(self._alert_counters[rate_key]),
                    "threshold": self._alert_config.rate_threshold
                })
    
    def _can_send_alert(self, alert_key: str) -> bool:
        """检查是否可以发送告警"""
        current_time = time.time()
        
        if alert_key in self._alert_cooldowns:
            if current_time - self._alert_cooldowns[alert_key] < self._alert_config.cooldown_period:
                return False
        
        self._alert_cooldowns[alert_key] = current_time
        return True
    
    def _trigger_alert(self, alert_type: str, data: Any):
        """触发告警"""
        self.alert_triggered.emit(alert_type, data)
        
        if self.logger:
            self.logger.warning(
                f"Alert triggered: {alert_type}",
                component="ErrorReporting",
                alert_type=alert_type,
                alert_data=data
            )
        
        # 发送通知
        if self._alert_config.notification_methods:
            for method in self._alert_config.notification_methods:
                if method == "email":
                    self._send_alert_email(alert_type, data)
                elif method == "system":
                    self._show_system_notification(alert_type, data)
    
    def _send_alert_email(self, alert_type: str, data: Any):
        """发送告警邮件"""
        if not self.config.smtp_server or not self.config.recipient_emails:
            return
        
        if not MimeMultipart or not MimeText:
            if self.logger:
                self.logger.warning("Email modules not available, skipping email alert", component="ErrorReporting")
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.config.sender_email
            msg['To'] = ', '.join(self.config.recipient_emails)
            msg['Subject'] = f"AIDCIS3 Error Alert: {alert_type}"
            
            body = f"""
            Error Alert Triggered
            
            Type: {alert_type}
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Data: {json.dumps(data, indent=2)}
            
            Please check the system for more details.
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.config.sender_email, self.config.recipient_emails, text)
            server.quit()
            
            if self.logger:
                self.logger.info("Alert email sent", component="ErrorReporting")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to send alert email: {e}", component="ErrorReporting")
    
    def _show_system_notification(self, alert_type: str, data: Any):
        """显示系统通知"""
        try:
            if QApplication.instance():
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("错误告警")
                msg.setText(f"系统触发了 {alert_type} 告警")
                msg.setDetailedText(f"详细信息: {json.dumps(data, indent=2)}")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to show system notification: {e}", component="ErrorReporting")
    
    def _generate_periodic_report(self):
        """生成定期报告"""
        try:
            with self._buffer_lock:
                if not self._error_buffer:
                    return
                
                errors = list(self._error_buffer)
                self._error_buffer.clear()
            
            # 生成报告
            report = self._create_report(
                errors=errors,
                title="Periodic Error Report",
                summary=f"Periodic report containing {len(errors)} error(s)"
            )
            
            # 保存报告
            self.database.save_report(report)
            
            # 发射信号
            self.report_generated.emit(report)
            
            if self.logger:
                self.logger.info(f"Periodic report generated: {report.id}", component="ErrorReporting")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to generate periodic report: {e}", component="ErrorReporting")
    
    def _generate_critical_report(self, error_record: ErrorRecord):
        """生成严重错误报告"""
        try:
            report = self._create_report(
                errors=[error_record],
                title="Critical Error Report",
                summary=f"Critical error in {error_record.component}: {error_record.message}"
            )
            
            # 保存报告
            self.database.save_report(report)
            
            # 发射信号
            self.report_generated.emit(report)
            
            # 立即发送
            if self.config.recipient_emails:
                self._send_report_email(report)
            
            if self.logger:
                self.logger.critical(f"Critical error report generated: {report.id}", component="ErrorReporting")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to generate critical report: {e}", component="ErrorReporting")
    
    def _create_report(self, 
                      errors: List[ErrorRecord],
                      title: str,
                      summary: str) -> ErrorReport:
        """创建报告"""
        import uuid
        import platform
        import psutil
        
        # 确定最高严重程度
        max_severity = ErrorSeverity.LOW
        categories = set()
        
        for error in errors:
            if error.severity.value > max_severity.value:
                max_severity = error.severity
            if "category" in error.context:
                categories.add(error.context["category"])
        
        # 统计信息
        statistics = {
            "total_errors": len(errors),
            "error_types": {},
            "components": {},
            "severity_distribution": {}
        }
        
        for error in errors:
            # 错误类型统计
            error_type = error.error_type
            statistics["error_types"][error_type] = statistics["error_types"].get(error_type, 0) + 1
            
            # 组件统计
            component = error.component
            statistics["components"][component] = statistics["components"].get(component, 0) + 1
            
            # 严重程度统计
            severity = error.severity.value
            statistics["severity_distribution"][severity] = statistics["severity_distribution"].get(severity, 0) + 1
        
        # 系统信息
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        }
        
        # 创建报告
        report = ErrorReport(
            id=str(uuid.uuid4()),
            timestamp=time.time(),
            severity=max_severity,
            category=list(categories)[0] if categories else ErrorCategory.APPLICATION,
            title=title,
            summary=summary,
            error_records=errors,
            statistics=statistics,
            system_info=system_info,
            attachments=[]
        )
        
        return report
    
    def _send_report_email(self, report: ErrorReport):
        """发送报告邮件"""
        if not self.config.smtp_server or not self.config.recipient_emails:
            return
        
        if not MimeMultipart or not MimeText:
            if self.logger:
                self.logger.warning("Email modules not available, skipping report email", component="ErrorReporting")
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.config.sender_email
            msg['To'] = ', '.join(self.config.recipient_emails)
            msg['Subject'] = f"AIDCIS3 Error Report: {report.title}"
            
            # 邮件正文
            body = f"""
            Error Report Generated
            
            Title: {report.title}
            Summary: {report.summary}
            Severity: {report.severity.value}
            Time: {datetime.fromtimestamp(report.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
            
            Statistics:
            - Total Errors: {report.statistics['total_errors']}
            - Error Types: {json.dumps(report.statistics['error_types'], indent=2)}
            - Components: {json.dumps(report.statistics['components'], indent=2)}
            
            System Information:
            - Platform: {report.system_info['platform']}
            - CPU Count: {report.system_info['cpu_count']}
            - Memory: {report.system_info['memory_available'] / (1024**3):.2f} GB available
            - Disk Usage: {report.system_info['disk_usage']}%
            
            Please check the system for more details.
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # 添加详细报告附件
            if self.config.include_logs:
                detailed_report = self._generate_detailed_report(report)
                attachment = MimeBase('application', 'octet-stream')
                attachment.set_payload(detailed_report.encode('utf-8'))
                encoders.encode_base64(attachment)
                attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename="error_report_{report.id}.json"'
                )
                msg.attach(attachment)
            
            # 发送邮件
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.config.sender_email, self.config.recipient_emails, text)
            server.quit()
            
            # 更新报告状态
            report.status = "sent"
            report.sent_at = time.time()
            report.sent_to = self.config.recipient_emails
            
            self.database.save_report(report)
            self.report_sent.emit(report)
            
            if self.logger:
                self.logger.info(f"Report email sent: {report.id}", component="ErrorReporting")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to send report email: {e}", component="ErrorReporting")
    
    def _generate_detailed_report(self, report: ErrorReport) -> str:
        """生成详细报告"""
        detailed_data = {
            "report_info": {
                "id": report.id,
                "timestamp": report.timestamp,
                "title": report.title,
                "summary": report.summary,
                "severity": report.severity.value,
                "category": report.category.value
            },
            "error_records": [
                {
                    "timestamp": record.timestamp,
                    "error_type": record.error_type,
                    "message": record.message,
                    "component": record.component,
                    "severity": record.severity.value,
                    "traceback": record.traceback,
                    "context": record.context
                }
                for record in report.error_records
            ],
            "statistics": report.statistics,
            "system_info": report.system_info
        }
        
        return json.dumps(detailed_data, indent=2, ensure_ascii=False)
    
    # 公共接口
    def generate_report(self, title: str, summary: str) -> ErrorReport:
        """手动生成报告"""
        with self._buffer_lock:
            errors = list(self._error_buffer)
            self._error_buffer.clear()
        
        report = self._create_report(errors, title, summary)
        self.database.save_report(report)
        self.report_generated.emit(report)
        
        return report
    
    def send_report(self, report_id: str) -> bool:
        """发送报告"""
        report = self.database.get_report(report_id)
        if not report:
            return False
        
        self._send_report_email(report)
        return True
    
    def get_report(self, report_id: str) -> Optional[ErrorReport]:
        """获取报告"""
        return self.database.get_report(report_id)
    
    def get_reports(self, **kwargs) -> List[ErrorReport]:
        """获取报告列表"""
        return self.database.get_reports(**kwargs)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.database.get_statistics()
    
    def set_alert_config(self, config: AlertConfig):
        """设置告警配置"""
        self._alert_config = config
    
    def clear_error_buffer(self):
        """清空错误缓冲区"""
        with self._buffer_lock:
            self._error_buffer.clear()
    
    def export_reports(self, output_path: str, 
                      start_time: Optional[float] = None,
                      end_time: Optional[float] = None) -> bool:
        """导出报告"""
        try:
            reports = self.database.get_reports(start_time=start_time, end_time=end_time)
            
            export_data = {
                "export_info": {
                    "timestamp": time.time(),
                    "start_time": start_time,
                    "end_time": end_time,
                    "total_reports": len(reports)
                },
                "reports": [
                    {
                        "id": report.id,
                        "timestamp": report.timestamp,
                        "title": report.title,
                        "summary": report.summary,
                        "severity": report.severity.value,
                        "category": report.category.value,
                        "statistics": report.statistics,
                        "system_info": report.system_info
                    }
                    for report in reports
                ]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to export reports: {e}", component="ErrorReporting")
            return False


# 便捷函数
def get_error_reporting_system() -> ErrorReportingSystem:
    """获取错误报告系统实例"""
    try:
        from .dependency_injection import get_container
        container = get_container()
        return container.resolve(ErrorReportingSystem)
    except Exception:
        return ErrorReportingSystem()


def generate_error_report(title: str, summary: str) -> ErrorReport:
    """生成错误报告"""
    system = get_error_reporting_system()
    return system.generate_report(title, summary)


def send_error_report(report_id: str) -> bool:
    """发送错误报告"""
    system = get_error_reporting_system()
    return system.send_report(report_id)