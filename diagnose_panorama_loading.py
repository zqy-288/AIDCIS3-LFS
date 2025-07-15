#!/usr/bin/env python3
"""
诊断全景图加载问题
检查用户看到的"等待数据加载..."问题的根本原因
"""

import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import time

from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
from aidcis2.dxf_parser import DXFParser


def diagnose_panorama_loading():
    """诊断全景图加载问题"""
    print("🔍 诊断全景图加载问题")
    print("="*60)
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # 1. 创建全景图组件
    print("🖼️ 创建全景图组件...")
    panorama_widget = CompletePanoramaWidget()
    panorama_widget.show()
    
    # 2. 检查初始状态
    print(f"📊 初始状态检查:")
    print(f"   - info_label文本: '{panorama_widget.info_label.text()}'")
    print(f"   - 是否有panorama_view: {hasattr(panorama_widget, 'panorama_view')}")
    print(f"   - 是否有hole_collection: {hasattr(panorama_widget, 'hole_collection')}")
    
    if hasattr(panorama_widget, 'panorama_view'):
        view = panorama_widget.panorama_view
        print(f"   - 视图场景: {view.scene is not None}")
        if view.scene:
            print(f"   - 场景项数: {len(view.scene.items())}")
    
    # 3. 尝试加载数据
    print(f"\\n📂 尝试加载DXF数据...")
    dxf_path = "/Users/vsiyo/Desktop/AIDCIS/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
    
    try:
        parser = DXFParser()
        hole_collection = parser.parse_file(dxf_path)
        print(f"✅ DXF解析成功: {len(hole_collection)} 个孔位")
        
        # 4. 调用load_complete_view
        print(f"\\n🔄 调用load_complete_view...")
        panorama_widget.load_complete_view(hole_collection)
        
        # 5. 等待加载完成
        time.sleep(1.0)
        
        # 6. 检查加载后状态
        print(f"\\n📊 加载后状态检查:")
        print(f"   - info_label文本: '{panorama_widget.info_label.text()}'")
        print(f"   - 是否有hole_collection: {hasattr(panorama_widget, 'hole_collection')}")
        
        if hasattr(panorama_widget, 'hole_collection') and panorama_widget.hole_collection:
            print(f"   - hole_collection大小: {len(panorama_widget.hole_collection)}")
        
        if hasattr(panorama_widget, 'panorama_view'):
            view = panorama_widget.panorama_view
            print(f"   - 视图场景: {view.scene is not None}")
            if view.scene:
                print(f"   - 场景项数: {len(view.scene.items())}")
                print(f"   - 场景矩形: {view.scene.sceneRect()}")
        
        # 7. 分析问题
        print(f"\\n🔍 问题分析:")
        current_text = panorama_widget.info_label.text()
        
        if current_text == "等待数据加载...":
            print("❌ 问题确认: info_label仍显示'等待数据加载...'")
            print("🔧 可能原因:")
            print("   1. load_complete_view方法没有被正确调用")
            print("   2. 数据加载过程中发生错误")
            print("   3. info_label.setText()调用失败")
            print("   4. 有其他代码重置了info_label")
            
            # 手动尝试设置文本
            print("\\n🧪 手动测试info_label.setText()...")
            try:
                panorama_widget.info_label.setText("测试文本")
                print(f"   - 设置后文本: '{panorama_widget.info_label.text()}'")
                
                if panorama_widget.info_label.text() == "测试文本":
                    print("✅ info_label.setText()工作正常")
                else:
                    print("❌ info_label.setText()可能被其他代码覆盖")
                    
            except Exception as e:
                print(f"❌ info_label.setText()失败: {e}")
                
        elif "个孔位" in current_text:
            print(f"✅ 成功: info_label显示正确内容: '{current_text}'")
            print("🎉 全景图加载正常工作!")
            
        else:
            print(f"⚠️ 意外: info_label显示意外内容: '{current_text}'")
            
        # 8. 检查是否有定时器或其他异步更新
        print(f"\\n⏰ 检查定时器和异步更新...")
        
        # 等待更长时间看是否有延迟更新
        for i in range(3):
            time.sleep(1)
            current_text = panorama_widget.info_label.text()
            print(f"   - {i+1}秒后文本: '{current_text}'")
            
            if current_text != "等待数据加载..." and "个孔位" in current_text:
                print("✅ 延迟更新成功!")
                break
        else:
            print("❌ 没有延迟更新，问题仍然存在")
            
    except Exception as e:
        print(f"❌ DXF加载失败: {e}")
        import traceback
        traceback.print_exc()
        
    # 9. 综合结论
    print(f"\\n📋 诊断总结:")
    final_text = panorama_widget.info_label.text()
    
    if final_text == "等待数据加载...":
        print("🚨 问题确认: 全景图确实存在加载显示问题")
        print("🎯 建议解决方案:")
        print("   1. 检查load_complete_view方法中的错误处理")
        print("   2. 确保info_label.setText()在正确的线程中调用")
        print("   3. 检查是否有其他代码在重置info_label")
        print("   4. 添加更多调试信息到load_complete_view方法")
    else:
        print(f"✅ 问题可能已解决: 当前显示 '{final_text}'")
    
    # 保持窗口显示
    QTimer.singleShot(2000, app.quit)
    app.exec()


if __name__ == "__main__":
    diagnose_panorama_loading()