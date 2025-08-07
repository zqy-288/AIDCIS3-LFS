#!/usr/bin/env python3
"""
测试定时器覆盖问题
验证快速检测时是否会导致之前的蓝色状态未更新
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtWidgets import QApplication
import time

class TimerTest(QObject):
    """测试定时器覆盖问题"""
    
    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.on_timeout)
        self.pending_items = []
        self.current_item = None
        
    def start_item(self, item_id):
        """开始一个项目（模拟开始检测）"""
        print(f"\n[{time.strftime('%H:%M:%S')}] 开始项目 {item_id}")
        
        # 保存当前项目
        self.current_item = item_id
        self.pending_items.append(item_id)
        
        # 启动定时器 - 这会取消之前的定时器！
        print(f"[{time.strftime('%H:%M:%S')}] 启动定时器（2秒后触发）")
        self.timer.start(2000)  # 2秒后触发
        
    def on_timeout(self):
        """定时器触发"""
        print(f"\n[{time.strftime('%H:%M:%S')}] 定时器触发！")
        print(f"当前项目: {self.current_item}")
        print(f"待处理项目: {self.pending_items}")
        
        # 只处理当前项目
        if self.current_item and self.current_item in self.pending_items:
            self.pending_items.remove(self.current_item)
            print(f"✅ 处理项目 {self.current_item}")
        
        # 显示未处理的项目
        if self.pending_items:
            print(f"❌ 未处理的项目: {self.pending_items}")
            

def test_scenario_1():
    """场景1：快速启动多个项目"""
    print("=== 场景1：快速启动多个项目 ===")
    app = QApplication.instance() or QApplication(sys.argv)
    
    test = TimerTest()
    
    # 快速启动3个项目
    test.start_item("A")
    QTimer.singleShot(500, lambda: test.start_item("B"))    # 0.5秒后
    QTimer.singleShot(1000, lambda: test.start_item("C"))   # 1秒后
    
    # 3秒后检查结果
    def check_result():
        print(f"\n[{time.strftime('%H:%M:%S')}] === 最终检查 ===")
        print(f"未处理的项目: {test.pending_items}")
        print("预期：A和B未处理，只有C被处理")
        app.quit()
        
    QTimer.singleShot(3000, check_result)
    
    app.exec()


def test_scenario_2():
    """场景2：正确的实现方式 - 使用独立定时器"""
    print("\n\n=== 场景2：使用独立定时器 ===")
    
    class BetterTimerTest(QObject):
        def __init__(self):
            super().__init__()
            self.item_timers = {}  # 每个项目独立的定时器
            
        def start_item(self, item_id):
            print(f"\n[{time.strftime('%H:%M:%S')}] 开始项目 {item_id}")
            
            # 为每个项目创建独立的定时器
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.on_item_timeout(item_id))
            timer.start(2000)
            
            self.item_timers[item_id] = timer
            print(f"[{time.strftime('%H:%M:%S')}] 为项目 {item_id} 创建独立定时器")
            
        def on_item_timeout(self, item_id):
            print(f"\n[{time.strftime('%H:%M:%S')}] 项目 {item_id} 定时器触发")
            print(f"✅ 处理项目 {item_id}")
            
            # 清理定时器
            if item_id in self.item_timers:
                del self.item_timers[item_id]
    
    app = QApplication.instance() or QApplication(sys.argv)
    test = BetterTimerTest()
    
    # 快速启动3个项目
    test.start_item("A")
    QTimer.singleShot(500, lambda: test.start_item("B"))
    QTimer.singleShot(1000, lambda: test.start_item("C"))
    
    # 3秒后检查结果
    def check_result():
        print(f"\n[{time.strftime('%H:%M:%S')}] === 最终检查 ===")
        print("预期：A、B、C都被正确处理")
        app.quit()
        
    QTimer.singleShot(3000, check_result)
    
    app.exec()


if __name__ == '__main__':
    print("测试定时器覆盖问题\n")
    
    # 测试场景1：问题演示
    test_scenario_1()
    
    # 测试场景2：正确实现
    test_scenario_2()