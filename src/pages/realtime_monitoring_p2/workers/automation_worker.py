# automation_worker.py (实时数据捕获版 - 双线程处理)
from PySide6.QtCore import QObject, Signal, QThread, QTimer
import subprocess
import sys
import os
import time
import re
import threading
from collections import deque

class AutomationWorker(QObject):
    progress_updated = Signal(str)
    task_finished = Signal(bool, str)
    # 新增：实时数据信号
    realtime_data_received = Signal(float, float)  # depth, diameter
    
    def __init__(self, acquisition_path, launcher_path):
        super().__init__()
        self.acquisition_exe_path = acquisition_path
        self.launcher_path = launcher_path
        self.acquisition_process_name = os.path.basename(acquisition_path)
        self.launcher_process = None
        self.acquisition_process = None
        self._is_running = True
        
        # 实时数据处理相关
        self.data_buffer = deque()  # 数据缓冲区（无限制）
        self.last_sequence = 0  # 记录最后处理的序号
        self.data_patterns = self._init_data_patterns()

        # 线程控制
        self.realtime_thread = None
        self.csv_monitor_thread = None

    def _init_data_patterns(self):
        """初始化数据解析正则表达式"""
        return [
            # 主要格式：序号3296，直径17.7418 (精确匹配)
            re.compile(r'^序号(\d+)[，,]直径(\d+\.\d+)$', re.IGNORECASE),
            # 变体格式：序号: 3296, 直径: 17.7418
            re.compile(r'^序号[：:]\s*(\d+)\s*[，,]\s*直径[：:]\s*(\d+\.\d+)$', re.IGNORECASE),
            # 英文格式：No: 3296, Diameter: 17.7418
            re.compile(r'^No[：:]\s*(\d+)\s*[，,]\s*Diameter[：:]\s*(\d+\.\d+)$', re.IGNORECASE),
        ]
    
    def parse_realtime_data(self, line):
        """解析实时数据行"""
        if not line or not line.strip():
            return None, None
            
        line = line.strip()
        
        for pattern in self.data_patterns:
            match = pattern.search(line)
            if match:
                try:
                    sequence = int(match.group(1))
                    diameter = float(match.group(2))

                    # 将序号转换为深度（每个序号对应0.1mm深度）
                    depth = sequence * 0.1

                    return depth, diameter
                except (ValueError, IndexError):
                    continue
        
        return None, None

    def realtime_data_monitor(self):
        """实时数据监控线程函数"""
        try:
            self.progress_updated.emit("🔄 开始实时数据监控...")

            # 添加计数器用于调试
            total_lines = 0
            empty_lines = 0

            while self._is_running and self.acquisition_process and self.acquisition_process.poll() is None:
                try:
                    # 使用readline读取一行输出
                    line = self.acquisition_process.stdout.readline()

                    if not line:
                        # 如果没有数据，短暂等待
                        time.sleep(0.01)  # 10ms等待
                        continue

                    total_lines += 1
                    line = line.strip()

                    if not line:
                        empty_lines += 1
                        continue

                    # 每100行输出一次统计信息
                    if total_lines % 100 == 0:
                        self.progress_updated.emit(f"📊 数据统计: 总行数{total_lines}, 空行{empty_lines}, 有效行{total_lines-empty_lines}")
                    
                    # 输出原始行用于调试（前10行和每100行输出一次）
                    if not hasattr(self, '_debug_line_count'):
                        self._debug_line_count = 0
                    self._debug_line_count += 1

                    # 前10行都输出，便于调试
                    if self._debug_line_count <= 10:
                        self.progress_updated.emit(f"🔍 第{self._debug_line_count}行原始输出: '{line}'")
                    elif self._debug_line_count % 100 == 0:
                        self.progress_updated.emit(f"🔍 第{self._debug_line_count}行: {line[:50]}...")

                    # 解析数据
                    depth, diameter = self.parse_realtime_data(line)
                    if depth is not None and diameter is not None:
                        # 第一次解析成功时的提示
                        if not hasattr(self, '_first_parse_success'):
                            self._first_parse_success = True
                            self.progress_updated.emit(f"🎉 首次解析成功! 原始行: '{line}'")
                            self.progress_updated.emit(f"🎉 解析结果: 序号{int(depth)}, 直径{diameter:.4f}mm")

                        # 暂时禁用去重逻辑，确保所有数据都能发送
                        sequence = int(depth / 0.1)  # 将深度转换回序号

                        # 缓存数据
                        self.data_buffer.append((depth, diameter))

                        # 立即发送到UI进行绘制
                        self.realtime_data_received.emit(depth, diameter)

                        # 前10个数据点输出发送确认
                        if not hasattr(self, '_emit_count'):
                            self._emit_count = 0
                        self._emit_count += 1

                        if self._emit_count <= 10:
                            self.progress_updated.emit(f"📡 发送第{self._emit_count}个数据到UI: 序号{sequence}, 深度{depth:.1f}mm, 直径{diameter:.4f}mm")

                        # 每50个数据点输出一次进度
                        if sequence % 50 == 0:
                            self.progress_updated.emit(f"📊 实时数据: 序号{sequence}, 深度{depth:.1f}mm, 直径{diameter:.4f}mm")

                        # 更新最后序号（用于统计）
                        self.last_sequence = max(self.last_sequence, sequence)
                    else:
                        # 解析失败的行，前20行输出用于调试
                        if self._debug_line_count <= 20:
                            self.progress_updated.emit(f"⚠️ 第{self._debug_line_count}行解析失败: '{line}'")
                    
                except Exception as e:
                    if self._is_running:  # 只在运行时报告错误
                        self.progress_updated.emit(f"⚠️ 数据解析错误: {e}")
                    time.sleep(0.01)
                    
        except Exception as e:
            if self._is_running:
                self.progress_updated.emit(f"❌ 实时数据监控异常: {e}")
        finally:
            self.progress_updated.emit("🔄 实时数据监控已停止")

    def stop(self):
        """停止所有进程和线程"""
        self.progress_updated.emit("🛑 收到外部停止请求...")
        self._is_running = False
        
        # 终止采集程序进程
        if self.acquisition_process and self.acquisition_process.poll() is None:
            self.progress_updated.emit("   - 正在终止采集程序...")
            self.acquisition_process.terminate()
            try:
                self.acquisition_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.acquisition_process.kill()
            self.progress_updated.emit("   - 采集程序已终止。")
        
        # 终止远程控制脚本
        if self.launcher_process and self.launcher_process.poll() is None:
            self.progress_updated.emit("   - 正在终止远程控制脚本...")
            self.launcher_process.terminate()
            try:
                self.launcher_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.launcher_process.kill()
            self.progress_updated.emit("   - 远程控制脚本已终止。")

        # 通过任务管理器确保进程终止
        self.progress_updated.emit(f"   - 通过任务管理器终止 '{self.acquisition_process_name}'...")
        subprocess.run(['taskkill', '/F', '/IM', self.acquisition_process_name],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.progress_updated.emit("所有进程已尝试终止。")

    def run_automation(self):
        try:
            self.progress_updated.emit("▶️ 自动化流程启动...")
            self._is_running = True

            # --- 步骤1: 启动采集程序并捕获实时输出 ---
            self.progress_updated.emit("\n--- 步骤 1/3: 启动采集程序并捕获实时输出 ---")
            
            if not os.path.exists(self.acquisition_exe_path):
                raise FileNotFoundError(f"采集程序不存在: {self.acquisition_exe_path}")

            acq_dir = os.path.dirname(self.acquisition_exe_path)
            
            self.progress_updated.emit(f"启动采集程序: {self.acquisition_exe_path}")

            # 启动采集程序并捕获标准输出
            # 尝试多种编码方式以解决乱码问题
            try:
                self.acquisition_process = subprocess.Popen(
                    [self.acquisition_exe_path],
                    cwd=acq_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='gbk',  # 中文Windows系统常用编码
                    errors='replace',
                    bufsize=0,  # 无缓冲，立即输出
                    universal_newlines=True
                )
                self.progress_updated.emit("✅ 使用GBK编码启动采集程序")
            except Exception as e:
                self.progress_updated.emit(f"⚠️ GBK编码失败，尝试UTF-8: {e}")
                self.acquisition_process = subprocess.Popen(
                    [self.acquisition_exe_path],
                    cwd=acq_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=0,  # 无缓冲，立即输出
                    universal_newlines=True
                )

            self.progress_updated.emit("✅ 采集程序已启动，开始捕获实时输出")
            
            # 等待程序初始化
            time.sleep(2)
            
            if not self._is_running: 
                self.task_finished.emit(False, "流程被用户提前终止。")
                return
            
            # 检查进程是否正常运行
            if self.acquisition_process.poll() is not None:
                raise RuntimeError("采集程序启动后立即退出，请检查程序是否正常")
            
            # --- 步骤2: 启动实时数据监控线程 ---
            self.progress_updated.emit("\n--- 步骤 2/3: 启动实时数据监控线程 ---")
            self.realtime_thread = threading.Thread(target=self.realtime_data_monitor, daemon=True)
            self.realtime_thread.start()
            self.progress_updated.emit("✅ 实时数据监控线程已启动")

            # --- 步骤3: 启动远程运动台控制脚本 ---
            self.progress_updated.emit("\n--- 步骤 3/3: 启动远程运动台控制脚本 ---")
            if not os.path.exists(self.launcher_path):
                raise FileNotFoundError(f"远程控制脚本不存在: {self.launcher_path}")
            
            self.progress_updated.emit(f"执行脚本: {self.launcher_path}")
            self.launcher_process = subprocess.Popen(
                [sys.executable, self.launcher_path],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding='gbk', errors='replace'  # 使用GBK编码，与LEConfocalDemo保持一致
            )
            
            # 监控控制脚本输出
            while self._is_running:
                output = self.launcher_process.stdout.readline()
                if output == '' and self.launcher_process.poll() is not None: 
                    break
                if output: 
                    self.progress_updated.emit(f"[控制脚本]: {output.strip()}")

            if not self._is_running: 
                self.task_finished.emit(False, "流程被用户提前终止。")
                return
            
            return_code = self.launcher_process.wait()
            self.progress_updated.emit(f"\n✅ 远程控制脚本执行完毕，返回码: {return_code}")
            
            self.task_finished.emit(True, "✅ 自动化流程正常结束。")

        except Exception as e:
            import traceback
            error_info = f"{str(e)}\n\n详细信息:\n{traceback.format_exc()}"
            self.task_finished.emit(False, f"❌ 自动化流程因错误中断: {error_info}")
        finally:
            self.stop()
