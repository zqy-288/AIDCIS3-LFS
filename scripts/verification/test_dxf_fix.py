#!/usr/bin/env python3
"""
测试DXF解析器修复
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core_business.dxf_parser import DXFParser
from src.core_business.hole_numbering_service import HoleNumberingService

def test_dxf_parser_fix():
    """测试DXF解析器的修复"""
    print("测试 DXF 解析器修复...")
    
    # 检查HoleNumberingService构造函数
    try:
        service = HoleNumberingService()
        print("✅ HoleNumberingService 创建成功（无参数）")
    except Exception as e:
        print(f"❌ HoleNumberingService 创建失败: {e}")
        
    # 检查DXF解析器代码
    parser_file = "src/core_business/dxf_parser.py"
    with open(parser_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "HoleNumberingService()" in content and "HoleNumberingService(logger=" not in content:
        print("✅ DXF解析器已正确调用HoleNumberingService（无logger参数）")
    else:
        print("❌ DXF解析器调用HoleNumberingService有误")
        
    print("\n修复完成！")

if __name__ == "__main__":
    test_dxf_parser_fix()