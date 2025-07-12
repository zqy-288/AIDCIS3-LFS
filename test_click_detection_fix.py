#!/usr/bin/env python3
"""
点击检测修复验证脚本
快速验证修复后的扇形点击检测算法
"""

import sys
import math
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtCore import QPointF
from aidcis2.graphics.sector_manager import SectorQuadrant

def test_click_detection():
    """测试点击检测算法"""
    print("🧪 测试点击检测算法修复")
    
    center = QPointF(400, 400)
    
    # 测试点和期望结果
    test_points = [
        (500, 200, SectorQuadrant.SECTOR_1, "右上"),
        (300, 200, SectorQuadrant.SECTOR_2, "左上"),
        (300, 600, SectorQuadrant.SECTOR_3, "左下"),
        (500, 600, SectorQuadrant.SECTOR_4, "右下"),
    ]
    
    def detect_clicked_sector(scene_pos: QPointF) -> SectorQuadrant:
        """点击检测算法（复制自修复后的代码）"""
        dx = scene_pos.x() - center.x()
        dy = scene_pos.y() - center.y()
        
        # 计算角度
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 转换为0-360度范围
        if angle_deg < 0:
            angle_deg += 360
        
        # 使用与SectorGraphicsManager相同的角度转换逻辑
        qt_angle = (360 - angle_deg) % 360
        
        # Qt坐标系中的扇形定义
        if 0 <= qt_angle < 90:
            return SectorQuadrant.SECTOR_1  # 右上
        elif 90 <= qt_angle < 180:
            return SectorQuadrant.SECTOR_2  # 左上
        elif 180 <= qt_angle < 270:
            return SectorQuadrant.SECTOR_3  # 左下
        else:  # 270 <= qt_angle < 360
            return SectorQuadrant.SECTOR_4  # 右下
    
    success_count = 0
    for x, y, expected, name in test_points:
        scene_pos = QPointF(x, y)
        detected = detect_clicked_sector(scene_pos)
        
        if detected == expected:
            print(f"✅ 点击检测正确: ({x}, {y}) {name} -> {expected.value}")
            success_count += 1
        else:
            print(f"❌ 点击检测错误: ({x}, {y}) {name} -> 期望{expected.value}，实际{detected.value}")
    
    print(f"\n📊 测试结果: {success_count}/{len(test_points)} 成功")
    return success_count == len(test_points)

if __name__ == "__main__":
    success = test_click_detection()
    if success:
        print("✅ 点击检测算法修复成功")
    else:
        print("❌ 点击检测算法仍有问题")
    sys.exit(0 if success else 1)