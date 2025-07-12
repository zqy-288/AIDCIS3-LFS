#!/usr/bin/env python3
"""测试DXF转换器"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modules.dxf_to_product_converter import DXFToProductConverter

# 创建转换器
converter = DXFToProductConverter()

# 测试文件路径
dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"

print(f"测试DXF文件: {dxf_path}")
print(f"文件是否存在: {Path(dxf_path).exists()}")

# 测试DXF解析器
from aidcis2.dxf_parser import DXFParser
parser = DXFParser()
print("\n测试DXF解析器...")
try:
    holes = parser.parse_file(dxf_path)
    if holes:
        print(f"解析成功，找到 {len(holes.holes)} 个孔位")
    else:
        print("解析失败")
except Exception as e:
    print(f"解析错误: {e}")
    import traceback
    traceback.print_exc()

# 转换
print("\n测试转换器...")
try:
    result = converter.convert_dxf_to_product_info(dxf_path)
    if result:
        print("\n转换成功！")
        print(f"产品名称: {result['product_name']}")
        print(f"产品编号: {result['product_code']}")
        print(f"孔位数量: {result['hole_count']}")
        print(f"孔径: {result['hole_diameter']}")
        print(f"形状: {result['shape']}")
        print(f"完整性评分: {converter.validate_product_info(result)['completeness_score']}%")
    else:
        print("转换返回None")
except Exception as e:
    print(f"转换错误: {e}")
    import traceback
    traceback.print_exc()