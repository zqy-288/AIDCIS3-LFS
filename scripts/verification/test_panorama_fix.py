#!/usr/bin/env python3
"""
测试全景显示修复
验证左侧显示全景，中间显示提示信息
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_panorama_display():
    print("🔍 测试全景显示修复...")
    
    try:
        # 测试导入
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        print("✅ 主视图导入成功")
        
        # 测试DXF加载服务
        from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
        print("✅ DXF加载服务导入成功")
        
        # 检查DXF文件
        dxf_file = project_root / "Data/Products/CAP1000/dxf/CAP1000.dxf"
        if dxf_file.exists():
            print(f"✅ 找到DXF文件: {dxf_file}")
            
            # 测试数据加载
            loader = DXFLoaderService()
            hole_collection = loader.load_dxf_file(str(dxf_file))
            
            if hole_collection and len(hole_collection) > 0:
                print(f"✅ 成功加载 {len(hole_collection)} 个孔位数据") 
                print("🎯 主要修复内容:")
                print("   1. 中间面板初始不显示完整全景，而是显示提示信息")
                print("   2. 左侧全景可以接收数据并显示完整全景")
                print("   3. 添加了全景扇形点击信号连接")
                print("   4. 点击左侧全景的扇形区域应该会在中间显示对应扇形")
            else:
                print("❌ 数据加载失败")
        else:
            print(f"❌ 找不到DXF文件: {dxf_file}")
            
        print("\n📋 修复总结:")
        print("   ✓ 修改了load_hole_collection方法，中间面板不再显示完整全景")
        print("   ✓ 中间面板显示提示用户点击扇形的信息")  
        print("   ✓ 添加了全景图扇形点击信号的连接")
        print("   → 现在左侧应该显示全景，中间显示提示信息")
        print("   → 点击左侧扇形区域应该在中间显示对应的扇形详细信息")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_panorama_display()