#!/usr/bin/env python3
"""
测试颜色图例显示效果
验证视图模式按钮旁边的颜色图例是否正常显示
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import logging
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

def test_color_legend_widgets():
    """测试颜色图例组件"""
    try:
        from src.pages.main_detection_p1.components.color_legend_widget import (
            ColorLegendWidget, 
            CompactColorLegendWidget
        )
        
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = QMainWindow()
        window.setWindowTitle("颜色图例显示测试")
        window.resize(600, 300)
        
        # 中央组件 
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("颜色图例显示测试")
        title_font = QFont("Arial", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 测试标准图例（水平布局）
        section1_label = QLabel("1. 标准水平图例：")
        section1_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(section1_label)
        
        legend1 = ColorLegendWidget(layout_direction="horizontal")
        main_layout.addWidget(legend1)
        
        # 测试标准图例（垂直布局）
        section2_label = QLabel("2. 标准垂直图例：")
        section2_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(section2_label)
        
        legend2 = ColorLegendWidget(layout_direction="vertical")
        main_layout.addWidget(legend2)
        
        # 测试紧凑图例
        section3_label = QLabel("3. 紧凑图例（用于视图模式按钮旁）：")
        section3_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(section3_label)
        
        # 创建模拟视图模式按钮区域
        button_area = QWidget()
        button_layout = QHBoxLayout(button_area)
        
        from PySide6.QtWidgets import QPushButton
        macro_btn = QPushButton("📊 宏观区域视图")
        macro_btn.setMinimumHeight(35)
        macro_btn.setMinimumWidth(140)
        
        micro_btn = QPushButton("🔍 微观孔位视图")
        micro_btn.setMinimumHeight(35)
        micro_btn.setMinimumWidth(140)
        
        compact_legend = CompactColorLegendWidget()
        
        button_layout.addWidget(macro_btn)
        button_layout.addWidget(micro_btn)
        button_layout.addWidget(compact_legend)
        button_layout.addStretch()
        
        main_layout.addWidget(button_area)
        
        # 添加说明
        info_label = QLabel(
            "说明：图例显示孔位状态的颜色编码\n"
            "• 灰色 - 待检测\n"
            "• 蓝色 - 检测中\n" 
            "• 绿色 - 合格\n"
            "• 红色 - 异常\n"
            "• 黄色 - 盲孔（在完整图例中显示）"
        )
        info_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        main_layout.addWidget(info_label)
        
        main_layout.addStretch()
        
        window.setCentralWidget(central_widget)
        window.show()
        
        print("✅ 颜色图例测试窗口已启动")
        print("📊 请检查以下内容：")
        print("   1. 标准图例是否正确显示颜色和标签")
        print("   2. 紧凑图例是否适合放在按钮旁边")
        print("   3. 颜色是否与配置文件中的定义一致")
        print("   4. 鼠标悬停是否显示详细信息")
        
        return app.exec()
        
    except ImportError as e:
        print(f"❌ 导入图例组件失败: {e}")
        print("请确保已正确创建颜色图例组件文件")
        return 1
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return 1

def test_defect_categories_config():
    """测试缺陷分类配置文件加载"""
    try:
        import json
        config_path = project_root / "config" / "defect_categories.json"
        
        if not config_path.exists():
            print(f"❌ 配置文件不存在: {config_path}")
            return False
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            
        categories = config_data.get("categories", [])
        print(f"✅ 加载了 {len(categories)} 个缺陷分类：")
        
        for i, category in enumerate(categories, 1):
            name = category.get("display_name", "未知")
            color = category.get("color", "#000000")
            enabled = category.get("enabled", True)
            status = "启用" if enabled else "禁用"
            print(f"   {i}. {name}: {color} ({status})")
            
        return True
        
    except Exception as e:
        print(f"❌ 测试配置文件失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("颜色图例显示效果测试")
    print("=" * 60)
    
    # 测试配置文件
    print("\n1. 测试缺陷分类配置文件...")
    config_ok = test_defect_categories_config()
    
    if not config_ok:
        print("❌ 配置文件测试失败，可能影响图例显示")
        return 1
    
    # 测试图例组件
    print("\n2. 测试颜色图例组件...")
    try:
        result = test_color_legend_widgets()
        if result == 0:
            print("✅ 颜色图例测试完成")
        else:
            print("❌ 颜色图例测试失败")
        return result
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
        return 0
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    sys.exit(main())