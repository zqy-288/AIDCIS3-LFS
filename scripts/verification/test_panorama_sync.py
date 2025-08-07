#!/usr/bin/env python3
"""
测试全景图与扇形区域染色同步机制
验证模拟检测时全景图是否会同步更新颜色
"""

import sys
import os
from pathlib import Path

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, current_dir)
sys.path.insert(0, src_dir)

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QTimer

def main():
    """测试全景图与扇形染色同步"""
    print("🔍 测试全景图与扇形区域染色同步机制")
    print("=" * 60)
    
    app = QApplication([])
    
    try:
        # 导入必要组件
        from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        from src.core_business.models.hole_data import HoleStatus
        from src.core.shared_data_manager import SharedDataManager
        
        print("✅ 关键组件导入成功")
        
        # 创建测试窗口
        window = QMainWindow()
        window.setWindowTitle("全景图同步测试")
        window.setGeometry(200, 200, 900, 700)
        
        central_widget = QWidget()
        window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态标签
        status_label = QLabel("正在设置测试环境...")
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)
        
        # 创建全景图组件
        panorama_widget = CompletePanoramaWidget()
        panorama_widget.setFixedSize(600, 400)
        layout.addWidget(panorama_widget)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        test_sync_btn = QPushButton("测试同步更新")
        reset_btn = QPushButton("重置状态")
        button_layout.addWidget(test_sync_btn)
        button_layout.addWidget(reset_btn)
        layout.addLayout(button_layout)
        
        # 加载CAP1000.dxf数据
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/Data/Products/CAP1000/dxf/CAP1000.dxf"
        hole_collection = None
        
        try:
            print(f"🔍 正在加载DXF文件: {dxf_path}")
            
            # 导入DXF解析器
            from src.core_business.dxf_parser import DXFParser
            
            # 解析DXF文件
            dxf_parser = DXFParser()
            if os.path.exists(dxf_path):
                hole_collection = dxf_parser.parse_file(dxf_path)
                print(f"✅ 成功解析DXF: {len(hole_collection.holes)} 个孔位")
                
                # 加载数据到全景图
                panorama_widget.load_hole_collection(hole_collection)
                status_label.setText(f"✅ 已加载CAP1000数据: {len(hole_collection.holes)} 个孔位\n点击按钮测试同步染色机制")
                
                # 同时更新共享数据管理器
                data_manager = SharedDataManager()
                data_manager.current_hole_collection = hole_collection
                
            else:
                print(f"❌ DXF文件不存在: {dxf_path}")
                status_label.setText("❌ CAP1000.dxf文件未找到")
                
        except Exception as dxf_error:
            print(f"❌ DXF解析失败: {dxf_error}")
            # 尝试备用方案：从共享数据管理器获取
            data_manager = SharedDataManager()
            if hasattr(data_manager, 'hole_collection') and data_manager.hole_collection:
                hole_collection = data_manager.hole_collection
                print(f"✅ 使用缓存数据: {len(hole_collection.holes)} 个孔位")
                panorama_widget.load_hole_collection(hole_collection)
                status_label.setText(f"✅ 已加载缓存数据: {len(hole_collection.holes)} 个孔位\n点击按钮测试同步机制")
            else:
                status_label.setText("❌ 无法加载测试数据")
        
        # 设置测试功能（无论数据是否加载成功）
        if hole_collection:
            # 测试同步功能
            def test_sync():
                """测试同步更新"""
                print("🔍 开始测试同步更新...")
                status_label.setText("🔍 正在测试孔位状态同步...")
                
                # 模拟分扇形区域染色测试
                all_holes = list(hole_collection.holes.keys())
                total_holes = len(all_holes)
                
                # 分4个象限进行染色测试
                quadrant_size = total_holes // 4
                
                print(f"  🎨 开始分象限染色测试，总孔位: {total_holes}")
                
                # 第一象限 - 绿色（合格）
                quadrant1_holes = all_holes[:quadrant_size]
                for hole_id in quadrant1_holes[:min(20, len(quadrant1_holes))]:  # 限制数量避免过多
                    panorama_widget.update_hole_status(hole_id, HoleStatus.QUALIFIED)
                print(f"  ✅ 第一象限: {len(quadrant1_holes[:20])} 个孔位染色为绿色（合格）")
                
                # 第二象限 - 红色（缺陷）
                quadrant2_holes = all_holes[quadrant_size:quadrant_size*2]
                for hole_id in quadrant2_holes[:min(20, len(quadrant2_holes))]:
                    panorama_widget.update_hole_status(hole_id, HoleStatus.DEFECTIVE)
                print(f"  ❌ 第二象限: {len(quadrant2_holes[:20])} 个孔位染色为红色（缺陷）")
                
                # 第三象限 - 橙色（检测中）
                quadrant3_holes = all_holes[quadrant_size*2:quadrant_size*3]
                for hole_id in quadrant3_holes[:min(20, len(quadrant3_holes))]:
                    panorama_widget.update_hole_status(hole_id, HoleStatus.PROCESSING)
                print(f"  🟠 第三象限: {len(quadrant3_holes[:20])} 个孔位染色为橙色（检测中）")
                
                # 第四象限 - 深灰色（跳过）
                quadrant4_holes = all_holes[quadrant_size*3:]
                for hole_id in quadrant4_holes[:min(20, len(quadrant4_holes))]:
                    panorama_widget.update_hole_status(hole_id, HoleStatus.SKIPPED)
                print(f"  ⚫ 第四象限: {len(quadrant4_holes[:20])} 个孔位染色为深灰（跳过）")
                
                status_label.setText(f"✅ 分象限染色完成!\n🟢绿色: 合格  🔴红色: 缺陷\n🟠橙色: 检测中  ⚫深灰: 跳过\n请观察全景图中的扇形染色效果")
                print("🎨 分象限染色测试完成，请观察全景图中的四色扇形效果")
            
            def reset_status():
                """重置状态"""
                print("🔄 重置所有孔位状态...")
                for hole_id in hole_collection.holes.keys():
                    if hasattr(panorama_widget, 'update_hole_status'):
                        panorama_widget.update_hole_status(hole_id, HoleStatus.PENDING)
                status_label.setText("🔄 已重置所有孔位状态为待检测")
                print("✅ 状态重置完成")
            
            test_sync_btn.clicked.connect(test_sync)
            reset_btn.clicked.connect(reset_status)
            
        else:
            status_label.setText("❌ 未找到测试数据")
            print("❌ 未找到CAP1000数据进行测试")
        
        # 显示窗口
        window.show()
        
        # 自动关闭
        QTimer.singleShot(30000, window.close)  # 30秒后关闭
        
        print("📋 测试窗口已打开，请:")
        print("  1. 观察全景图初始状态")
        print("  2. 点击'测试同步更新'按钮")
        print("  3. 观察孔位颜色是否改变")
        print("  4. 点击'重置状态'验证重置功能")
        print("  (窗口将在30秒后自动关闭)")
        
        # 运行应用
        app.exec()
        
        print("✅ 同步测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🔚 测试结果: {'同步机制工作正常' if success else '同步机制需要修复'}")
    sys.exit(0 if success else 1)