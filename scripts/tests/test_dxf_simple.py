#!/usr/bin/env python3
"""
简单的DXF解析测试
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_dxf_parsing():
    """测试DXF解析"""
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        from aidcis2.dxf_parser import DXFParser
        logger.info("✅ DXFParser导入成功")
    except Exception as e:
        logger.error(f"❌ DXFParser导入失败: {e}")
        return False
    
    # 创建解析器
    parser = DXFParser()
    logger.info("✅ DXFParser创建成功")
    
    # 测试文件
    test_file = "测试管板.dxf"
    
    if not Path(test_file).exists():
        logger.error(f"❌ 测试文件不存在: {test_file}")
        return False
    
    logger.info(f"✅ 测试文件存在: {test_file}")
    
    try:
        # 解析文件
        logger.info("开始解析DXF文件...")
        hole_collection = parser.parse_file(test_file)
        
        if hole_collection is None:
            logger.error("❌ 解析返回None")
            return False
            
        logger.info(f"✅ 解析完成，孔位数量: {len(hole_collection)}")
        
        if len(hole_collection) > 0:
            # 显示第一个孔位信息
            first_hole = hole_collection[0]
            logger.info(f"第一个孔位: ID={first_hole.hole_id}, 位置=({first_hole.center_x}, {first_hole.center_y}), 半径={first_hole.radius}")
            
            # 显示边界
            bounds = hole_collection.get_bounds()
            logger.info(f"边界: {bounds}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dxf_parsing()
    print(f"\n测试结果: {'成功' if success else '失败'}")
