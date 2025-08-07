#!/usr/bin/env python3
"""
验证全景图恢复 - 静态检查
"""

import sys
from pathlib import Path


def verify_panorama_restoration():
    """验证全景图恢复的代码修改"""
    print("🔍 验证全景图恢复...\n")
    
    # 检查文件修改
    file_path = Path("src/pages/main_detection_p1/native_main_detection_view_p1.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # 1. 检查是否添加了全景预览组
    if "self.panorama_group = self._create_panorama_group(group_font)" in content:
        checks.append(("✅", "全景预览组添加到布局"))
    else:
        checks.append(("❌", "全景预览组未添加到布局"))
    
    # 2. 检查_create_panorama_group方法
    if "def _create_panorama_group(self, group_font):" in content:
        checks.append(("✅", "_create_panorama_group方法已定义"))
    else:
        checks.append(("❌", "_create_panorama_group方法未定义"))
    
    # 3. 检查CompletePanoramaWidget导入
    if "from src.core_business.graphics.complete_panorama_widget import CompletePanoramaWidget" in content:
        checks.append(("✅", "CompletePanoramaWidget导入正确"))
    else:
        checks.append(("❌", "CompletePanoramaWidget导入缺失"))
    
    # 4. 检查sidebar_panorama创建
    if "self.sidebar_panorama = CompletePanoramaWidget()" in content:
        checks.append(("✅", "sidebar_panorama组件创建"))
    else:
        checks.append(("❌", "sidebar_panorama组件未创建"))
    
    # 5. 检查协调器设置
    if "self.coordinator.set_panorama_widget(self.left_panel.sidebar_panorama)" in content:
        checks.append(("✅", "全景图已连接到协调器"))
    else:
        checks.append(("❌", "全景图未连接到协调器"))
    
    # 6. 检查模拟控制器设置
    if "self.simulation_controller.set_panorama_widget(self.left_panel.sidebar_panorama)" in content:
        checks.append(("✅", "全景图已连接到模拟控制器"))
    else:
        checks.append(("❌", "全景图未连接到模拟控制器"))
    
    # 7. 检查信号连接
    if "self.left_panel.sidebar_panorama.sector_clicked.connect(self._on_panorama_sector_clicked)" in content:
        checks.append(("✅", "扇形点击信号已连接"))
    else:
        checks.append(("❌", "扇形点击信号未连接"))
    
    # 打印结果
    print("📊 验证结果:")
    print("="*50)
    
    passed = 0
    for status, desc in checks:
        print(f"{status} {desc}")
        if status == "✅":
            passed += 1
    
    total = len(checks)
    print(f"\n总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n🎉 全景图预览已成功恢复到左侧面板！")
        return True
    else:
        print(f"\n⚠️ 有 {total - passed} 项需要修复")
        return False


if __name__ == "__main__":
    print("="*60)
    print("左侧全景图预览恢复验证")
    print("="*60)
    
    success = verify_panorama_restoration()
    sys.exit(0 if success else 1)