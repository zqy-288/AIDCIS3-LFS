#!/usr/bin/env python3
"""
验证关键修复的测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core_business.dxf_parser import DXFParser
from src.core_business.graphics.graphics_view import GraphicsView
from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer
from PySide6.QtWidgets import QApplication
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_dxf_parser():
    """测试DXF解析器的修复"""
    print("\n=== 测试DXF解析器 ===")
    
    parser = DXFParser()
    
    # 使用CAP1000的DXF文件
    dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/data/CAP1000.dxf"
    
    if not os.path.exists(dxf_path):
        print(f"❌ DXF文件不存在: {dxf_path}")
        return False
        
    try:
        # 解析DXF文件
        hole_collection = parser.parse_dxf_file(dxf_path)
        
        if hole_collection is None:
            print("❌ 解析返回None")
            return False
            
        print(f"✅ 成功解析 {len(hole_collection.holes)} 个孔位")
        
        # 检查是否生成了标准格式的ID
        sample_ids = list(hole_collection.holes.keys())[:5]
        print(f"   示例ID: {sample_ids}")
        
        # 验证ID格式
        for hole_id in sample_ids:
            if not (hole_id.startswith('AC') or hole_id.startswith('BC')):
                print(f"❌ ID格式不正确: {hole_id}")
                return False
                
        print("✅ 所有ID格式正确")
        return True
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_micro_view_scale():
    """测试微观视图缩放"""
    print("\n=== 测试微观视图缩放 ===")
    
    app = QApplication.instance() or QApplication([])
    
    try:
        view = GraphicsView()
        
        # 测试set_micro_view_scale方法
        view.set_micro_view_scale()
        
        # 获取当前缩放值
        current_scale = view.transform().m11()
        print(f"当前缩放值: {current_scale}")
        
        # 验证缩放范围
        if 0.5 <= current_scale <= 2.0:
            print("✅ 缩放值在正确范围内 (0.5-2.0)")
            return True
        else:
            print(f"❌ 缩放值超出范围: {current_scale}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_r164_priority():
    """测试R164行的优先级处理"""
    print("\n=== 测试R164行优先级 ===")
    
    renderer = SnakePathRenderer()
    
    # 创建模拟的孔位数据
    from src.core_business.models.hole_data import HoleData, HoleCollection
    
    holes_dict = {}
    
    # 创建R164行的孔位
    for col in [94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104]:
        hole_id = f"BC{col:03d}R164"
        hole = HoleData(
            hole_id=hole_id,
            center_x=col * 10.0,
            center_y=-1640.0,  # R164的Y坐标
            diameter=10.0
        )
        holes_dict[hole_id] = hole
    
    # 创建其他行的孔位
    for row in [163, 162]:
        for col in [98, 99, 100, 101, 102]:
            hole_id = f"BC{col:03d}R{row:03d}"
            hole = HoleData(
                hole_id=hole_id,
                center_x=col * 10.0,
                center_y=-row * 10.0,
                diameter=10.0
            )
            holes_dict[hole_id] = hole
    
    hole_collection = HoleCollection(holes=holes_dict)
    renderer.set_hole_collection(hole_collection)
    
    # 生成间隔4列路径
    from src.pages.shared.components.snake_path.snake_path_renderer import PathStrategy
    detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    
    if not detection_units:
        print("❌ 没有生成检测单元")
        return False
        
    print(f"✅ 生成了 {len(detection_units)} 个检测单元")
    
    # 检查第一个检测单元
    if detection_units:
        first_unit = detection_units[0]
        if hasattr(first_unit, 'holes') and len(first_unit.holes) == 2:
            hole_ids = [h.hole_id for h in first_unit.holes]
            print(f"   第一个检测单元: {hole_ids}")
            
            # 验证是否是BC098R164+BC102R164
            if 'BC098R164' in hole_ids and 'BC102R164' in hole_ids:
                print("✅ BC098R164+BC102R164 正确作为第一个配对")
                return True
            else:
                print(f"❌ 第一个配对不是预期的: {hole_ids}")
                return False
    
    return False

def main():
    """主测试函数"""
    print("开始验证关键修复...")
    
    results = []
    
    # 测试1: DXF解析器
    results.append(("DXF解析器", test_dxf_parser()))
    
    # 测试2: 微观视图缩放
    results.append(("微观视图缩放", test_micro_view_scale()))
    
    # 测试3: R164优先级
    results.append(("R164优先级", test_r164_priority()))
    
    # 输出总结
    print("\n=== 测试总结 ===")
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试通过!")
    else:
        print("\n⚠️ 部分测试失败，请检查相关修复")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)