#!/usr/bin/env python3
"""
诊断定时器时序问题
"""

import sys
from pathlib import Path
import time
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, Signal

class TimingDiagnostic(QObject):
    """模拟定时器时序诊断"""
    
    def __init__(self):
        super().__init__()
        self.current_index = 0
        self.start_time = None
        
        # 主定时器 - 10秒
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.process_next)
        self.main_timer.setInterval(10000)
        
        # 状态定时器 - 9.5秒
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.finalize_status)
        self.status_timer.setSingleShot(True)
        
    def start(self):
        self.start_time = time.time()
        print(f"[{self.get_elapsed():.1f}s] 开始模拟")
        
        # 启动主定时器
        self.main_timer.start()
        
        # 立即处理第一个
        self.process_next()
        
    def get_elapsed(self):
        """获取经过时间"""
        return time.time() - self.start_time if self.start_time else 0
        
    def process_next(self):
        """处理下一个检测单元"""
        elapsed = self.get_elapsed()
        print(f"\n[{elapsed:.1f}s] === 主定时器触发 ===")
        print(f"[{elapsed:.1f}s] 当前 index = {self.current_index}")
        
        if self.current_index >= 5:  # 只测试5个单元
            print(f"[{elapsed:.1f}s] 模拟完成")
            self.main_timer.stop()
            QApplication.quit()
            return
            
        # 开始检测
        print(f"[{elapsed:.1f}s] 开始检测单元 #{self.current_index + 1} (设置为蓝色)")
        
        # 启动状态定时器
        self.status_timer.start(9500)
        print(f"[{elapsed:.1f}s] 启动9.5秒状态定时器")
        
        # 这里是问题所在 - index立即增加
        self.current_index += 1
        print(f"[{elapsed:.1f}s] index 增加到 {self.current_index}")
        
    def finalize_status(self):
        """完成状态更新"""
        elapsed = self.get_elapsed()
        print(f"\n[{elapsed:.1f}s] === 状态定时器触发 ===")
        # 注意：这里使用的是 current_index - 1，因为已经增加了
        unit_number = self.current_index  # 这实际上是下一个单元的编号！
        print(f"[{elapsed:.1f}s] 单元 #{unit_number} 变为绿色/红色")
        print(f"[{elapsed:.1f}s] 但实际应该是单元 #{unit_number}!")


def main():
    app = QApplication([])
    
    print("=== 定时器时序诊断 ===")
    print("预期时序：")
    print("0s: 开始#1(蓝) → 9.5s: #1变绿 → 10s: 开始#2(蓝) → 19.5s: #2变绿...")
    print("\n实际时序：")
    
    diagnostic = TimingDiagnostic()
    diagnostic.start()
    
    app.exec()
    
    print("\n=== 诊断结果 ===")
    print("问题：current_index 在开始检测时就增加了，导致：")
    print("1. 进度显示可能不准确")
    print("2. 状态更新时的单元编号可能混乱")
    print("3. 如果在9.5-10秒之间查询当前检测单元，会得到错误的结果")


if __name__ == "__main__":
    main()