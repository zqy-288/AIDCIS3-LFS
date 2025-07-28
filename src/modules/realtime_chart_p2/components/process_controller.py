"""
进程控制组件
负责启动、停止和监控外部进程
"""
import subprocess
import os
import signal
import threading
from typing import Optional, Dict, List, Callable
from PySide6.QtCore import QObject, QTimer, Signal
import psutil
from datetime import datetime
from ..utils.constants import PROCESS_CHECK_INTERVAL, PROCESS_TIMEOUT


class ProcessController(QObject):
    """进程控制器"""
    
    # 信号定义
    process_started = Signal(int)  # PID
    process_stopped = Signal(int, int)  # PID, 退出码
    process_output = Signal(str)  # 输出文本
    process_error = Signal(str)  # 错误信息
    status_changed = Signal(str)  # 状态变化
    
    def __init__(self):
        super().__init__()
        
        # 进程信息
        self._process = None
        self._pid = None
        self._command = None
        self._working_dir = None
        
        # 状态
        self._status = "stopped"  # stopped, starting, running, stopping
        self._start_time = None
        self._stop_time = None
        
        # 监控定时器
        self._monitor_timer = QTimer()
        self._monitor_timer.timeout.connect(self._monitor_process)
        self._monitor_timer.setInterval(PROCESS_CHECK_INTERVAL)
        
        # 输出捕获线程
        self._output_thread = None
        self._error_thread = None
        self._stop_threads = False
        
        # 进程统计
        self._cpu_usage = 0.0
        self._memory_usage = 0.0
        
        # 回调函数
        self._output_callback = None
        self._error_callback = None
        
    def set_command(self, command: str, working_dir: Optional[str] = None):
        """设置要执行的命令"""
        self._command = command
        self._working_dir = working_dir or os.getcwd()
        
    def start_process(self, command: Optional[str] = None, working_dir: Optional[str] = None) -> bool:
        """启动进程"""
        if self._status == "running":
            self.process_error.emit("进程已在运行中")
            return False
            
        if command:
            self._command = command
        if working_dir:
            self._working_dir = working_dir
            
        if not self._command:
            self.process_error.emit("未设置要执行的命令")
            return False
            
        try:
            self._set_status("starting")
            
            # 启动进程
            self._process = subprocess.Popen(
                self._command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                cwd=self._working_dir,
                bufsize=1,
                universal_newlines=True,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self._pid = self._process.pid
            self._start_time = datetime.now()
            self._stop_threads = False
            
            # 启动输出捕获线程
            self._output_thread = threading.Thread(
                target=self._capture_output,
                args=(self._process.stdout, self._handle_output)
            )
            self._error_thread = threading.Thread(
                target=self._capture_output,
                args=(self._process.stderr, self._handle_error)
            )
            
            self._output_thread.daemon = True
            self._error_thread.daemon = True
            self._output_thread.start()
            self._error_thread.start()
            
            # 启动监控
            self._monitor_timer.start()
            
            self._set_status("running")
            self.process_started.emit(self._pid)
            
            return True
            
        except Exception as e:
            self._set_status("stopped")
            self.process_error.emit(f"启动进程失败: {str(e)}")
            return False
            
    def stop_process(self, force: bool = False) -> bool:
        """停止进程"""
        if self._status != "running" or not self._process:
            return False
            
        try:
            self._set_status("stopping")
            self._stop_threads = True
            
            if force or os.name == 'nt':
                # 强制终止
                if os.name == 'nt':
                    self._process.terminate()
                else:
                    os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
            else:
                # 优雅终止
                os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                
                # 等待进程结束
                try:
                    self._process.wait(timeout=PROCESS_TIMEOUT)
                except subprocess.TimeoutExpired:
                    # 超时后强制终止
                    os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
                    
            # 获取退出码
            exit_code = self._process.returncode
            
            # 停止监控
            self._monitor_timer.stop()
            
            # 清理
            self._process = None
            self._pid = None
            self._stop_time = datetime.now()
            
            self._set_status("stopped")
            self.process_stopped.emit(self._pid or 0, exit_code or 0)
            
            return True
            
        except Exception as e:
            self.process_error.emit(f"停止进程失败: {str(e)}")
            return False
            
    def restart_process(self) -> bool:
        """重启进程"""
        if self._status == "running":
            if not self.stop_process():
                return False
                
            # 等待进程完全停止
            import time
            time.sleep(1)
            
        return self.start_process()
        
    def send_input(self, text: str) -> bool:
        """向进程发送输入"""
        if self._status != "running" or not self._process:
            return False
            
        try:
            self._process.stdin.write(text + '\n')
            self._process.stdin.flush()
            return True
        except Exception as e:
            self.process_error.emit(f"发送输入失败: {str(e)}")
            return False
            
    def get_status(self) -> Dict[str, any]:
        """获取进程状态"""
        status = {
            'status': self._status,
            'pid': self._pid,
            'command': self._command,
            'working_dir': self._working_dir,
            'start_time': self._start_time,
            'stop_time': self._stop_time,
            'running_time': None,
            'cpu_usage': self._cpu_usage,
            'memory_usage': self._memory_usage
        }
        
        if self._start_time and self._status == "running":
            status['running_time'] = (datetime.now() - self._start_time).total_seconds()
            
        return status
        
    def is_running(self) -> bool:
        """检查进程是否在运行"""
        return self._status == "running" and self._process is not None
        
    def set_output_callback(self, callback: Callable[[str], None]):
        """设置输出回调函数"""
        self._output_callback = callback
        
    def set_error_callback(self, callback: Callable[[str], None]):
        """设置错误回调函数"""
        self._error_callback = callback
        
    def _capture_output(self, stream, handler):
        """捕获输出流"""
        try:
            for line in iter(stream.readline, ''):
                if self._stop_threads:
                    break
                if line:
                    handler(line.rstrip())
        except Exception as e:
            if not self._stop_threads:
                self.process_error.emit(f"读取输出失败: {str(e)}")
        finally:
            stream.close()
            
    def _handle_output(self, line: str):
        """处理标准输出"""
        self.process_output.emit(line)
        if self._output_callback:
            self._output_callback(line)
            
    def _handle_error(self, line: str):
        """处理错误输出"""
        self.process_error.emit(line)
        if self._error_callback:
            self._error_callback(line)
            
    def _monitor_process(self):
        """监控进程状态"""
        if not self._process or self._status != "running":
            return
            
        # 检查进程是否仍在运行
        poll_result = self._process.poll()
        if poll_result is not None:
            # 进程已结束
            self._monitor_timer.stop()
            self._stop_threads = True
            self._stop_time = datetime.now()
            self._set_status("stopped")
            self.process_stopped.emit(self._pid, poll_result)
            self._process = None
            self._pid = None
            return
            
        # 获取进程资源使用情况
        try:
            if self._pid:
                process = psutil.Process(self._pid)
                self._cpu_usage = process.cpu_percent(interval=0.1)
                self._memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    def _set_status(self, status: str):
        """设置状态"""
        if self._status != status:
            self._status = status
            self.status_changed.emit(status)
            
    def kill_all_processes(self, name_pattern: str) -> int:
        """终止所有匹配名称的进程"""
        killed_count = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # 检查进程名或命令行是否匹配
                    if (name_pattern in proc.info['name'] or 
                        any(name_pattern in arg for arg in proc.info.get('cmdline', []))):
                        proc.kill()
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
        except Exception as e:
            self.process_error.emit(f"终止进程失败: {str(e)}")
            
        return killed_count
        
    def get_process_list(self, name_pattern: Optional[str] = None) -> List[Dict[str, any]]:
        """获取进程列表"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
                try:
                    # 如果指定了名称模式，进行过滤
                    if name_pattern:
                        if not (name_pattern in proc.info['name'] or 
                               any(name_pattern in arg for arg in proc.info.get('cmdline', []))):
                            continue
                            
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': ' '.join(proc.info.get('cmdline', [])),
                        'cpu_percent': proc.info.get('cpu_percent', 0),
                        'memory_mb': proc.info.get('memory_info', psutil._common.pmem(0, 0)).rss / 1024 / 1024
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
        except Exception as e:
            self.process_error.emit(f"获取进程列表失败: {str(e)}")
            
        return processes