#!/usr/bin/env python3
"""
诊断全景预览更新问题
检查为什么某些区域的孔位状态无法更新
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QHBoxLayout
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor

# 添加项目路径
sys.path.append('src')

from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from aidcis2.graphics.graphics_view import OptimizedGraphicsView
import random

class PanoramaUpdateTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("全景预览更新问题诊断")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建测试数据
        self.create_test_data()
        
        # 设置UI
        self.setup_ui()
        
        # 加载数据
        self.load_data()
        
    def create_test_data(self):
        """创建测试孔位数据 - 覆盖所有区域"""
        holes = {}
        
        # 创建分布在各个区域的孔位
        regions = [
            # 区域1：右上 (0°-90°)
            [(50, 50), (100, 30), (80, 80), (120, 60)],
            # 区域2：左上 (90°-180°)
            [(-50, 50), (-100, 30), (-80, 80), (-120, 60)],
            # 区域3：左下 (180°-270°)
            [(-50, -50), (-100, -30), (-80, -80), (-120, -60)],
            # 区域4：右下 (270°-360°)
            [(50, -50), (100, -30), (80, -80), (120, -60)]
        ]
        
        hole_id = 1
        for region_idx, positions in enumerate(regions):
            for x, y in positions:
                hole = HoleData(
                    hole_id=f"H{hole_id:04d}",
                    center_x=x,
                    center_y=y,
                    radius=5,  # 使用radius而不是diameter
                    status=HoleStatus.PENDING
                )
                holes[hole.hole_id] = hole
                hole_id += 1
        
        self.hole_collection = HoleCollection(holes=holes)
        self.test_holes = list(holes.keys())
        print(f"✅ 创建了 {len(self.test_holes)} 个测试孔位")
    
    def setup_ui(self):
        """设置测试界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # 左侧：全景预览
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.panorama = CompletePanoramaWidget()
        self.panorama.setFixedSize(400, 400)
        left_layout.addWidget(self.panorama)
        
        # 控制按钮
        btn_layout = QVBoxLayout()
        
        self.btn_single_update = QPushButton("测试单个更新")
        self.btn_single_update.clicked.connect(self.test_single_update)
        btn_layout.addWidget(self.btn_single_update)
        
        self.btn_batch_update = QPushButton("测试批量更新")
        self.btn_batch_update.clicked.connect(self.test_batch_update)
        btn_layout.addWidget(self.btn_batch_update)
        
        self.btn_region_update = QPushButton("测试区域更新")
        self.btn_region_update.clicked.connect(self.test_region_update)
        btn_layout.addWidget(self.btn_region_update)
        
        self.btn_check_items = QPushButton("检查hole_items")
        self.btn_check_items.clicked.connect(self.check_hole_items)
        btn_layout.addWidget(self.btn_check_items)
        
        self.btn_force_refresh = QPushButton("强制刷新视图")
        self.btn_force_refresh.clicked.connect(self.force_refresh)
        btn_layout.addWidget(self.btn_force_refresh)
        
        left_layout.addLayout(btn_layout)
        left_layout.addStretch()
        
        layout.addWidget(left_panel)
        
        # 右侧：日志输出
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        layout.addWidget(self.log_widget)
        
    def load_data(self):
        """加载数据到全景预览"""
        self.log("🔄 开始加载数据...")
        
        # 加载到全景预览
        self.panorama.load_complete_view(self.hole_collection)
        
        # 等待加载完成
        QTimer.singleShot(500, self.check_initial_state)
        
    def check_initial_state(self):
        """检查初始状态"""
        self.log("\n📊 检查初始状态:")
        
        # 检查全景视图
        if hasattr(self.panorama, 'panorama_view'):
            view = self.panorama.panorama_view
            self.log(f"✅ panorama_view 存在: {type(view)}")
            
            # 检查hole_items
            if hasattr(view, 'hole_items'):
                count = len(view.hole_items) if view.hole_items else 0
                self.log(f"✅ hole_items 存在: {count} 个项目")
                
                if count > 0:
                    # 显示前5个孔位ID
                    sample_ids = list(view.hole_items.keys())[:5]
                    self.log(f"   示例孔位: {sample_ids}")
                else:
                    self.log("❌ hole_items 为空!")
            else:
                self.log("❌ panorama_view 没有 hole_items 属性!")
                
            # 检查场景
            if hasattr(view, 'scene') and view.scene:
                items = view.scene.items()
                self.log(f"✅ 场景中有 {len(items)} 个图形项")
            else:
                self.log("❌ 没有场景或场景为空!")
        else:
            self.log("❌ panorama 没有 panorama_view 属性!")
            
    def test_single_update(self):
        """测试单个孔位更新"""
        self.log("\n🔧 测试单个更新:")
        
        # 随机选择一个孔位
        hole_id = random.choice(self.test_holes)
        status = random.choice([HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, HoleStatus.PROCESSING])
        
        self.log(f"更新孔位: {hole_id} -> {status.value}")
        
        # 直接调用更新方法
        self.panorama.update_hole_status(hole_id, status)
        
        # 检查缓存状态
        if hasattr(self.panorama, 'pending_status_updates'):
            pending_count = len(self.panorama.pending_status_updates)
            self.log(f"待更新缓存: {pending_count} 个项目")
            
        # 检查定时器状态
        if hasattr(self.panorama, 'batch_update_timer'):
            is_active = self.panorama.batch_update_timer.isActive()
            self.log(f"批量更新定时器: {'激活' if is_active else '未激活'}")
            if is_active:
                remaining = self.panorama.batch_update_timer.remainingTime()
                self.log(f"剩余时间: {remaining}ms")
                
    def test_batch_update(self):
        """测试批量更新"""
        self.log("\n🔧 测试批量更新:")
        
        # 创建批量更新
        updates = {}
        for i in range(8):  # 每个区域更新2个
            hole_id = self.test_holes[i]
            status = random.choice([HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE])
            updates[hole_id] = status
            
        self.log(f"批量更新 {len(updates)} 个孔位")
        
        # 使用批量更新方法
        self.panorama.batch_update_hole_status(updates)
        
    def test_region_update(self):
        """测试特定区域的更新"""
        self.log("\n🔧 测试区域更新:")
        
        # 更新每个区域的孔位
        for region in range(4):
            start_idx = region * 4
            end_idx = start_idx + 4
            
            self.log(f"\n更新区域 {region + 1}:")
            for i in range(start_idx, end_idx):
                if i < len(self.test_holes):
                    hole_id = self.test_holes[i]
                    status = HoleStatus.QUALIFIED if region % 2 == 0 else HoleStatus.DEFECTIVE
                    self.panorama.update_hole_status(hole_id, status)
                    self.log(f"  {hole_id} -> {status.value}")
                    
        # 等待批量更新触发
        QTimer.singleShot(1500, self.check_update_results)
        
    def check_update_results(self):
        """检查更新结果"""
        self.log("\n📊 检查更新结果:")
        
        if hasattr(self.panorama, 'panorama_view') and hasattr(self.panorama.panorama_view, 'hole_items'):
            hole_items = self.panorama.panorama_view.hole_items
            
            # 统计各状态的孔位数
            status_count = {}
            for hole_id, item in hole_items.items():
                if hasattr(item, 'brush'):
                    color = item.brush().color().name()
                    status_count[color] = status_count.get(color, 0) + 1
                    
            self.log("颜色分布:")
            for color, count in status_count.items():
                self.log(f"  {color}: {count} 个")
                
    def check_hole_items(self):
        """详细检查hole_items内容"""
        self.log("\n🔍 详细检查hole_items:")
        
        if hasattr(self.panorama, 'panorama_view'):
            view = self.panorama.panorama_view
            
            if hasattr(view, 'hole_items') and view.hole_items:
                self.log(f"hole_items 包含 {len(view.hole_items)} 个项目")
                
                # 检查前10个项目
                for i, (hole_id, item) in enumerate(view.hole_items.items()):
                    if i >= 10:
                        break
                        
                    self.log(f"\n孔位 {hole_id}:")
                    self.log(f"  类型: {type(item)}")
                    self.log(f"  位置: ({item.pos().x():.1f}, {item.pos().y():.1f})")
                    
                    if hasattr(item, 'brush'):
                        color = item.brush().color().name()
                        self.log(f"  颜色: {color}")
                        
                    if hasattr(item, 'isVisible'):
                        self.log(f"  可见: {item.isVisible()}")
                        
            else:
                self.log("❌ hole_items 不存在或为空!")
                
    def force_refresh(self):
        """强制刷新视图"""
        self.log("\n🔄 强制刷新视图...")
        
        if hasattr(self.panorama, 'panorama_view'):
            view = self.panorama.panorama_view
            
            # 强制刷新场景
            if hasattr(view, 'scene') and view.scene:
                view.scene.update()
                self.log("✅ 场景已更新")
                
            # 强制刷新视口
            view.viewport().update()
            view.update()
            self.log("✅ 视口已更新")
            
            # 强制重绘
            view.viewport().repaint()
            self.log("✅ 视口已重绘")
            
    def log(self, message):
        """输出日志"""
        self.log_widget.append(message)
        print(message)

def main():
    app = QApplication(sys.argv)
    window = PanoramaUpdateTester()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()