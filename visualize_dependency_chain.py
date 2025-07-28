#!/usr/bin/env python3
"""
可视化项目的13层依赖链
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_dependency_visualization():
    """创建依赖链可视化图"""
    
    # 创建图形
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 16))
    
    # 左侧：主要依赖链
    ax1.set_title("主要13层依赖链", fontsize=16, fontweight='bold', pad=20)
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 14)
    ax1.axis('off')
    
    # 定义层级
    layers = [
        ("Layer 1", "main.py", "#FF6B6B"),
        ("Layer 2", "main_window.py", "#4ECDC4"),
        ("Layer 3", "graphics_view.py", "#45B7D1"),
        ("Layer 4", "hole_item.py", "#96CEB4"),
        ("Layer 5", "hole_data.py", "#FECA57"),
        ("Layer 6", "shared_data_manager.py", "#FF9FF3"),
        ("Layer 7", "unified_sector_adapter.py", "#54A0FF"),
        ("Layer 8", "coordinate_system.py", "#48DBFB"),
        ("Layer 9", "unified_id_manager.py", "#C8E6C9"),
        ("Layer 10", "data_adapter.py", "#FFCCBC"),
        ("Layer 11", "data_access_layer.py", "#B2DFDB"),
        ("Layer 12", "config_manager.py", "#D1C4E9"),
        ("Layer 13", "dependency_injection.py", "#F8BBD0")
    ]
    
    # 绘制层级
    for i, (layer_name, file_name, color) in enumerate(layers):
        y = 13 - i
        
        # 绘制层级框
        box = FancyBboxPatch((1, y - 0.4), 8, 0.8, 
                             boxstyle="round,pad=0.1",
                             facecolor=color,
                             edgecolor='black',
                             linewidth=2)
        ax1.add_patch(box)
        
        # 添加文字
        ax1.text(5, y, f"{layer_name}: {file_name}", 
                ha='center', va='center', 
                fontsize=11, fontweight='bold')
        
        # 绘制箭头
        if i < len(layers) - 1:
            arrow = patches.FancyArrowPatch((5, y - 0.4), (5, y - 0.6),
                                          connectionstyle="arc3",
                                          arrowstyle='-|>',
                                          mutation_scale=20,
                                          linewidth=2,
                                          color='darkred')
            ax1.add_patch(arrow)
    
    # 右侧：问题分析
    ax2.set_title("依赖链问题分析", fontsize=16, fontweight='bold', pad=20)
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 14)
    ax2.axis('off')
    
    # 问题区域
    problems = [
        {
            "title": "循环依赖风险",
            "items": [
                "SharedDataManager ↔ UnifiedSectorAdapter",
                "CoordinateSystem ↔ UnifiedIDManager",
                "HoleData 被多层重复引用"
            ],
            "color": "#FF6B6B",
            "y": 11
        },
        {
            "title": "违反依赖倒置原则",
            "items": [
                "graphics_view → HoleGraphicsItem (具体类)",
                "main_window 直接创建实例",
                "data_adapter → DataAccessLayer (具体类)"
            ],
            "color": "#FFA726",
            "y": 8
        },
        {
            "title": "职责混乱",
            "items": [
                "data_adapter: 数据+缓存+错误处理",
                "coordinate_system: 坐标+ID+编号",
                "SharedDataManager: 全局状态管理"
            ],
            "color": "#66BB6A",
            "y": 5
        },
        {
            "title": "传递依赖过多",
            "items": [
                "main → ... → dependency_injection (13层)",
                "错误处理链路过长",
                "业务逻辑与基础设施耦合"
            ],
            "color": "#42A5F5",
            "y": 2
        }
    ]
    
    for problem in problems:
        # 绘制问题框
        box = FancyBboxPatch((0.5, problem["y"] - 0.5), 9, 2.5,
                           boxstyle="round,pad=0.1",
                           facecolor=problem["color"],
                           alpha=0.3,
                           edgecolor=problem["color"],
                           linewidth=2)
        ax2.add_patch(box)
        
        # 标题
        ax2.text(5, problem["y"] + 1.5, problem["title"],
                ha='center', va='center',
                fontsize=12, fontweight='bold')
        
        # 问题项
        for j, item in enumerate(problem["items"]):
            ax2.text(5, problem["y"] + 0.8 - j*0.4, f"• {item}",
                    ha='center', va='center',
                    fontsize=10)
    
    # 添加总体说明
    fig.text(0.5, 0.02, 
             "13层依赖链严重影响了系统的可维护性、可测试性和可扩展性",
             ha='center', fontsize=14, fontweight='bold', color='red')
    
    plt.tight_layout()
    plt.savefig('dependency_chain_visualization.png', dpi=300, bbox_inches='tight')
    plt.savefig('dependency_chain_visualization.pdf', bbox_inches='tight')
    print("依赖链可视化图已生成: dependency_chain_visualization.png/pdf")

def create_ideal_structure():
    """创建理想的依赖结构图"""
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    ax.set_title("优化后的理想依赖结构", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # 理想层级
    ideal_layers = [
        ("应用入口", "main.py + DI配置", "#FF6B6B"),
        ("依赖注入容器", "DI Container", "#4ECDC4"),
        ("应用服务层", "Controllers + UI", "#45B7D1"),
        ("领域接口层", "Domain Interfaces", "#96CEB4"),
        ("领域服务层", "Business Services", "#FECA57"),
        ("基础设施层", "DAL + Cache + Config", "#FF9FF3"),
        ("外部依赖", "Qt + Database + Libraries", "#54A0FF")
    ]
    
    for i, (layer_name, description, color) in enumerate(ideal_layers):
        y = 7 - i
        
        # 绘制层级框
        box = FancyBboxPatch((1, y - 0.4), 8, 0.8,
                           boxstyle="round,pad=0.1",
                           facecolor=color,
                           alpha=0.6,
                           edgecolor='black',
                           linewidth=2)
        ax.add_patch(box)
        
        # 添加文字
        ax.text(5, y, f"{layer_name}: {description}",
                ha='center', va='center',
                fontsize=12, fontweight='bold')
        
        # 绘制箭头
        if i < len(ideal_layers) - 1:
            arrow = patches.FancyArrowPatch((5, y - 0.4), (5, y - 0.6),
                                          connectionstyle="arc3",
                                          arrowstyle='-|>',
                                          mutation_scale=20,
                                          linewidth=2,
                                          color='darkgreen')
            ax.add_patch(arrow)
    
    # 添加优化说明
    benefits_text = """
    优化收益：
    • 依赖层级从13层减少到7层
    • 消除循环依赖
    • 实现依赖倒置原则
    • 职责单一，易于测试
    • 提高可维护性和可扩展性
    """
    
    ax.text(5, -0.5, benefits_text,
            ha='center', va='top',
            fontsize=11,
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgreen', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('ideal_dependency_structure.png', dpi=300, bbox_inches='tight')
    plt.savefig('ideal_dependency_structure.pdf', bbox_inches='tight')
    print("理想依赖结构图已生成: ideal_dependency_structure.png/pdf")

if __name__ == "__main__":
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 生成可视化
    create_dependency_visualization()
    create_ideal_structure()
    
    print("\n依赖链分析可视化完成！")
    print("生成的文件：")
    print("- dependency_chain_visualization.png/pdf: 13层依赖链及问题分析")
    print("- ideal_dependency_structure.png/pdf: 优化后的理想结构")