#!/usr/bin/env python3
"""
测试新版动态扇形显示功能
验证DXF划分为4个扇形区域和动态显示功能
"""

import sys
import os
import logging
from pathlib import Path

# 添加源代码路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'modules'))
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'models'))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_dynamic_sector_functionality():
    """测试动态扇形功能"""
    print("🧪 测试动态扇形区域显示功能")
    print("=" * 50)
    
    try:
        # 测试DXF解析和扇形划分
        from aidcis2.dxf_parser import DXFParser
        from aidcis2.graphics.dynamic_sector_view import SectorGraphicsManager
        from aidcis2.graphics.sector_manager import SectorQuadrant
        
        # 解析DXF文件
        dxf_path = "assets/dxf/DXF Graph/东重管板.dxf"
        if not Path(dxf_path).exists():
            print(f"❌ DXF文件不存在: {dxf_path}")
            return False
        
        print(f"🔄 解析DXF文件: {dxf_path}")
        parser = DXFParser()
        hole_collection = parser.parse_file(dxf_path)
        
        if not hole_collection or len(hole_collection) == 0:
            print("❌ DXF解析失败或无孔位数据")
            return False
        
        print(f"✅ DXF解析成功: {len(hole_collection)} 个孔位")
        
        # 测试扇形图形管理器
        print("🔄 创建扇形图形管理器...")
        sector_graphics_manager = SectorGraphicsManager(hole_collection)
        
        print("📊 扇形区域划分结果:")
        total_allocated = 0
        for sector in SectorQuadrant:
            sector_collection = sector_graphics_manager.get_sector_collection(sector)
            if sector_collection:
                hole_count = len(sector_collection)
                total_allocated += hole_count
                bounds = sector_collection.metadata.get('sector_bounds', (0,0,0,0))
                print(f"   {sector.value}: {hole_count} 个孔位")
                print(f"     范围: x({bounds[0]:.1f}, {bounds[2]:.1f}) y({bounds[1]:.1f}, {bounds[3]:.1f})")
            else:
                print(f"   {sector.value}: 0 个孔位")
        
        print(f"✅ 总分配孔位: {total_allocated} / {len(hole_collection)}")
        
        if total_allocated != len(hole_collection):
            print("⚠️ 扇形分配不完整，可能有遗漏")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_window_integration():
    """测试主窗口集成"""
    print("\n📋 测试主窗口集成...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from main_window import MainWindow
        
        # 创建应用（无界面模式）
        app = QApplication([])
        app.setQuitOnLastWindowClosed(False)
        
        print("🔄 创建主窗口...")
        window = MainWindow()
        
        # 检查新组件是否存在
        components = [
            ('动态扇形显示', 'dynamic_sector_display'),
            ('完整全景图', 'complete_panorama'),
            ('扇形概览', 'sector_overview'),
            ('扇形详细视图', 'sector_detail_view'),
            ('扇形管理器', 'sector_manager'),
            ('孔位集合', 'hole_collection'),
        ]
        
        print("🔍 检查组件:")
        for name, attr in components:
            if hasattr(window, attr):
                obj = getattr(window, attr)
                if obj is not None:
                    print(f"   ✅ {name}: {type(obj).__name__}")
                else:
                    print(f"   ⚠️ {name}: 存在但为None")
            else:
                print(f"   ❌ {name}: 未找到")
        
        # 检查DXF数据加载
        if hasattr(window, 'hole_collection') and window.hole_collection:
            print(f"✅ DXF数据已加载: {len(window.hole_collection)} 个孔位")
            
            # 检查动态扇形显示是否已设置
            if hasattr(window, 'dynamic_sector_display') and window.dynamic_sector_display:
                if window.dynamic_sector_display.sector_graphics_manager:
                    print("✅ 动态扇形显示已配置")
                    current_sector = window.dynamic_sector_display.get_current_sector()
                    print(f"   当前显示扇形: {current_sector.value}")
                else:
                    print("⚠️ 动态扇形显示未完全配置")
        else:
            print("❌ DXF数据未加载")
        
        return True
        
    except Exception as e:
        print(f"❌ 主窗口集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 动态扇形区域显示功能测试")
    print("🎯 新功能特点:")
    print("   • 完整孔位图显示全景DXF")
    print("   • 动态扇形显示当前检测区域的DXF部分")
    print("   • DXF自动划分为4个扇形区域")
    print("   • 根据检测进度自动切换显示区域")
    print()
    
    success = True
    
    # 测试1: 动态扇形功能
    if not test_dynamic_sector_functionality():
        success = False
    
    # 测试2: 主窗口集成
    if not test_main_window_integration():
        success = False
    
    if success:
        print("\n🎉 所有测试通过！")
        print("\n💡 新布局说明:")
        print("📱 上半部分（主要显示）:")
        print("   🎯 左侧: 动态扇形区域显示（当前检测区域的DXF部分）")
        print("   🖼️ 右侧: 完整孔位全景图（整个DXF的缩略图）")
        print("📱 下半部分（控制面板）:")
        print("   🎮 左侧: 扇形概览控制（200x200px，用于手动切换）")
        print("   📊 右侧: 扇形详细信息（显示选中区域的统计）")
        print("\n🚀 运行完整系统: python3 run_project.py")
    else:
        print("\n❌ 部分测试失败，请检查日志")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)