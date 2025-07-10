"""
数据工作线程模块
负责模拟硬件数据接收和跨线程安全传递
"""

import time
import random
import numpy as np
from PySide6.QtCore import QThread, Signal


class WorkerThread(QThread):
    """
    数据工作线程类
    继承自QThread，专门用于后台数据处理和信号发射
    """
    
    # 定义信号：传递测量数据 (深度, 直径值)
    data_updated = Signal(float, float)  # depth, diameter
    
    # 定义信号：传递状态信息
    status_updated = Signal(str, float, str)  # hole_id, probe_depth, comm_status
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.hole_id = "H001"
        self.probe_depth = 0.0
        self.comm_status = "连接正常"
        
        # 模拟参数
        self.target_diameter = 18.5  # 目标直径 18.5mm (17-20mm范围中值)
        self.tolerance = 0.5  # 公差 ±0.5mm
        self.noise_level = 0.05  # 噪声水平
        self.measurement_frequency = 50  # 测量频率 50Hz
        
    def start_measurement(self, hole_id="H001"):
        """开始测量指定孔"""
        self.hole_id = hole_id
        self.probe_depth = 0.0
        self.running = True
        self.start()
        
    def stop_measurement(self):
        """停止测量"""
        self.running = False
        self.wait()  # 等待线程结束
        
    def run(self):
        """线程主循环 - 模拟数据采集"""
        print(f"开始测量孔 {self.hole_id}")
        
        while self.running:
            try:
                # 模拟探头深度递增
                self.probe_depth += 1.0  # 每次深入1.0mm（适应更大深度范围）

                # 模拟直径测量值（带噪声）
                base_diameter = self.target_diameter

                # 添加深度相关的变化（模拟孔的不规则性）
                depth_variation = 0.1 * np.sin(self.probe_depth * 0.01)  # 调整频率适应更大深度

                # 添加随机噪声
                noise = random.gauss(0, self.noise_level)

                measured_diameter = base_diameter + depth_variation + noise

                # 发射数据信号
                self.data_updated.emit(self.probe_depth, measured_diameter)

                # 发射状态信号
                self.status_updated.emit(
                    self.hole_id,
                    self.probe_depth,
                    self.comm_status
                )

                # 控制测量频率
                time.sleep(1.0 / self.measurement_frequency)

                # 模拟测量完成条件（深度达到900mm）
                if self.probe_depth >= 900.0:
                    print(f"孔 {self.hole_id} 测量完成")
                    self.running = False
                    
            except Exception as e:
                print(f"数据采集错误: {e}")
                self.comm_status = "通信异常"
                time.sleep(0.1)
                
        print(f"孔 {self.hole_id} 测量线程结束")


class DataSimulator:
    """
    数据模拟器 - 用于测试和演示
    可以生成不同类型的测量数据模式
    """
    
    @staticmethod
    def generate_normal_data(depth, target_diameter=18.5, noise=0.05):
        """生成正常范围内的数据"""
        variation = 0.1 * np.sin(depth * 0.01)  # 调整频率适应更大深度
        noise_val = random.gauss(0, noise)
        return target_diameter + variation + noise_val

    @staticmethod
    def generate_defective_data(depth, target_diameter=18.5):
        """生成包含缺陷的数据"""
        if 200 <= depth <= 250:  # 在200-250mm深度模拟缺陷
            return target_diameter - 0.6  # 直径偏小
        elif 500 <= depth <= 550:  # 在500-550mm深度模拟另一个缺陷
            return target_diameter + 0.7  # 直径偏大
        elif 750 <= depth <= 800:  # 在750-800mm深度模拟第三个缺陷
            return target_diameter - 0.8  # 直径偏小
        else:
            return DataSimulator.generate_normal_data(depth, target_diameter)

    @staticmethod
    def generate_trend_data(depth, target_diameter=18.5):
        """生成有趋势变化的数据"""
        trend = 0.0005 * depth  # 随深度线性增加，调整斜率
        noise = random.gauss(0, 0.05)
        return target_diameter + trend + noise


if __name__ == "__main__":
    """测试代码"""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    def on_data_received(depth, diameter):
        print(f"深度: {depth:.1f}mm, 直径: {diameter:.3f}mm")
    
    def on_status_received(hole_id, probe_depth, comm_status):
        print(f"状态 - 孔ID: {hole_id}, 探头深度: {probe_depth:.1f}mm, 通信: {comm_status}")
    
    # 创建工作线程
    worker = WorkerThread()
    worker.data_updated.connect(on_data_received)
    worker.status_updated.connect(on_status_received)
    
    # 开始测量
    worker.start_measurement("TEST_H001")
    
    # 运行5秒后停止
    QTimer = app.timer()
    QTimer.singleShot(5000, worker.stop_measurement)
    
    sys.exit(app.exec())
