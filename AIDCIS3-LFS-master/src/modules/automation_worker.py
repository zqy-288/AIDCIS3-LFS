#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化工作器模块 - 完全按照原项目还原
负责管理自动化流程，包括本地数据采集程序和远程运动台控制脚本的启动和管理

原项目特征：
- 隐藏窗口启动程序
- 缩短延迟时间
- 完善的进程管理
- 信号驱动的状态通信
"""

from PySide6.QtCore import QObject, Signal
import subprocess
import sys
import os
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutomationWorker(QObject):
    """
    自动化工作器类 - 完全按照原项目还原
    
    功能：
    1. 管理本地数据采集程序的启动和停止
    2. 管理远程运动台控制脚本的执行
    3. 提供进度反馈和状态通信
    4. 处理异常情况和错误恢复
    
    设计原则：
    - 高内聚：所有自动化相关功能集中管理
    - 低耦合：通过信号与UI解耦，不直接操作UI组件
    - 异步执行：在后台线程中运行，不阻塞UI
    """
    
    # 信号定义 - 完全按照原项目
    progress_updated = Signal(str)  # 进度更新信号
    task_finished = Signal(bool, str)  # 任务完成信号 (成功标志, 消息)

    def __init__(self, acquisition_path, launcher_path):
        """
        初始化自动化工作器
        
        Args:
            acquisition_path (str): 本地数据采集程序路径
            launcher_path (str): 远程运动台控制脚本路径
        """
        super().__init__()
        
        # 路径配置
        self.acquisition_exe_path = acquisition_path
        self.launcher_path = launcher_path
        self.acquisition_process_name = os.path.basename(acquisition_path)
        
        # 进程管理
        self.launcher_process = None
        self._is_running = True
        
        logger.info(f"自动化工作器初始化完成")
        logger.info(f"采集程序路径: {self.acquisition_exe_path}")
        logger.info(f"控制脚本路径: {self.launcher_path}")

    def stop(self):
        """
        停止自动化流程 - 完全按照原项目实现
        通过任务管理器按名称终止所有相关进程
        """
        try:
            self.progress_updated.emit("🛑 收到外部停止请求...")
            self._is_running = False
            
            # 终止远程控制脚本
            if self.launcher_process and self.launcher_process.poll() is None:
                self.progress_updated.emit("   - 正在终止远程控制脚本...")
                self.launcher_process.terminate()
                try:
                    self.launcher_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.launcher_process.kill()
                self.progress_updated.emit("   - 远程控制脚本已终止。")

            # 终止本地采集程序
            # 即使程序在后台运行，我们依然可以通过taskkill按名称精确终止它
            self.progress_updated.emit(f"   - 正在通过任务管理器终止 '{self.acquisition_process_name}'...")
            subprocess.run(['taskkill', '/F', '/IM', self.acquisition_process_name],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.progress_updated.emit(f"   - '{self.acquisition_process_name}' 的停止命令已发送。")
            
            self.progress_updated.emit("所有进程已尝试终止。")
            logger.info("自动化流程停止完成")
            
        except Exception as e:
            error_msg = f"停止自动化流程时发生错误: {e}"
            self.progress_updated.emit(f"❌ {error_msg}")
            logger.error(error_msg)

    def run_automation(self):
        """
        执行自动化流程 - 完全按照原项目实现
        
        流程：
        1. 在后台启动本地数据采集服务
        2. 启动远程运动台控制脚本
        3. 监控执行状态并提供反馈
        """
        try:
            self.progress_updated.emit("▶️ 自动化流程启动...")
            self._is_running = True
            logger.info("开始执行自动化流程")

            # --- 步骤1: 在后台启动本地采集程序 ---
            self.progress_updated.emit("\n--- 步骤 1/2: 正在后台启动本地数据采集服务 ---")
            
            if not os.path.exists(self.acquisition_exe_path):
                raise FileNotFoundError(f"采集程序不存在: {self.acquisition_exe_path}")

            acq_dir = os.path.dirname(self.acquisition_exe_path)
            
            # --- 核心特征：使用 CREATE_NO_WINDOW 标志来隐藏窗口 ---
            # CREATE_NO_WINDOW 是一个Windows特定的标志，值为 0x08000000
            DETACHED_PROCESS = 0x00000008
            CREATE_NO_WINDOW = 0x08000000
            
            self.progress_updated.emit(f"在后台启动程序: {self.acquisition_exe_path}")
            # 直接启动exe，并设置正确的工作目录(cwd)和隐藏窗口的标志
            subprocess.Popen(
                [self.acquisition_exe_path],
                cwd=acq_dir,
                creationflags=CREATE_NO_WINDOW
            )

            self.progress_updated.emit("✅ 启动命令已发送。")
            
            # --- 核心特征：缩短初始化等待时间 ---
            wait_seconds = 5
            self.progress_updated.emit(f"⏳ 等待采集服务初始化 ({wait_seconds}秒)...")
            time.sleep(wait_seconds)

            if not self._is_running: 
                self.task_finished.emit(False, "流程被用户提前终止。")
                return
            
            # 检查进程是否仍在运行
            result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {self.acquisition_process_name}'],
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if self.acquisition_process_name not in result.stdout:
                raise RuntimeError("自动化流程因错误中断: 本地采集程序启动后未能保持运行。\n请确认上位机软件是否已'以管理员身份运行'。")
            
            self.progress_updated.emit("✅ 采集服务初始化完成，进程正在后台运行。")

            # --- 步骤2: 启动远程运动台控制脚本 ---
            self.progress_updated.emit("\n--- 步骤 2/2: 正在启动远程运动台控制脚本 ---")
            if not os.path.exists(self.launcher_path):
                raise FileNotFoundError(f"远程控制脚本不存在: {self.launcher_path}")
            
            self.progress_updated.emit(f"执行脚本: {self.launcher_path}")
            self.launcher_process = subprocess.Popen(
                [sys.executable, self.launcher_path],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding='utf-8', errors='replace', creationflags=CREATE_NO_WINDOW
            )
            
            # 实时监控脚本输出
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
            logger.info("自动化流程执行完成")

        except Exception as e:
            import traceback
            error_info = f"{str(e)}\n\n详细信息:\n{traceback.format_exc()}"
            error_msg = f"❌ 自动化流程因错误中断: {error_info}"
            self.task_finished.emit(False, error_msg)
            logger.error(f"自动化流程执行失败: {e}")
            logger.debug(traceback.format_exc())
        finally:
            self.stop()

    def is_running(self):
        """
        检查自动化流程是否正在运行
        
        Returns:
            bool: 运行状态
        """
        return self._is_running

    def get_status(self):
        """
        获取当前状态信息
        
        Returns:
            dict: 状态信息字典
        """
        return {
            'is_running': self._is_running,
            'acquisition_path': self.acquisition_exe_path,
            'launcher_path': self.launcher_path,
            'acquisition_process_name': self.acquisition_process_name,
            'launcher_process_active': self.launcher_process and self.launcher_process.poll() is None
        }
