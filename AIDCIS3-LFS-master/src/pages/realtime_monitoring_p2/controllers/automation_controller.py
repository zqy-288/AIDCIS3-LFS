"""
自动化控制器
负责管理外部程序启动、CSV监控、数据采集等自动化任务
"""

import os
import subprocess
import logging
from typing import Optional
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QTimer, QThread, QFileSystemWatcher


class AutomationController(QObject):
    """
    自动化控制器
    管理外部采集程序和数据监控
    """
    
    # 信号定义
    process_started = Signal(str)  # process_name
    process_stopped = Signal(str)  # process_name
    csv_file_detected = Signal(str)  # file_path
    automation_log = Signal(str)  # log_message
    error_occurred = Signal(str)  # error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # 日志 - 必须在setup_paths之前初始化
        self.logger = logging.getLogger(__name__)

        # 路径配置
        self.setup_paths()

        # 进程管理
        self.acquisition_process = None
        self.remote_launcher_process = None

        # 文件监控
        self.csv_watcher = QFileSystemWatcher(self)
        self.csv_watcher.directoryChanged.connect(self.on_directory_changed)

        # 定时器
        self.process_monitor_timer = QTimer()
        self.process_monitor_timer.timeout.connect(self.check_process_status)

    def setup_paths(self):
        """设置路径配置"""
        try:
            # 获取项目根目录
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir))))
            
            # 设置各种路径
            self.acquisition_program_path = os.path.join(project_root, "src", "hardware", "Release", "LEConfocalDemo.exe")
            self.launcher_script_path = os.path.join(project_root, "src", "automation", "launcher.py")
            self.remote_launcher_path = os.path.join(project_root, "remote_launcher.py")
            
            # CSV输出文件路径
            self.csv_output_folder = os.path.join(project_root, "src", "hardware", "Release")
            self.output_csv_path = os.path.join(self.csv_output_folder, "R0_C0.csv")
            
            # 归档路径
            self.archive_base_path = os.path.join(project_root, "Data", "CAP1000")
            
            self.logger.info("路径配置完成")
            self.automation_log.emit("📁 路径配置完成")
            
        except Exception as e:
            self.logger.error(f"路径配置失败: {e}")
            self.error_occurred.emit(f"路径配置失败: {e}")
            
    def start_acquisition_program(self) -> bool:
        """启动采集程序"""
        try:
            if not os.path.exists(self.acquisition_program_path):
                self.automation_log.emit(f"⚠️ 采集程序不存在: {self.acquisition_program_path}")
                return False
                
            self.automation_log.emit("🚀 启动外部采集控制程序...")
            
            # 启动外部程序
            self.acquisition_process = subprocess.Popen(
                [self.acquisition_program_path],
                cwd=os.path.dirname(self.acquisition_program_path),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                shell=False
            )
            
            self.automation_log.emit(f"✅ 采集程序启动成功，进程ID: {self.acquisition_process.pid}")
            self.process_started.emit("LEConfocalDemo.exe")
            
            # 启动进程监控
            self.start_process_monitoring()
            
            # 启动CSV文件监控
            self.start_csv_monitoring()
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动采集程序失败: {e}")
            self.automation_log.emit(f"❌ 启动采集程序失败: {e}")
            self.error_occurred.emit(f"启动采集程序失败: {e}")
            return False
            
    def stop_acquisition_program(self) -> bool:
        """停止采集程序"""
        try:
            if self.acquisition_process and self.acquisition_process.poll() is None:
                self.automation_log.emit(f"⏹️ 停止采集程序，进程ID: {self.acquisition_process.pid}")
                
                # 终止外部程序
                self.acquisition_process.terminate()
                
                # 等待程序结束
                try:
                    self.acquisition_process.wait(timeout=5)
                    self.automation_log.emit("✅ 采集程序已正常结束")
                except subprocess.TimeoutExpired:
                    self.automation_log.emit("⚠️ 程序未在5秒内结束，强制终止")
                    self.acquisition_process.kill()
                    self.acquisition_process.wait()
                    self.automation_log.emit("✅ 采集程序已强制终止")
                    
                self.acquisition_process = None
                self.process_stopped.emit("LEConfocalDemo.exe")
                
            # 停止进程监控
            self.stop_process_monitoring()
            
            # 停止CSV监控
            self.stop_csv_monitoring()
            
            return True
            
        except Exception as e:
            self.logger.error(f"停止采集程序失败: {e}")
            self.automation_log.emit(f"❌ 停止采集程序失败: {e}")
            self.error_occurred.emit(f"停止采集程序失败: {e}")
            return False
            
    def start_remote_launcher(self) -> bool:
        """启动远程启动器"""
        try:
            if not os.path.exists(self.remote_launcher_path):
                self.automation_log.emit(f"⚠️ 远程启动器不存在: {self.remote_launcher_path}")
                return False
                
            self.automation_log.emit("🚀 启动远程控制脚本...")
            
            # 启动远程启动器
            self.remote_launcher_process = subprocess.Popen(
                ["python", self.remote_launcher_path],
                cwd=os.path.dirname(self.remote_launcher_path),
                shell=False
            )
            
            self.automation_log.emit(f"✅ 远程控制脚本启动成功，进程ID: {self.remote_launcher_process.pid}")
            self.process_started.emit("remote_launcher.py")
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动远程启动器失败: {e}")
            self.automation_log.emit(f"❌ 启动远程启动器失败: {e}")
            self.error_occurred.emit(f"启动远程启动器失败: {e}")
            return False
            
    def stop_remote_launcher(self) -> bool:
        """停止远程启动器"""
        try:
            if self.remote_launcher_process and self.remote_launcher_process.poll() is None:
                self.automation_log.emit(f"⏹️ 停止远程控制脚本，进程ID: {self.remote_launcher_process.pid}")
                
                self.remote_launcher_process.terminate()
                try:
                    self.remote_launcher_process.wait(timeout=5)
                    self.automation_log.emit("✅ 远程控制脚本已正常结束")
                except subprocess.TimeoutExpired:
                    self.remote_launcher_process.kill()
                    self.remote_launcher_process.wait()
                    self.automation_log.emit("✅ 远程控制脚本已强制终止")
                    
                self.remote_launcher_process = None
                self.process_stopped.emit("remote_launcher.py")
                
            return True
            
        except Exception as e:
            self.logger.error(f"停止远程启动器失败: {e}")
            self.automation_log.emit(f"❌ 停止远程启动器失败: {e}")
            self.error_occurred.emit(f"停止远程启动器失败: {e}")
            return False
            
    def start_csv_monitoring(self):
        """启动CSV文件监控"""
        try:
            if os.path.exists(self.csv_output_folder):
                self.csv_watcher.addPath(self.csv_output_folder)
                self.automation_log.emit(f"📁 开始监控CSV输出目录: {self.csv_output_folder}")
            else:
                self.automation_log.emit(f"⚠️ CSV输出目录不存在: {self.csv_output_folder}")
                
        except Exception as e:
            self.logger.error(f"启动CSV监控失败: {e}")
            self.automation_log.emit(f"❌ 启动CSV监控失败: {e}")
            
    def stop_csv_monitoring(self):
        """停止CSV文件监控"""
        try:
            paths = self.csv_watcher.directories()
            for path in paths:
                self.csv_watcher.removePath(path)
            self.automation_log.emit("📁 CSV文件监控已停止")
            
        except Exception as e:
            self.logger.error(f"停止CSV监控失败: {e}")
            
    def start_process_monitoring(self):
        """启动进程监控"""
        self.process_monitor_timer.start(2000)  # 每2秒检查一次
        self.automation_log.emit("🔍 进程监控已启动")
        
    def stop_process_monitoring(self):
        """停止进程监控"""
        if self.process_monitor_timer.isActive():
            self.process_monitor_timer.stop()
            self.automation_log.emit("🔍 进程监控已停止")
            
    def check_process_status(self):
        """检查进程状态"""
        try:
            # 检查采集程序状态
            if self.acquisition_process:
                if self.acquisition_process.poll() is not None:
                    # 进程已结束
                    self.automation_log.emit("⚠️ 采集程序意外结束")
                    self.acquisition_process = None
                    self.process_stopped.emit("LEConfocalDemo.exe")
                    
            # 检查远程启动器状态
            if self.remote_launcher_process:
                if self.remote_launcher_process.poll() is not None:
                    # 进程已结束
                    self.automation_log.emit("⚠️ 远程控制脚本意外结束")
                    self.remote_launcher_process = None
                    self.process_stopped.emit("remote_launcher.py")
                    
        except Exception as e:
            self.logger.error(f"检查进程状态失败: {e}")
            
    def on_directory_changed(self, path: str):
        """目录变化回调"""
        try:
            self.automation_log.emit(f"📁 检测到目录变化: {path}")
            
            # 检查是否有新的CSV文件
            if os.path.exists(path):
                csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
                for csv_file in csv_files:
                    csv_path = os.path.join(path, csv_file)
                    if csv_file == "R0_C0.csv":  # 目标CSV文件
                        self.automation_log.emit(f"📄 检测到目标CSV文件: {csv_file}")
                        self.csv_file_detected.emit(csv_path)
                        
        except Exception as e:
            self.logger.error(f"处理目录变化失败: {e}")
            
    def is_acquisition_running(self) -> bool:
        """检查采集程序是否运行"""
        return self.acquisition_process is not None and self.acquisition_process.poll() is None
        
    def is_remote_launcher_running(self) -> bool:
        """检查远程启动器是否运行"""
        return self.remote_launcher_process is not None and self.remote_launcher_process.poll() is None
