#!/usr/bin/env python3
"""
调试DXF解析问题（无GUI版本）
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from aidcis2.dxf_parser import DXFParser

def main():
    # 设置详细日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # 创建DXF解析器
    dxf_parser = DXFParser()
    
    # 测试文件列表
    test_files = [
        "测试管板.dxf",
        "DXF Graph/东重管板.dxf"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            logger.info(f"=" * 50)
            logger.info(f"测试文件: {test_file}")
            logger.info(f"文件大小: {Path(test_file).stat().st_size} 字节")
            
            try:
                # 解析DXF文件
                hole_collection = dxf_parser.parse_file(test_file)
                
                if hole_collection and len(hole_collection) > 0:
                    logger.info(f"✅ 成功解析 {len(hole_collection)} 个孔位")
                    
                    # 显示孔位详细信息
                    logger.info("孔位详细信息:")
                    for i, hole in enumerate(hole_collection):
                        if i < 10:  # 只显示前10个
                            logger.info(f"  孔位 {i+1}: ID={hole.hole_id}, 位置=({hole.center_x:.3f}, {hole.center_y:.3f}), 半径={hole.radius:.3f}, 状态={hole.status}")
                        elif i == 10:
                            logger.info(f"  ... 还有 {len(hole_collection) - 10} 个孔位")
                            break
                    
                    # 显示边界信息
                    bounds = hole_collection.get_bounds()
                    logger.info(f"边界: X=[{bounds[0]:.3f}, {bounds[2]:.3f}], Y=[{bounds[1]:.3f}, {bounds[3]:.3f}]")
                    
                    return True
                    
                else:
                    logger.warning(f"❌ 文件 {test_file} 中未找到孔位")
                    
            except Exception as e:
                logger.error(f"❌ 解析 {test_file} 失败: {str(e)}", exc_info=True)
        else:
            logger.info(f"⚠️  文件不存在: {test_file}")
    
    logger.error("❌ 未找到可用的测试DXF文件或解析失败")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
