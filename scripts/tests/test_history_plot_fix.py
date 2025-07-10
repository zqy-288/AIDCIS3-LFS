#!/usr/bin/env python3
"""
测试历史查看器图表修复
"""

import sys
import os

def test_history_plot_initialization():
    """测试历史查看器图表初始化"""
    print("🔧 测试历史查看器图表修复")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        sys.path.append('.')
        from PySide6.QtWidgets import QApplication
        from modules.history_viewer import HistoryDataPlot
        
        # 创建应用程序
        app = QApplication([])
        
        print("📊 创建HistoryDataPlot实例...")
        plot_widget = HistoryDataPlot()
        
        # 检查ax1, ax2, ax3, ax4是否存在
        attributes_to_check = ['ax1', 'ax2', 'ax3', 'ax4']
        all_attributes_exist = True
        
        for attr in attributes_to_check:
            if hasattr(plot_widget, attr):
                print(f"  ✅ {attr}: 存在")
            else:
                print(f"  ❌ {attr}: 不存在")
                all_attributes_exist = False
        
        if all_attributes_exist:
            print("\n🎉 所有图表轴都已正确初始化!")
            
            # 测试init_empty_plots方法
            print("\n📈 测试init_empty_plots方法...")
            try:
                plot_widget.init_empty_plots()
                print("  ✅ init_empty_plots执行成功")
            except Exception as e:
                print(f"  ❌ init_empty_plots执行失败: {e}")
                all_attributes_exist = False
            
            # 测试plot_measurement_data方法
            print("\n📊 测试plot_measurement_data方法...")
            try:
                # 创建一些测试数据
                test_measurements = [
                    {
                        'position': 1.0,
                        'diameter': 17.6014,
                        'channel1': 1385.62,
                        'channel2': 2004.95,
                        'channel3': 1436.21,
                        'is_qualified': True,
                        'timestamp': '2025-07-09 10:00:00',
                        'operator': 'test'
                    }
                ]
                
                plot_widget.plot_measurement_data(test_measurements, {})
                print("  ✅ plot_measurement_data执行成功")
            except Exception as e:
                print(f"  ❌ plot_measurement_data执行失败: {e}")
                all_attributes_exist = False
        
        app.quit()
        return all_attributes_exist
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_history_viewer_creation():
    """测试完整的历史查看器创建"""
    print("\n" + "=" * 60)
    print("🖥️ 测试完整的历史查看器创建")
    print("=" * 60)
    
    try:
        from PySide6.QtWidgets import QApplication
        from modules.history_viewer import HistoryViewer
        
        # 创建应用程序
        app = QApplication([])
        
        print("📱 创建HistoryViewer实例...")
        viewer = HistoryViewer()
        
        # 检查plot_widget是否正确创建
        if hasattr(viewer, 'plot_widget'):
            print("  ✅ plot_widget: 存在")
            
            # 检查plot_widget的轴
            plot_widget = viewer.plot_widget
            axes_exist = all(hasattr(plot_widget, attr) for attr in ['ax1', 'ax2', 'ax3', 'ax4'])
            
            if axes_exist:
                print("  ✅ 所有图表轴: 存在")
                
                # 测试查询功能（模拟）
                print("\n🔍 测试CSV数据查询功能...")
                try:
                    # 模拟load_csv_data_for_hole方法
                    measurements = viewer.load_csv_data_for_hole('H00001')
                    if measurements:
                        print(f"  ✅ CSV数据加载: 成功 ({len(measurements)} 条数据)")
                        
                        # 测试图表更新
                        print("  📊 测试图表更新...")
                        viewer.plot_widget.plot_measurement_data(measurements, {})
                        print("  ✅ 图表更新: 成功")
                        
                    else:
                        print("  ⚠️ CSV数据加载: 无数据")
                        
                except Exception as e:
                    print(f"  ❌ CSV数据查询测试失败: {e}")
                    
            else:
                print("  ❌ 图表轴: 缺失")
                return False
        else:
            print("  ❌ plot_widget: 不存在")
            return False
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ 历史查看器创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始历史查看器图表修复测试")
    
    # 测试1: 图表初始化
    plot_test_success = test_history_plot_initialization()
    
    # 测试2: 完整查看器创建
    viewer_test_success = test_history_viewer_creation()
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 测试结果总结")
    print("=" * 60)
    print(f"📊 图表初始化: {'✅ 通过' if plot_test_success else '❌ 失败'}")
    print(f"🖥️ 查看器创建: {'✅ 通过' if viewer_test_success else '❌ 失败'}")
    
    overall_success = plot_test_success and viewer_test_success
    
    if overall_success:
        print("\n🎉 所有测试通过! 历史查看器图表问题已修复")
        print("💡 现在应该不会再出现 'HistoryDataPlot' object has no attribute 'ax1' 错误")
    else:
        print("\n⚠️ 仍有问题需要解决")
    
    sys.exit(0 if overall_success else 1)
