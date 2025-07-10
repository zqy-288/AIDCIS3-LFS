#!/usr/bin/env python3
"""
搜索UI修复调试脚本
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def debug_search_ui_fix():
    """调试搜索UI修复"""
    print("🔍 搜索UI修复调试")
    print("=" * 60)
    
    try:
        from main_window import MainWindow
        import inspect
        
        print("📋 **修复验证**")
        print("=" * 60)
        
        # 1. 验证变量引用修复
        search_source = inspect.getsource(MainWindow.perform_search)
        
        if "self.selected_hole.hole_id in [\"H00001\", \"H00002\"]" in search_source:
            print("✅ 1. 变量引用已修复 (self.selected_hole.hole_id)")
        else:
            print("❌ 1. 变量引用未修复")
            return False
        
        # 2. 验证UI更新增强
        ui_source = inspect.getsource(MainWindow.update_hole_info_display)
        
        checks = [
            ("repaint()", "强制重绘"),
            ("processEvents()", "事件处理"),
            ("🔄 开始UI更新", "详细日志"),
            ("设置ID标签", "标签设置日志"),
            ("✅ UI更新完成", "完成确认")
        ]
        
        for check, desc in checks:
            if check in ui_source:
                print(f"✅ 2. {desc}已添加")
            else:
                print(f"❌ 2. {desc}未添加")
                return False
        
        # 3. 验证搜索后刷新
        if "QApplication.processEvents()" in search_source:
            print("✅ 3. 搜索后UI强制刷新已添加")
        else:
            print("❌ 3. 搜索后UI强制刷新未添加")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        return False

def create_test_scenario():
    """创建测试场景"""
    print("\n🧪 **测试场景**")
    print("=" * 60)
    
    print("场景1: 搜索H00001")
    print("  预期: 左侧显示完整信息，按钮全部启用")
    print("  验证: ID='H00001', 位置='(X.X, Y.Y)', 状态='PENDING', 半径='X.XXXmm'")
    print()
    
    print("场景2: 搜索H00002")
    print("  预期: 左侧显示完整信息，按钮全部启用")
    print("  验证: ID='H00002', 位置='(X.X, Y.Y)', 状态='QUALIFIED', 半径='X.XXXmm'")
    print()
    
    print("场景3: 搜索其他孔位")
    print("  预期: 左侧显示基本信息，实时监控/历史数据按钮禁用")
    print("  验证: ID='H00XXX', 实时监控按钮灰色，历史数据按钮灰色")
    print()
    
    print("场景4: 清空搜索")
    print("  预期: 清除高亮，保持当前选中状态")
    print("  验证: 不出现错误，UI保持稳定")

def provide_debugging_steps():
    """提供调试步骤"""
    print("\n🔧 **调试步骤**")
    print("=" * 60)
    
    print("1. 启动程序并加载DXF:")
    print("   python main.py")
    print("   按 Ctrl+T 加载测试管板.dxf")
    print()
    
    print("2. 测试H00001搜索:")
    print("   - 在搜索框输入 'H00001'")
    print("   - 点击搜索按钮")
    print("   - 检查左侧四个标签是否显示具体值")
    print("   - 检查右侧日志输出")
    print()
    
    print("3. 观察日志输出:")
    print("   应该看到:")
    print("   🔄 开始UI更新...")
    print("   🔄 UI更新: 显示孔位 H00001 信息")
    print("   📝 设置ID标签: 'H00001'")
    print("   📝 设置位置标签: '(X.X, Y.Y)'")
    print("   📝 设置状态标签: 'PENDING' (颜色: gray)")
    print("   📝 设置半径标签: 'X.XXXmm'")
    print("   ✅ UI更新完成: H00001 - 所有标签已刷新")
    print("   🔄 搜索完成，UI已刷新: H00001")
    print()
    
    print("4. 如果标签仍然为空:")
    print("   - 检查控制台是否有错误信息")
    print("   - 验证selected_hole是否正确赋值")
    print("   - 检查标签对象是否存在")
    print("   - 尝试手动调用update_hole_info_display()")

def provide_troubleshooting():
    """提供故障排除指南"""
    print("\n🚨 **故障排除**")
    print("=" * 60)
    
    print("问题1: 标签显示为空")
    print("  可能原因:")
    print("  - selected_hole未正确赋值")
    print("  - UI标签对象不存在")
    print("  - Qt事件循环问题")
    print("  解决方案:")
    print("  - 检查日志中的'🔄 UI更新'信息")
    print("  - 验证标签setText()调用")
    print("  - 确保repaint()和processEvents()被调用")
    print()
    
    print("问题2: 按钮状态不正确")
    print("  可能原因:")
    print("  - 数据可用性检查逻辑错误")
    print("  - 按钮setEnabled()未生效")
    print("  解决方案:")
    print("  - 检查has_data变量值")
    print("  - 验证按钮对象存在")
    print("  - 检查工具提示是否更新")
    print()
    
    print("问题3: 搜索无响应")
    print("  可能原因:")
    print("  - hole_collection未加载")
    print("  - 搜索逻辑异常")
    print("  解决方案:")
    print("  - 确认DXF文件已加载")
    print("  - 检查搜索匹配逻辑")
    print("  - 验证图形视图方法调用")

def main():
    """主函数"""
    print("🔍 搜索UI修复 - 调试和验证")
    print("=" * 60)
    
    # 验证修复
    if debug_search_ui_fix():
        print("\n✅ 所有修复验证通过！")
        
        # 提供测试指导
        create_test_scenario()
        provide_debugging_steps()
        provide_troubleshooting()
        
        print("\n🎯 **关键修复点**")
        print("=" * 60)
        print("1. 🔧 修复变量引用错误 (hole → self.selected_hole)")
        print("2. 🖥️ 增强UI更新机制 (repaint + processEvents)")
        print("3. 📝 添加详细调试日志")
        print("4. 🔄 强制UI刷新时机")
        print("5. ⚡ 事件循环处理")
        
        print("\n💡 **测试建议**")
        print("=" * 60)
        print("1. 运行单元测试: python -m pytest tests/unit/test_ui_update_fix.py -v")
        print("2. 运行集成测试: python -m pytest tests/integration/test_search_ui_integration.py -v")
        print("3. 运行端到端测试: python -m pytest tests/system/test_search_ui_e2e.py -v")
        print("4. 手动测试: python main.py")
        
        return True
    else:
        print("\n❌ 修复验证失败！")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 搜索UI修复调试完成！")
        print("现在可以测试修复后的搜索功能。")
    else:
        print("\n💥 调试发现问题，请检查修复代码。")
