#!/usr/bin/env python3
"""
分析东重管板的实际孔位分布
确定正确的扇形划分方式
"""

import sys
import math
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core_business.dxf_parser import DXFParser
from src.core_business.hole_numbering_service import HoleNumberingService

def analyze_hole_distribution():
    """分析孔位分布"""
    print("=== 分析东重管板孔位分布 ===")
    
    dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
    
    # 解析DXF
    parser = DXFParser()
    hole_collection = parser.parse_file(dxf_path)
    
    if not hole_collection:
        print("❌ DXF解析失败")
        return
        
    print(f"✅ 解析成功: {len(hole_collection.holes)} 个孔位")
    
    # 获取所有孔位坐标
    x_coords = []
    y_coords = []
    for hole in hole_collection.holes.values():
        x_coords.append(hole.center_x)
        y_coords.append(hole.center_y)
    
    x_coords = np.array(x_coords)
    y_coords = np.array(y_coords)
    
    # 计算中心和边界
    center_x = np.mean(x_coords)
    center_y = np.mean(y_coords)
    
    print(f"\n几何中心: ({center_x:.2f}, {center_y:.2f})")
    print(f"X范围: [{np.min(x_coords):.2f}, {np.max(x_coords):.2f}]")
    print(f"Y范围: [{np.min(y_coords):.2f}, {np.max(y_coords):.2f}]")
    
    # 转换为极坐标
    dx = x_coords - center_x
    dy = y_coords - center_y
    distances = np.sqrt(dx**2 + dy**2)
    angles = np.arctan2(dy, dx) * 180 / np.pi
    angles[angles < 0] += 360  # 转换到0-360度
    
    # 创建图表
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. 散点图
    ax1 = axes[0, 0]
    ax1.scatter(x_coords, y_coords, s=1, alpha=0.5)
    ax1.axhline(y=center_y, color='r', linestyle='--', alpha=0.5)
    ax1.axvline(x=center_x, color='r', linestyle='--', alpha=0.5)
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_title('孔位分布')
    ax1.set_aspect('equal')
    
    # 2. 极坐标分布
    ax2 = axes[0, 1]
    ax2.scatter(angles, distances, s=1, alpha=0.5)
    ax2.set_xlabel('角度 (度)')
    ax2.set_ylabel('距离')
    ax2.set_title('极坐标分布')
    ax2.grid(True)
    
    # 3. 角度直方图
    ax3 = axes[1, 0]
    n_bins = 72  # 每5度一个bin
    counts, bins, _ = ax3.hist(angles, bins=n_bins, alpha=0.7)
    ax3.set_xlabel('角度 (度)')
    ax3.set_ylabel('孔位数量')
    ax3.set_title('角度分布直方图')
    ax3.grid(True, alpha=0.3)
    
    # 找出最小值的位置（间隙）
    min_indices = []
    for i in range(1, len(counts)-1):
        if counts[i] < counts[i-1] and counts[i] < counts[i+1]:
            min_indices.append(i)
    
    print("\n角度分布分析:")
    print(f"总bin数: {len(counts)}")
    print(f"平均每bin: {np.mean(counts):.1f} 个孔")
    print(f"发现的低密度区域 (可能的分界): ")
    for idx in min_indices:
        angle = (bins[idx] + bins[idx+1]) / 2
        count = counts[idx]
        print(f"  {angle:.1f}° (孔数: {int(count)})")
    
    # 4. 四象限分析
    ax4 = axes[1, 1]
    quadrants = {
        'Q1 (0-90°)': np.sum((angles >= 0) & (angles < 90)),
        'Q2 (90-180°)': np.sum((angles >= 90) & (angles < 180)),
        'Q3 (180-270°)': np.sum((angles >= 180) & (angles < 270)),
        'Q4 (270-360°)': np.sum((angles >= 270) & (angles < 360))
    }
    
    bars = ax4.bar(quadrants.keys(), quadrants.values())
    ax4.set_ylabel('孔位数量')
    ax4.set_title('四象限孔位分布')
    for bar, count in zip(bars, quadrants.values()):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50, 
                str(count), ha='center', va='bottom')
    
    # 分析基于密度的分区
    print("\n基于密度的分区建议:")
    
    # 寻找90度间隔附近的最低点
    target_angles = [0, 90, 180, 270]
    window = 10  # ±10度窗口
    
    boundaries = []
    for target in target_angles:
        # 在目标角度附近寻找最低点
        mask = np.abs(bins[:-1] - target) < window
        if np.any(mask):
            local_counts = counts[mask]
            local_bins = bins[:-1][mask]
            min_idx = np.argmin(local_counts)
            boundary_angle = local_bins[min_idx]
            boundaries.append(boundary_angle)
            print(f"  在{target}°附近找到边界: {boundary_angle:.1f}°")
    
    # 在直方图上标记边界
    for boundary in boundaries:
        ax3.axvline(x=boundary, color='r', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('hole_distribution_analysis.png', dpi=150)
    plt.show()
    
    return hole_collection, center_x, center_y, boundaries

if __name__ == "__main__":
    analyze_hole_distribution()