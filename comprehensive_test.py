#!/usr/bin/env python3
"""
综合测试 - 验证所有修复的功能
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_imports():
    """测试所有必要的导入"""
    print("\n1. 测试导入...")
    try:
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        print("✅ NativeMainDetectionView 导入成功")
        
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        print("✅ SimulationController 导入成功")
        
        from src.pages.main_detection_p1.components.graphics.panorama_view import PanoramaWidget
        print("✅ PanoramaWidget 导入成功")
        
        from src.pages.main_detection_p1.components.panorama_sector_coordinator import PanoramaSectorCoordinator
        print("✅ PanoramaSectorCoordinator 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_table_widget():
    """测试表格组件"""
    print("\n2. 测试扇形统计表格...")
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeLeftInfoPanel
        panel = NativeLeftInfoPanel()
        
        # 检查表格是否存在
        if hasattr(panel, 'sector_stats_table'):
            print("✅ 扇形统计表格存在")
            
            # 检查表格配置
            table = panel.sector_stats_table
            if table.rowCount() == 6:
                print("✅ 表格有6行（正确）")
            else:
                print(f"❌ 表格行数不正确: {table.rowCount()}")
                
            if table.columnCount() == 2:
                print("✅ 表格有2列（正确）")
            else:
                print(f"❌ 表格列数不正确: {table.columnCount()}")
                
            return True
        else:
            print("❌ 扇形统计表格不存在")
            return False
            
    except Exception as e:
        print(f"❌ 表格测试失败: {e}")
        return False

def test_panorama_adaptive():
    """测试全景图自适应"""
    print("\n3. 测试全景图自适应设置...")
    try:
        # 读取文件内容
        file_path = Path("src/pages/main_detection_p1/native_main_detection_view_p1.py")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = {
            "setMaximumHeight": "self.sidebar_panorama.setMaximumHeight" not in content,
            "QSizePolicy.Expanding": "QSizePolicy.Expanding" in content,
            "setMinimumHeight": "self.sidebar_panorama.setMinimumHeight" in content,
            "stretch factor": "layout.addWidget(self.panorama_group, 1)" in content
        }
        
        all_passed = True
        for check, result in checks.items():
            if result:
                print(f"✅ {check} 检查通过")
            else:
                print(f"❌ {check} 检查失败")
                all_passed = False
                
        return all_passed
        
    except Exception as e:
        print(f"❌ 自适应测试失败: {e}")
        return False

def test_simulation_controller():
    """测试模拟控制器"""
    print("\n4. 测试模拟控制器...")
    try:
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance() or QApplication(sys.argv)
        controller = SimulationController()
        
        # 检查关键属性
        checks = {
            "定时器存在": hasattr(controller, 'simulation_timer'),
            "状态变化定时器": hasattr(controller, 'status_change_timer'),
            "检测时间设置": controller.pair_detection_time == 10000,
            "状态变化时间": controller.status_change_time == 9500
        }
        
        all_passed = True
        for check, result in checks.items():
            if result:
                print(f"✅ {check}")
            else:
                print(f"❌ {check}")
                all_passed = False
                
        return all_passed
        
    except Exception as e:
        print(f"❌ 模拟控制器测试失败: {e}")
        return False

def test_panorama_module():
    """测试全景图模块"""
    print("\n5. 测试全景图模块...")
    try:
        # 检查模块是否在正确位置
        module_path = Path("src/pages/main_detection_p1/components/graphics/panorama_view")
        if module_path.exists():
            print("✅ 全景图模块在正确位置")
            
            # 检查关键文件
            files = [
                "__init__.py",
                "components/panorama_widget.py",
                "adapters/legacy_adapter.py",
                "components/panorama_graphics_view.py"
            ]
            
            all_exist = True
            for file in files:
                file_path = module_path / file
                if file_path.exists():
                    print(f"✅ {file} 存在")
                else:
                    print(f"❌ {file} 不存在")
                    all_exist = False
                    
            return all_exist
        else:
            print("❌ 全景图模块不在正确位置")
            return False
            
    except Exception as e:
        print(f"❌ 全景图模块测试失败: {e}")
        return False

def test_update_hole_status_signature():
    """测试 update_hole_status 方法签名"""
    print("\n6. 测试 update_hole_status 方法签名...")
    try:
        # 检查 legacy_adapter.py
        adapter_path = Path("src/pages/main_detection_p1/components/graphics/panorama_view/adapters/legacy_adapter.py")
        with open(adapter_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "def update_hole_status(self, hole_id: str, status: HoleStatus, color_override=None)" in content:
                print("✅ legacy_adapter.py 方法签名正确")
            else:
                print("❌ legacy_adapter.py 方法签名不正确")
                return False
                
        # 检查 panorama_widget.py
        widget_path = Path("src/pages/main_detection_p1/components/graphics/panorama_view/components/panorama_widget.py")
        with open(widget_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "def update_hole_status(self, hole_id: str, status, color_override=None)" in content:
                print("✅ panorama_widget.py 方法签名正确")
            else:
                print("❌ panorama_widget.py 方法签名不正确")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ 方法签名测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("="*60)
    print("综合功能测试")
    print("="*60)
    
    tests = [
        ("导入测试", test_imports),
        ("表格组件测试", test_table_widget),
        ("全景图自适应测试", test_panorama_adaptive),
        ("模拟控制器测试", test_simulation_controller),
        ("全景图模块测试", test_panorama_module),
        ("方法签名测试", test_update_hole_status_signature)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 异常: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结:")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败")
    
    print("="*60)

if __name__ == "__main__":
    main()