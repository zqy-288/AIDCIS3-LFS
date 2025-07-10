"""
创建测试用DXF文件
用于验证AIDCIS2的DXF导入功能
"""

import ezdxf
import os


def create_sample_dxf():
    """创建包含管孔的测试DXF文件"""
    # 创建新的DXF文档
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # 管孔参数
    hole_radius = 8.865  # 标准管孔半径
    
    # 创建一个3x3的管孔阵列
    positions = [
        (100, 100), (200, 100), (300, 100),
        (100, 200), (200, 200), (300, 200),
        (100, 300), (200, 300), (300, 300)
    ]
    
    print(f"创建测试DXF文件，包含 {len(positions)} 个管孔")
    
    for i, (x, y) in enumerate(positions):
        # 为每个孔位创建两个半圆弧组成完整的圆
        
        # 第一个半圆弧 (0-180度)
        msp.add_arc(
            center=(x, y),
            radius=hole_radius,
            start_angle=0,
            end_angle=180,
            dxfattribs={'layer': '0'}
        )
        
        # 第二个半圆弧 (180-360度)
        msp.add_arc(
            center=(x, y),
            radius=hole_radius,
            start_angle=180,
            end_angle=360,
            dxfattribs={'layer': '0'}
        )
        
        print(f"  孔位 {i+1}: 中心({x}, {y}), 半径{hole_radius}mm")
    
    # 添加一个边界大圆（应该被过滤掉）
    msp.add_arc(
        center=(200, 200),
        radius=2300,
        start_angle=0,
        end_angle=360,
        dxfattribs={'layer': 'boundary'}
    )
    print("  添加边界圆（半径2300mm，应被过滤）")
    
    # 保存文件
    output_file = "测试管板.dxf"
    doc.saveas(output_file)
    
    # 检查文件
    file_size = os.path.getsize(output_file)
    print(f"\n✅ 测试DXF文件创建成功:")
    print(f"   文件名: {output_file}")
    print(f"   文件大小: {file_size} 字节")
    print(f"   管孔数量: {len(positions)}")
    print(f"   管孔半径: {hole_radius}mm")
    
    return output_file


if __name__ == "__main__":
    try:
        dxf_file = create_sample_dxf()
        print(f"\n🎉 可以使用 {dxf_file} 测试AIDCIS2的DXF导入功能")
    except Exception as e:
        print(f"❌ 创建测试DXF文件失败: {e}")
        import traceback
        traceback.print_exc()
